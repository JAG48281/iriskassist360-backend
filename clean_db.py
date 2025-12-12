from app.database import engine
from sqlalchemy import text

def clean_and_reset():
    with engine.begin() as conn:
        print("Truncating add_on_rates...")
        conn.execute(text("TRUNCATE TABLE add_on_rates RESTART IDENTITY CASCADE"))
    print("Done.")

if __name__ == "__main__":
    clean_and_reset()
