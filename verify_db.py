from app.database import SessionLocal
from sqlalchemy import text

def check():
    db = SessionLocal()
    try:
        count = db.execute(text("SELECT count(*) FROM add_on_rates")).scalar()
        print(f"DB Check - add_on_rates count: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
