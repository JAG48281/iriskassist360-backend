import csv
import os

def check_integrity():
    # 1. Load Master Codes
    master_codes = set()
    with open("data/add_on_master.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            master_codes.add(row["add_on_code"])
    print(f"Master Codes: {len(master_codes)}")

    # 2. Check Rates CSV
    rates_path = "data/add_on_rates.csv"
    if not os.path.exists(rates_path):
        print("Rates CSV missing")
        return

    mismatch = []
    total = 0
    with open(rates_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            code = row["add_on_code"]
            if code not in master_codes:
                mismatch.append(code)
    
    print(f"Rates Total Rows: {total}")
    print(f"Mismatch Count: {len(mismatch)}")
    if mismatch:
        print(f"Unique Mismatched Codes: {set(mismatch)}")

if __name__ == "__main__":
    check_integrity()
