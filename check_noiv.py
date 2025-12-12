from app.database import SessionLocal
from sqlalchemy import text

def check():
    with SessionLocal() as db:
        res = db.execute(text("SELECT id, add_on_code FROM add_on_master WHERE add_on_code='NOIV'")).fetchone()
        print(f"NOIV: {res}")

if __name__ == "__main__":
    check()
