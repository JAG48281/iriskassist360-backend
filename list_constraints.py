from sqlalchemy import text
from app.database import engine

def list_constraints():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid = 'add_on_rates'::regclass")).fetchall()
        for r in res:
            print(r[0])

if __name__ == "__main__":
    list_constraints()
