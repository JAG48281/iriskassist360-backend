import sys
import os
from sqlalchemy import create_engine, inspect

sys.path.append(os.getcwd())
from app.database import Base
from app.config import settings

def check_schema():
    print("Checking specific column rename...")
    # Use SQLite for local check
    engine = create_engine("sqlite:///./local.db") # Assuming local.db is used
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('occupancies')]
    
    if 'risk_description' in columns:
        print("PASS: Column 'risk_description' exists.")
    else:
        print("FAIL: Column 'risk_description' MISSING.")
        
    if 'occupancy_description' not in columns:
        print("PASS: Column 'occupancy_description' removed.")
    else:
        print("FAIL: Column 'occupancy_description' STILL EXISTS.")

if __name__ == "__main__":
    check_schema()
