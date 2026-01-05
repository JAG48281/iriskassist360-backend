
from sqlalchemy import create_engine, text
from app.database import engine

def check_rate():
    print(f"DB URL: {engine.url}")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM fire_iib_rates WHERE iib_code = '2003'")).fetchone()
        print(f"Result for 2003: {result}")
        
        # Check count
        count = conn.execute(text("SELECT count(*) FROM fire_iib_rates")).scalar()
        print(f"Total rows in fire_iib_rates: {count}")

if __name__ == "__main__":
    check_rate()
