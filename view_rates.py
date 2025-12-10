from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.rate import Rate
from tabulate import tabulate # You might need to pip install tabulate, or we just print simply

def view_rates():
    db = SessionLocal()
    rates = db.query(Rate).all()
    
    print(f"\n{'PRODUCT':<10} | {'OCCUPANCY (Key)':<20} | {'RATE (Per Mille)':<10}")
    print("-" * 50)
    
    for r in rates:
        print(f"{r.product:<10} | {r.key:<20} | {r.value:<10}")
    
    print("-" * 50)
    print(f"Total Rates Found: {len(rates)}")
    db.close()

if __name__ == "__main__":
    view_rates()
