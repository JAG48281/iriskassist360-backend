from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.rate import Rate
from app.models.master import LobMaster, ProductMaster

# Ensure tables exist
# Base.metadata.create_all(bind=engine) # Better to rely on Alembic

def seed_lobs(db: Session):
    lobs = [
        ("FIRE", "Fire Insurance", "Fire and Special Perils"),
        ("MOTOR", "Motor Insurance", "Private and Commercial Vehicles"),
        ("HEALTH", "Health Insurance", "Individual and Floater policies"),
        ("PA", "Personal Accident", "Individual and Group PA"),
        ("LIABILITY", "Liability Insurance", "CGL, D&O, WC"),
        ("ENGINEERING", "Engineering Insurance", "CAR, EAR, MBD"),
        ("MISC", "Miscellaneous", "Other insurance products"),
    ]
    
    for code, name, desc in lobs:
        lob = db.query(LobMaster).filter(LobMaster.lob_code == code).first()
        if not lob:
            lob = LobMaster(lob_code=code, lob_name=name, description=desc, active=True)
            db.add(lob)
            print(f"Added LOB: {code}")
        else:
            print(f"LOB exists: {code}")
    db.commit()

def seed_products(db: Session):
    # Fetch Fire LOB
    fire_lob = db.query(LobMaster).filter(LobMaster.lob_code == "FIRE").first()
    if not fire_lob:
        print("Error: FIRE LOB not found. Cannot seed products.")
        return

    # Fire Products
    fire_products = [
        ("SFSP", "Standard Fire and Special Perils", "Traditional Fire Policy"),
        ("IAR", "Industrial All Risk", "Comprehensive Industrial Cover"),
        ("BGRP", "Bharat Griha Raksha Policy", "Home Insurance"),
        ("BSUSP", "Bharat Sookshma Udyam Suraksha", "Micro Enterprise"),
        ("BLUSP", "Bharat Laghu Udyam Suraksha", "Small Enterprise"),
        ("VUSP", "Value Udyam", "Value Added Product"), # based on existing seed
        ("UBGR", "Bharat Griha Raksha (UIIC)", "UIIC Specific Home Insurance"), # Mentioned in request metadata context
    ]

    for code, name, desc in fire_products:
        prod = db.query(ProductMaster).filter(ProductMaster.product_code == code, ProductMaster.lob_id == fire_lob.id).first()
        if not prod:
            prod = ProductMaster(lob_id=fire_lob.id, product_code=code, product_name=name, description=desc, active=True)
            db.add(prod)
            print(f"Added Product: {code}")
        else:
            print(f"Product exists: {code}")

    # Placeholders for other LOBs can be added here as needed
    
    db.commit()

def seed_rates():
    db = SessionLocal()
    
    seed_lobs(db)
    seed_products(db)

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

    print("Checking existing rates (legacy)...")
    
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
    print(f"✅ Seeding completed. Added legacy rates: {count}")
    db.close()

if __name__ == "__main__":
    seed_rates()
