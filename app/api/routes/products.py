from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.api.dependencies import get_current_user
from app.models.product import ProductCreate, ProductUpdate, ProductInDB

import csv
import io
from fastapi import UploadFile, File
from app.models.product import ImportResult, ImportRowResult

router = APIRouter()
db = firestore.client()


@router.post("", response_model=ProductInDB, status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, current_user: dict = Depends(get_current_user)):
    products_ref = db.collection('products')
    query = products_ref.where(filter=FieldFilter("sku", "==", product_data.sku)).limit(1).stream()
    if len(list(query)) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{product_data.sku}' already exists."
        )

    new_product_ref = products_ref.document()
    product_to_save = ProductInDB(id=new_product_ref.id, version=1, **product_data.dict())

    new_product_ref.set(product_to_save.dict())

    # Return the created object directly
    return product_to_save


@router.get("", response_model=list[ProductInDB])
def list_products(current_user: dict = Depends(get_current_user)):
    products_ref = db.collection('products').stream()
    return [doc.to_dict() for doc in products_ref]


@router.get("/{product_id}", response_model=ProductInDB)
def get_product(product_id: str, current_user: dict = Depends(get_current_user)):
    product_doc = db.collection('products').document(product_id).get()
    if not product_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product_doc.to_dict()


@router.put("/{product_id}", response_model=ProductInDB)
def update_product(
        product_id: str,
        product_update: ProductUpdate,
        current_user: dict = Depends(get_current_user)
):
    product_ref = db.collection('products').document(product_id)

    user_role = current_user.get("role")
    if user_role == "staff" and product_update.unit_price is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members cannot change the unit price."
        )

    @firestore.transactional
    def transact_update(transaction, doc_ref, update_data):
        snapshot = doc_ref.get(transaction=transaction)
        if not snapshot.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        current_data = snapshot.to_dict()
        current_version = current_data.get('version')

        if current_version != update_data.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Stale data. Expected version {update_data.version}, but found {current_version}."
            )

        update_payload = update_data.dict(exclude_unset=True)
        del update_payload['version']
        update_payload['version'] = current_version + 1

        transaction.update(doc_ref, update_payload)

        current_data.update(update_payload)
        return current_data

    transaction = db.transaction()
    updated_product = transact_update(transaction, product_ref, product_update)
    return updated_product


# Note the addition of response_model=None
@router.delete("/{product_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    product_ref = db.collection('products').document(product_id)
    if not product_ref.get().exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product_ref.delete()
    return None





@router.post("/import/csv", response_model=ImportResult)
async def import_products_from_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Idempotently imports products from a CSV file.
    - Validates each row.
    - Upserts (creates or updates) products based on SKU.
    - Uses a batch write for efficiency.
    - Returns a detailed report of the operation.
    """
    # --- 1. Read and Validate CSV content ---
    content = await file.read()
    try:
        content_text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content_text))
        rows = list(reader)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file format. Must be UTF-8 encoded.")

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    # --- 2. Fetch Existing Products for Upsert Logic ---
    products_ref = db.collection('products')
    existing_products_docs = products_ref.stream()
    # Create a map of {sku: {id, version}} for quick lookups
    existing_sku_map = {doc.to_dict()['sku']: {'id': doc.id, 'version': doc.to_dict()['version']} for doc in existing_products_docs}

    # --- 3. Process Rows and Prepare Batch ---
    batch = db.batch()
    results = []
    successful_creates = 0
    successful_updates = 0

    for i, row in enumerate(rows):
        row_num = i + 2  # Account for header row

        sku = row.get("sku")
        if not sku:
            results.append(ImportRowResult(row_number=row_num, status="error", details="SKU is missing."))
            continue

        try:
            # Pydantic validation for the rest of the fields
            product_data = ProductCreate(**row)
        except Exception as e:
            results.append(ImportRowResult(row_number=row_num, status="error", details=str(e), sku=sku))
            continue

        # --- 4. Logic for Create vs. Update ---
        if sku in existing_sku_map:
            # UPDATE logic
            product_info = existing_sku_map[sku]
            doc_ref = products_ref.document(product_info['id'])
            update_payload = product_data.dict()
            update_payload['version'] = product_info['version'] + 1
            batch.update(doc_ref, update_payload)

            results.append(ImportRowResult(row_number=row_num, status="updated", sku=sku))
            successful_updates += 1
        else:
            # CREATE logic
            new_doc_ref = products_ref.document()
            product_to_save = ProductInDB(id=new_doc_ref.id, version=1, **product_data.dict())
            batch.set(new_doc_ref, product_to_save.dict())

            results.append(ImportRowResult(row_number=row_num, status="created", sku=sku))
            successful_creates += 1

    # --- 5. Commit Batch and Return Result ---
    if successful_creates > 0 or successful_updates > 0:
        batch.commit()

    error_results = [res for res in results if res.status == 'error']

    return ImportResult(
        processed_rows=len(rows),
        successful_creates=successful_creates,
        successful_updates=successful_updates,
        errors=error_results
    )