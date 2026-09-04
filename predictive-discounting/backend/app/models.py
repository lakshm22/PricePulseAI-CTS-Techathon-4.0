from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(100), unique=True, nullable=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    mrp = Column(Numeric(10, 2), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    manufacture_date = Column(Date)
    expiry_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    inventory = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    sales = relationship("SalesHistory", back_populates="product", cascade="all, delete-orphan")

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    store_id = Column(String(50), nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    product = relationship("Product", back_populates="inventory")

class SalesHistory(Base):
    __tablename__ = "sales_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    store_id = Column(String(50), nullable=False)
    sale_date = Column(Date, nullable=False)
    units_sold = Column(Integer, nullable=False)
    price_sold = Column(Numeric(10, 2), nullable=False)
    product = relationship("Product", back_populates="sales")

class DiscountRecommendation(Base):
    __tablename__ = "discount_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    store_id = Column(String(50), nullable=False)
    predicted_demand = Column(Numeric(10, 2))
    risk_score = Column(Numeric(5, 4))
    risk_level = Column(String(20))
    recommended_min_discount = Column(Numeric(5, 2))
    recommended_max_discount = Column(Numeric(5, 2))
    recommended_discount_pct = Column(Numeric(5, 2))
    recommended_price = Column(Numeric(10, 2))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String(100), nullable=True)

class DiscountEvent(Base):
    __tablename__ = "discount_events"
    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("discount_recommendations.id", ondelete="CASCADE"))
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=False)
    applied_price = Column(Numeric(10, 2), nullable=False)
    applied_at = Column(DateTime, server_default=func.now())
    units_sold_after = Column(Integer, default=0)
    revenue_recovered = Column(Numeric(12, 2), default=0)

class ExcelSyncLog(Base):
    __tablename__ = "excel_sync_logs"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    store_id = Column(String(50), nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    updated_price = Column(Numeric(10, 2), nullable=False)
    file_path = Column(String(500))
    synced_at = Column(DateTime, server_default=func.now())
    success = Column(Boolean, default=True)
