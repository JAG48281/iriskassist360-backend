from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.rate import Rate

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def seed_rates():
    db = SessionLocal()
    
    # Define standard rates for UIIC Fire Products
    # Format: (Product Code, Occupancy Name, Rate Per Mille)
    rates_data = [
        # Bharat Griha Raksha (BGRP)
        ("BGRP", "Residential", 0.15),
        ("BGRP", "Apartment", 0.15),
        ("BGRP", "Independent House", 0.15),
        
        # Bharat Sookshma Udyam (BSUSP)
        ("BSUSP", "Office", 0.20),
        ("BSUSP", "Shop", 0.25),
        ("BSUSP", "Industrial", 0.30),
        ("BSUSP", "Warehouse", 0.35),
        ("BSUSP", "Residential", 0.16),
        
        # Bharat Laghu Udyam (BLUSP)
        ("BLUSP", "Office", 0.20),
        ("BLUSP", "Shop", 0.25),
        ("BLUSP", "Industrial", 0.30),
        ("BLUSP", "Warehouse", 0.35),
        
        # Value Udyam (VUSP)
        ("VUSP", "Office", 0.20),
        ("VUSP", "Shop", 0.25),
        
        # Standard Fire (SFSP)
        ("SFSP", "Factory", 0.60),
        ("SFSP", "Plant", 0.75),
        ("SFSP", "Warehouse", 0.40),
        ("SFSP", "Office", 0.25),
        
        # Industrial All Risk (IAR)
        ("IAR", "Factory", 0.60),
        ("IAR", "Plant", 0.75),
    ]

    print("Checking existing rates...")
    
    count = 0
    for product, occupancy, rate_val in rates_data:
        # Check if rate already exists to avoid duplicates
        exists = db.query(Rate).filter(
            Rate.company == "UIIC",
            Rate.product == product,
            Rate.key == occupancy
        ).first()
        
        if not exists:
            new_rate = Rate(
                company="UIIC",
                lob="Fire",
                product=product,
                category="occupancy",
                key=occupancy,   # This matches 'occupancy' in your lookup logic
                value=rate_val   # This matches 'rate_per_mille'
            )
            db.add(new_rate)
            count += 1
            print(f"Added: {product} - {occupancy} @ {rate_val}")
    
    db.commit()
    print(f"✅ Successfully added {count} new rates to PostgreSQL!")
    db.close()

if __name__ == "__main__":
    seed_rates()
