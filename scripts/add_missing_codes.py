"""Add missing codes to add_on_master.csv"""
import time

# Wait a moment for any file locks to release
time.sleep(2)

# Read current content
with open('data/add_on_master.csv', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if codes already exist
if 'PASL' not in content:
    # Append the 4 missing codes
    with open('data/add_on_master.csv', 'a', encoding='utf-8', newline='') as f:
        f.write('PASL,Personal Accident (Self),,FALSE,TRUE,TRUE\r\n')
        f.write('PASP,Personal Accident (Spouse),,FALSE,TRUE,TRUE\r\n')
        f.write('VLIT,Valuable Items Cover,,FALSE,TRUE,TRUE\r\n')
        f.write('ALAC,Alternate Accommodation,,FALSE,TRUE,TRUE\r\n')
    print("Added 4 missing codes to add_on_master.csv")
else:
    print("Codes already exist in add_on_master.csv")

# Verify
with open('data/add_on_master.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    # Subtract 1 for header
    count = len([l for l in lines if l.strip() and not l.startswith('add_on_code')]) 
    print(f"Total add-on codes in CSV: {count}")
