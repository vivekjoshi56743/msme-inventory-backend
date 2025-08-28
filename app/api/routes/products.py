from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.api.dependencies import get_current_user
from app.models.product import ProductCreate, ProductUpdate, ProductInDB

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