from datetime import date, timedelta
import random
from .database import SessionLocal, Base, engine
from . import models

Base.metadata.create_all(bind=engine)
STORE_ID = "STORE-1"
SAMPLE_PRODUCTS = [
    ("DRY-1042","890100000001","Milk 500ml","Dairy",60,1),
    ("BKY-2201","890100000002","Bread loaf","Bakery",45,1),
    ("DRY-1188","890100000003","Paneer 200g","Dairy",90,2),
    ("PRD-3305","890100000004","Bananas 1kg","Produce",50,2),
    ("DRY-1067","890100000005","Curd 400g","Dairy",35,1),
    ("PRD-3312","890100000006","Tomatoes 1kg","Produce",40,3),
    ("GRN-4410","890100000007","Rice 5kg","Grocery",320,20),
    ("GRN-4455","890100000008","Cooking oil 1L","Grocery",180,30),
]
def run():
    db=SessionLocal()
    try:
        for sku, barcode, name, category, mrp, shelf in SAMPLE_PRODUCTS:
            p=db.query(models.Product).filter(models.Product.sku==sku).first()
            if not p:
                p=models.Product(sku=sku, barcode=barcode, name=name, category=category, mrp=mrp,
                    current_price=mrp, manufacture_date=date.today()-timedelta(days=2),
                    expiry_date=date.today()+timedelta(days=shelf))
                db.add(p); db.flush()
            inv=db.query(models.Inventory).filter(models.Inventory.product_id==p.id, models.Inventory.store_id==STORE_ID).first()
            if not inv:
                inv=models.Inventory(product_id=p.id, store_id=STORE_ID, stock_quantity=random.randint(15,60)); db.add(inv)
            if db.query(models.SalesHistory).filter(models.SalesHistory.product_id==p.id, models.SalesHistory.store_id==STORE_ID).count()==0:
                for i in range(7,0,-1):
                    db.add(models.SalesHistory(product_id=p.id, store_id=STORE_ID, sale_date=date.today()-timedelta(days=i),
                        units_sold=random.randint(2,20), price_sold=mrp))
        db.commit(); print("Seed complete.")
    finally: db.close()
if __name__=="__main__": run()
