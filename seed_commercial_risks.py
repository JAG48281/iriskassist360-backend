
import logging
from app.database import SessionLocal
from app.models.fire_models import Occupancy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_commercial_risks():
    db = SessionLocal()
    try:
        # Standard IIB-like codes for seeding
        # Group A (Residential) - ensuring they exist
        residential_risks = [
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
                "allow_addons": False
            }
        ]

        # Group B (Commercial/Industrial) - generic codes for demo/seeding
        commercial_risks = [
            {
                "iib_code": "2001",
                "section_aift": "IV",
                "occupancy_type": "Office/Shops",
                "risk_description": "Offices, Shops, Hotels, etc. (Non-Industrial)",
                "allow_addons": True
            },
            {
                "iib_code": "2002",
                "section_aift": "V",
                "occupancy_type": "Industrial",
                "risk_description": "Industrial Manufacturing / Factories",
                "allow_addons": True
            },
            {
                "iib_code": "2003",
                "section_aift": "IV",
                "occupancy_type": "Storage",
                "risk_description": "Warehouses, Godowns, Cold Storage",
                "allow_addons": True
            },
            {
                "iib_code": "2004",
                "section_aift": "IV",
                "occupancy_type": "Utilities",
                "risk_description": "Power Plants, Water Treatment, Utilities",
                "allow_addons": True
            },
            {
                "iib_code": "2005",
                "section_aift": "IV",
                "occupancy_type": "IT/ITES",
                "risk_description": "IT Parks, BPOs, Server Farms",
                "allow_addons": True
            },
            {
                "iib_code": "2006",
                "section_aift": "IV",
                "occupancy_type": "Healthcare",
                "risk_description": "Hospitals, Nursing Homes, Clinics",
                "allow_addons": True
            }
        ]

        all_risks = residential_risks + commercial_risks

        logger.info(f"Seeding {len(all_risks)} Risk Descriptions...")
        
        for risk in all_risks:
            try:
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
                
                db.commit() # Commit per row to isolate error
            except Exception as row_error:
                logger.error(f"Failed to process {risk['iib_code']}: {row_error}")
                db.rollback()
        
        logger.info("✅ Seeding Process Finished.")
        
    except Exception as e:
        logger.error(f"Global Seeding Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_commercial_risks()
