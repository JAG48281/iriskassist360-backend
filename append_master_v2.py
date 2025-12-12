import csv

# Read all
with open('data/add_on_master.csv', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if ALAC exists
if "ALAC" in content:
    print("Already exists.")
else:
    # Append
    new_rows = """
PASL,PA to Self,,FALSE,TRUE,TRUE
PASP,PA to Spouse,,FALSE,TRUE,TRUE
VLIT,Valuable Items,,FALSE,TRUE,TRUE
ALAC,Alternate Accommodation,,FALSE,TRUE,TRUE
"""
    if not content.endswith('\n'):
        content += '\n'
    content += new_rows.strip() + '\n'
    
    with open('data/add_on_master.csv', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Rewrote file with new rows.")
