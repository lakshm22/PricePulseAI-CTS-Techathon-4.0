from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class ProductCreate(BaseModel):
    sku: str
    barcode: Optional[str] = None
    name: str
    category: Optional[str] = None
    mrp: float = Field(gt=0)
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    stock_quantity: int = Field(default=0, ge=0)
    store_id: str = "STORE-1"

class ProductOut(BaseModel):
    id: int
    sku: str
    barcode: Optional[str]
    name: str
    category: Optional[str]
    mrp: float
    current_price: float
    manufacture_date: Optional[date]
    expiry_date: Optional[date]
    stock_quantity: int = 0
    class Config:
        from_attributes = True

class DiscountRecommendationOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    barcode: Optional[str]
    store_id: str
    mrp: float
    current_price: float
    predicted_demand: float
    risk_score: float
    risk_level: str
    recommended_min_discount: float
    recommended_max_discount: float
    recommended_discount_pct: float
    recommended_price: float
    status: str
    days_to_expiry: Optional[int]
    stock_quantity: int

class ApplyDiscountRequest(BaseModel):
    recommendation_id: int
    discount_percentage: float = Field(ge=10, le=20)
    decided_by: str = "manager"

class BillingScanRequest(BaseModel):
    barcode: str
    quantity: int = Field(default=1, ge=1)

class BillingResponse(BaseModel):
    product_id: int
    barcode: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    price_source: str
