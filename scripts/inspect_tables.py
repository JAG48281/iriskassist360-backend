from sqlalchemy import create_engine, inspect
import sys
import os

# Add parent dir to path if needed for app imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def list_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Current Tables in Database:")
    for table in tables:
        print(f"- {table}")

if __name__ == "__main__":
    list_tables()
