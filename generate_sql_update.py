"""
Direct SQL script to update fire_iib_rates on Railway production database.
This will be executed manually via Railway's database console.
"""

# Generate SQL statements from CSV
import csv
from pathlib import Path

csv_path = Path("data/fire_iib_rates.csv")

print("-- ============================================")
print("-- FIRE_IIB_RATES DATA REFRESH SQL SCRIPT")
print("-- Execute this in Railway Database Console")
print("-- ============================================")
print()
print("-- Step 1: Truncate existing data")
print("TRUNCATE TABLE fire_iib_rates RESTART IDENTITY CASCADE;")
print()
print("-- Step 2: Insert corrected data from CSV")
print()

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        iib_code = row.get('iib_code', '').strip()
        basic_rate = row.get('basic_rate', '').strip()
        
        if iib_code and basic_rate:
            print(f"INSERT INTO fire_iib_rates (iib_code, rate_per_mille) VALUES ('{iib_code}', {basic_rate});")

print()
print("-- Step 3: Verify")
print("SELECT COUNT(*) FROM fire_iib_rates;")
print("SELECT * FROM fire_iib_rates WHERE iib_code IN ('1001', '1002', '2001', '2003', '2005') ORDER BY iib_code;")
