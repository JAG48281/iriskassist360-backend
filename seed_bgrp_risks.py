
import logging
from app.database import SessionLocal
from app.models.fire_models import Occupancy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_bgrp_risks():
    db = SessionLocal()
    try:
        risks_data = [
            {
                "iib_code": "1001",
                "section_aift": "III",
                "occupancy_type": "Residential",
                "risk_description": "Dwellings used for residence purpose",
                "allow_addons": True
            },
            {
                "iib_code": "1001_2",
                "section_aift": "III",
                "occupancy_type": "Residential",
                "risk_description": "Dwelling Co-operative Housing Society",
                "allow_addons": False # Restricted as per previous logic
            }
        ]

        logger.info("Seeding BGRP Risk Descriptions (Occupancies)...")
        
        for risk in risks_data:
            existing = db.query(Occupancy).filter(Occupancy.iib_code == risk["iib_code"]).first()
            
            if existing:
                logger.info(f"Updating existing occupancy: {risk['iib_code']}")
                existing.section_aift = risk["section_aift"]
                existing.occupancy_type = risk["occupancy_type"]
                existing.risk_description = risk["risk_description"]
                existing.allow_addons = risk["allow_addons"]
            else:
                logger.info(f"Creating new occupancy: {risk['iib_code']}")
                new_occ = Occupancy(**risk)
                db.add(new_occ)
        
        db.commit()
        logger.info("✅ Seeding Complete.")
        
    except Exception as e:
        logger.error(f"Seeding Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_bgrp_risks()
