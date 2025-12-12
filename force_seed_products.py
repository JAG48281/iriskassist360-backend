from app.database import engine
from sqlalchemy import text

def force_seed():
    products = [
        ("SFSP", "Standard Fire and Special Perils"),
        ("IAR", "Industrial All Risk"),
        ("BGRP", "Bharat Griha Raksha Policy"),
        ("BSUSP", "Bharat Sookshma Udyam Suraksha"),
        ("BLUSP", "Bharat Laghu Udyam Suraksha"),
        ("VUSP", "Value Udyam"),
        ("UBGR", "Bharat Griha Raksha (UIIC)"),
        ("UVGS", "Udyam Value Griha Suraksha")
    ]
    
    with engine.begin() as conn:
        # Get FIRE Lob ID
        lob_id = conn.execute(text("SELECT id FROM lob_master WHERE lob_code='FIRE'")).scalar()
        if not lob_id:
            print("Creating FIRE LOB...")
            conn.execute(text("INSERT INTO lob_master (lob_code, lob_name, description, active) VALUES ('FIRE','Fire','Desc',true)"))
            lob_id = conn.execute(text("SELECT id FROM lob_master WHERE lob_code='FIRE'")).scalar()
            
        print(f"FIRE LOB ID: {lob_id}")
        
        for code, name in products:
            exists = conn.execute(text("SELECT id FROM product_master WHERE product_code=:c"), {"c": code}).scalar()
            if not exists:
                print(f"Inserting {code}...")
                conn.execute(text("""
                    INSERT INTO product_master (lob_id, product_code, product_name, description, active)
                    VALUES (:lid, :code, :name, 'Desc', true)
                """), {"lid": lob_id, "code": code, "name": name})
            else:
                print(f"Found {code} (ID: {exists})")

if __name__ == "__main__":
    force_seed()
