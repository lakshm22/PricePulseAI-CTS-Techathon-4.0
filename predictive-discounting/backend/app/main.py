from datetime import date, datetime
from typing import List
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, engine as discount_engine
from .database import Base, engine, get_db
from .excel_service import update_product_price

app = FastAPI(
    title="PricePulse API",
    description="Predict demand, identify unsold risk, optimize discounts, synchronize approved prices, and support barcode billing.",
    version="1.0.0",
)

origins = [o.strip() for o in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

STORE_ID = "STORE-1"

@app.get("/")
def root():
    return {"status": "ok", "service": "pricepulse-api"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.get("/api/products")
def list_products(store_id: str = STORE_ID, db: Session = Depends(get_db)):
    rows = db.query(models.Inventory).filter(models.Inventory.store_id == store_id).all()
    result = []
    for inv in rows:
        p = db.query(models.Product).filter(models.Product.id == inv.product_id).first()
        if p:
            result.append({
                "id": p.id, "sku": p.sku, "barcode": p.barcode, "name": p.name,
                "category": p.category, "mrp": float(p.mrp), "current_price": float(p.current_price),
                "manufacture_date": p.manufacture_date, "expiry_date": p.expiry_date,
                "stock_quantity": inv.stock_quantity
            })
    return result

@app.post("/api/products")
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    if db.query(models.Product).filter(models.Product.sku == payload.sku).first():
        raise HTTPException(409, "SKU already exists")
    p = models.Product(
        sku=payload.sku, barcode=payload.barcode, name=payload.name, category=payload.category,
        mrp=payload.mrp, current_price=payload.mrp,
        manufacture_date=payload.manufacture_date, expiry_date=payload.expiry_date
    )
    db.add(p); db.flush()
    db.add(models.Inventory(product_id=p.id, store_id=payload.store_id, stock_quantity=payload.stock_quantity))
    db.commit(); db.refresh(p)
    return {"id": p.id, "message": "Product created"}

def build_recommendations(store_id: str, db: Session):
    results = []
    inventories = db.query(models.Inventory).filter(models.Inventory.store_id == store_id).all()
    for inv in inventories:
        p = db.query(models.Product).filter(models.Product.id == inv.product_id).first()
        if not p:
            continue
        sales = (
            db.query(models.SalesHistory)
            .filter(models.SalesHistory.product_id == p.id, models.SalesHistory.store_id == store_id)
            .order_by(models.SalesHistory.sale_date.desc()).limit(7).all()
        )
        recent = [x.units_sold for x in reversed(sales)]
        days = discount_engine.days_to_expiry(p.expiry_date, date.today())
        demand = discount_engine.predict_demand(recent, max(days, 1))
        risk = discount_engine.compute_risk_score(inv.stock_quantity, demand, days)
        level = discount_engine.risk_level(risk)
        min_d, max_d = discount_engine.discount_range(risk, days)
        expired = bool(p.expiry_date and p.expiry_date <= date.today())
        suggested = 0 if expired else max_d if level == "HIGH" else min_d
        price = discount_engine.recommended_price(float(p.mrp), suggested, expired)
        rec = db.query(models.DiscountRecommendation).filter(
            models.DiscountRecommendation.product_id == p.id,
            models.DiscountRecommendation.store_id == store_id,
            models.DiscountRecommendation.status == "pending"
        ).order_by(models.DiscountRecommendation.created_at.desc()).first()
        if not rec:
            rec = models.DiscountRecommendation(
                product_id=p.id, store_id=store_id,
                predicted_demand=demand, risk_score=risk, risk_level=level,
                recommended_min_discount=min_d, recommended_max_discount=max_d,
                recommended_discount_pct=suggested, recommended_price=price, status="pending"
            )
            db.add(rec); db.flush()
        else:
            rec.predicted_demand=demand; rec.risk_score=risk; rec.risk_level=level
            rec.recommended_min_discount=min_d; rec.recommended_max_discount=max_d
            rec.recommended_discount_pct=suggested; rec.recommended_price=price
        results.append({
            "id": rec.id, "product_id": p.id, "product_name": p.name, "sku": p.sku, "barcode": p.barcode,
            "store_id": store_id, "mrp": float(p.mrp), "current_price": float(p.current_price),
            "predicted_demand": demand, "risk_score": risk, "risk_level": level,
            "recommended_min_discount": min_d, "recommended_max_discount": max_d,
            "recommended_discount_pct": suggested, "recommended_price": price,
            "status": "pending", "days_to_expiry": days, "stock_quantity": inv.stock_quantity
        })
    db.commit()
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)

@app.get("/api/recommendations")
def get_recommendations(store_id: str = STORE_ID, db: Session = Depends(get_db)):
    return build_recommendations(store_id, db)

@app.post("/api/apply-discount")
def apply_discount(payload: schemas.ApplyDiscountRequest, db: Session = Depends(get_db)):
    rec = db.query(models.DiscountRecommendation).filter(models.DiscountRecommendation.id == payload.recommendation_id).first()
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    p = db.query(models.Product).filter(models.Product.id == rec.product_id).first()
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == p.id, models.Inventory.store_id == rec.store_id).first()
    if not p or not inv:
        raise HTTPException(404, "Product or inventory not found")
    if p.expiry_date and p.expiry_date <= date.today():
        raise HTTPException(400, "Expired products cannot be discounted or sold")
    if not (rec.recommended_min_discount <= payload.discount_percentage <= rec.recommended_max_discount):
        raise HTTPException(400, f"Choose a discount between {rec.recommended_min_discount}% and {rec.recommended_max_discount}%")
    old_price = float(p.current_price)
    new_price = discount_engine.recommended_price(float(p.mrp), payload.discount_percentage)
    p.current_price = new_price
    rec.status = "applied"
    rec.recommended_discount_pct = payload.discount_percentage
    rec.recommended_price = new_price
    rec.decided_at = datetime.utcnow()
    rec.decided_by = payload.decided_by
    event = models.DiscountEvent(
        recommendation_id=rec.id, discount_percentage=payload.discount_percentage,
        original_price=old_price, applied_price=new_price
    )
    db.add(event)
    db.commit()
    try:
        excel = update_product_price(p, inv, payload.discount_percentage)
        db.add(models.ExcelSyncLog(
            product_id=p.id, store_id=rec.store_id, discount_percentage=payload.discount_percentage,
            updated_price=new_price, file_path=excel["file_path"], success=True
        ))
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Price updated in PostgreSQL but Excel synchronization failed: {exc}")
    return {
        "status": "applied", "product_id": p.id, "product_name": p.name,
        "discount_percentage": payload.discount_percentage,
        "old_price": old_price, "new_price": new_price,
        "excel_updated": True
    }

@app.post("/api/billing/scan", response_model=schemas.BillingResponse)
def billing_scan(payload: schemas.BillingScanRequest, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.barcode == payload.barcode).first()
    if not p:
        p = db.query(models.Product).filter(models.Product.sku == payload.barcode).first()
    if not p:
        raise HTTPException(404, "Product/barcode not found")
    if p.expiry_date and p.expiry_date <= date.today():
        raise HTTPException(400, "Product is expired and cannot be sold")
    unit_price = float(p.current_price)
    return schemas.BillingResponse(
        product_id=p.id, barcode=p.barcode or p.sku, product_name=p.name,
        quantity=payload.quantity, unit_price=unit_price,
        line_total=round(unit_price * payload.quantity, 2),
        price_source="approved PostgreSQL price"
    )

@app.get("/api/dashboard-summary")
def dashboard_summary(store_id: str = STORE_ID, db: Session = Depends(get_db)):
    recs = build_recommendations(store_id, db)
    at_risk = [r for r in recs if r["risk_score"] >= 0.35]
    applied = db.query(models.DiscountEvent).all()
    return {
        "products_at_risk": len(at_risk),
        "pending_recommendations": len(at_risk),
        "approved_discounts": len(applied),
        "active_products": len(recs)
    }
