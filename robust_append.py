import os

lines_to_add = [
    "PASL,PA to Self,,FALSE,TRUE,TRUE",
    "PASP,PA to Spouse,,FALSE,TRUE,TRUE",
    "VLIT,Valuable Items,,FALSE,TRUE,TRUE",
    "ALAC,Alternate Accommodation,,FALSE,TRUE,TRUE"
]

file_path = "data/add_on_master.csv"

# Read existing
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read().splitlines()

# Append if not present
for line in lines_to_add:
    code = line.split(",")[0]
    if not any(l.startswith(code + ",") for l in content):
        content.append(line)
        print(f"Adding {code}")
    else:
        print(f"Skipping {code}")

# Write back
try:
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(content) + "\n")
    print("Write success.")
except Exception as e:
    print(f"Write failed: {e}")
