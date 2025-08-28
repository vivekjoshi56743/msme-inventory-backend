from pydantic import BaseModel, Field
from typing import Optional

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sku: str = Field(..., min_length=1, max_length=64)
    category: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(..., ge=0) # Must be >= 0
    unit_price: float = Field(..., ge=0.0) # Must be >= 0.0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    # All fields are optional for updates
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    quantity: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0.0)
    version: int # Version is required for optimistic concurrency

class ProductInDB(ProductBase):
    id: str
    version: int = 1