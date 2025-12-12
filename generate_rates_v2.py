import csv
import os

OUTPUT_PATH = "data/add_on_rates.csv"
MAP_PATH = "data/add_on_product_map.csv"

# Alias Map
ALIAS_MAP = {"BLUS": "BLUSP", "BSUS": "BSUSP", "UVUS": "VUSP", "BGR": "BGRP"}

def get_product_map_codes(target_products):
    codes = set()
    with open(MAP_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = row["product_code"].strip()
            p = ALIAS_MAP.get(p, p)
            if p in target_products:
                codes.add(row["add_on_code"])
    return list(codes)

def generate():
    rows = []
    def add_row(prod, code, r_type, r_val, remarks=""):
        rows.append({
            "add_on_code": code,
            "product_code": prod,
            "rate_type": r_type,
            "rate_value": r_val,
            "min_si": "", "max_si": "", "max_payable": "",
            "remarks": remarks
        })

    # GROUP 1: SFSP, IAR
    G1_CODES = get_product_map_codes(["SFSP", "IAR"])
    rules_g1 = {
        "CMST": (5.0, "per_mille"),
        "LOOV": (7.0, "per_mille"),
        "MMCL": (0.65, "per_mille")
    }
    for prod in ["SFSP", "IAR"]:
        for code in G1_CODES:
            val, typ = rules_g1.get(code, (1.0, "policy_rate"))
            add_row(prod, code, typ, val)

    # GROUP 2: BLUSP, BSUSP, VUSP
    G2_CODES = get_product_map_codes(["BLUSP", "BSUSP", "VUSP"])
    # Adjusted for likely valid types
    rules_g2 = {
        "ACDM": (0.010, "per_mille"),
        "DBRM": (12.5, "per_mille"), # 1.25% -> 12.5 per mille
        "ESCL": (0.5, "policy_rate") # 50% -> 0.5 factor
    }
    for prod in ["BLUSP", "BSUSP", "VUSP"]:
        for code in G2_CODES:
            remarks = ""
            val, typ = rules_g2.get(code, (1.0, "policy_rate"))
            if code == "DBRM": remarks = "of composite rate"
            add_row(prod, code, typ, val, remarks)

    # GROUP 3: BGR, UVGS
    G3_CODES = get_product_map_codes(["BGRP", "UVGS"]) # PASL, PASP, VLIT, LREN, ALAC
    # Rate Rules: 
    # PASL, PASP -> 7 flat. Use "flat" (if invalid, try "fixed")
    # Others -> 0.15 per mille
    for prod in ["BGRP", "UVGS"]:
        for code in G3_CODES:
            if code in ["PASL", "PASP"]:
                val, typ = (7.0, "flat") 
            else:
                val, typ = (0.15, "per_mille")
            add_row(prod, code, typ, val)

    # Sort
    order = ["SFSP", "IAR", "BLUSP", "BSUSP", "VUSP", "BGRP", "UVGS"]
    rows.sort(key=lambda x: (order.index(x["product_code"]), x["add_on_code"]))
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["add_on_code", "product_code", "rate_type", "rate_value", "min_si", "max_si", "max_payable", "remarks"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} rows.")

if __name__ == "__main__":
    generate()
