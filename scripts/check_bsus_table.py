
from sqlalchemy import text, inspect
from app.database import engine

def check_table():
    inspector = inspect(engine)
    if "fire_bsus_rates" in inspector.get_table_names():
        print("Table 'fire_bsus_rates' exists.")
        columns = inspector.get_columns("fire_bsus_rates")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")
        
        print("\nSample Data:")
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM fire_bsus_rates LIMIT 5")).fetchall()
            for r in rows:
                print(r)
    else:
        print("Table 'fire_bsus_rates' DOES NOT exist.")

if __name__ == "__main__":
    check_table()
