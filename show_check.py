from sqlalchemy import text
from app.database import engine

def show_check():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ck_add_on_rates_rate_type'")).scalar()
        print(f"DEF: {res}")

if __name__ == "__main__":
    show_check()
