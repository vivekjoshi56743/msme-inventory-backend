from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from pydantic import BaseModel

from app.api.dependencies import get_current_user

router = APIRouter()
db = firestore.client()

class KpiData(BaseModel):
    total_items: int
    total_stock_value: float
    low_stock_count: int

@router.get("/kpis", response_model=KpiData)
def get_kpis(current_user: dict = Depends(get_current_user)):
    """
    Computes and returns dashboard KPIs in a single efficient query.
    """
    try:
        products_ref = db.collection('products')
        all_products = products_ref.stream()

        total_items = 0
        total_stock_value = 0.0
        low_stock_count = 0

        for product in all_products:
            prod_data = product.to_dict()
            quantity = prod_data.get('quantity', 0)
            unit_price = prod_data.get('unit_price', 0.0)

            total_items += 1
            total_stock_value += quantity * unit_price
            if quantity < 5:
                low_stock_count += 1

        return KpiData(
            total_items=total_items,
            total_stock_value=round(total_stock_value, 2),
            low_stock_count=low_stock_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
