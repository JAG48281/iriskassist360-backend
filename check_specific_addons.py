from app.database import SessionLocal
from sqlalchemy import text

def check_addons():
    with SessionLocal() as db:
        res = db.execute(text("SELECT add_on_code FROM add_on_master WHERE add_on_code IN ('PASL','PASP','VLIT','ALAC','ACDM')")).fetchall()
        print(f"Found: {len(res)}")
        print(res)

if __name__ == "__main__":
    check_addons()
