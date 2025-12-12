from sqlalchemy import text
from app.database import engine

def drop_constraint():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE add_on_rates DROP CONSTRAINT ck_add_on_rates_rate_type"))
            print("Dropped constraint.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    drop_constraint()
