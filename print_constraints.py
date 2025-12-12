from sqlalchemy import text
from app.database import engine

def check_constraints():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'add_on_rates'::regclass")).fetchall()
        for r in res:
            print(r)

if __name__ == "__main__":
    check_constraints()
