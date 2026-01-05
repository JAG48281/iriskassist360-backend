
from sqlalchemy import text, create_engine
from app.database import engine

def check_multiple_rates():
    codes = ['2001', '2003', '2005', '2010', '2101']
    print(f"Checking rates for: {codes}")
    
    with engine.connect() as conn:
        # Check specific codes
        for code in codes:
            row = conn.execute(text("SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :c"), {"c": code}).fetchone()
            print(f"Code {code}: {row[0] if row else 'Not Found'}")
            
        # Find code with 0.22
        row = conn.execute(text("SELECT iib_code FROM fire_iib_rates WHERE rate_per_mille = 0.22 LIMIT 1")).fetchone()
        print(f"Code with 0.22: {row[0]}")
        dist = conn.execute(text("SELECT rate_per_mille, count(*) as c FROM fire_iib_rates GROUP BY rate_per_mille ORDER BY c DESC LIMIT 5")).fetchall()
        for r in dist:
            print(f"Rate {r[0]}: {r[1]} records")

if __name__ == "__main__":
    check_multiple_rates()
