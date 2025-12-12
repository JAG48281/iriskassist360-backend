from sqlalchemy import text
from app.database import engine

def check_all_constraints():
    sql = "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'add_on_rates'::regclass"
    with engine.connect() as conn:
        res = conn.execute(text(sql)).fetchall()
        for r in res:
            print(f"Constraint: {r[0]}")
            print(f"Def: {r[1]}")
            print("-" * 20)

if __name__ == "__main__":
    check_all_constraints()
