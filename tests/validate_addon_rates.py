import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_validation():
    if not DATABASE_URL:
        print(json.dumps({"error": "DATABASE_URL not set"}))
        sys.exit(1)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    results = {}
    remediation = []
    
    # Rule 1: Count == 121
    cur.execute("SELECT COUNT(*) as cnt FROM add_on_rates WHERE active = true")
    count = cur.fetchone()['cnt']
    results['rule_1_count'] = {
        'pass': count == 121,
        'expected': 121,
        'actual': count,
        'message': f"Add-on rates count: {count}/121"
    }
    if count != 121:
        remediation.append(f"-- Missing {121 - count} add-on rates. Check CSV and reseed.")
    
    # Rule 2: Valid rate_types
    valid_types = ['FREE', 'POLICY_RATE', 'PER_MILLE', 'PERCENT_OF_BASIC_RATE', 'FLAT', 'MIN_PREMIUM']
    cur.execute("""
        SELECT id, add_on_id, product_code, rate_type 
        FROM add_on_rates 
        WHERE active = true 
        AND UPPER(rate_type) NOT IN ('FREE', 'POLICY_RATE', 'PER_MILLE', 'PERCENT_OF_BASIC_RATE', 'FLAT', 'MIN_PREMIUM')
        LIMIT 10
    """)
    invalid_types = cur.fetchall()
    results['rule_2_valid_types'] = {
        'pass': len(invalid_types) == 0,
        'failing_count': len(invalid_types),
        'failing_samples': [dict(r) for r in invalid_types],
        'message': f"Found {len(invalid_types)} rows with invalid rate_type"
    }
    if invalid_types:
        for row in invalid_types:
            remediation.append(f"UPDATE add_on_rates SET rate_type = 'POLICY_RATE' WHERE id = {row['id']}; -- Fix invalid type: {row['rate_type']}")
    
    # Rule 3: PER_MILLE validation
    cur.execute("""
        SELECT id, add_on_id, product_code, rate_type, rate_value 
        FROM add_on_rates 
        WHERE active = true 
        AND UPPER(rate_type) = 'PER_MILLE'
        AND (rate_value <= 0 OR rate_value >= 1000)
        LIMIT 10
    """)
    invalid_per_mille = cur.fetchall()
    results['rule_3_per_mille_range'] = {
        'pass': len(invalid_per_mille) == 0,
        'failing_count': len(invalid_per_mille),
        'failing_samples': [dict(r) for r in invalid_per_mille],
        'message': f"Found {len(invalid_per_mille)} PER_MILLE rows with invalid rate_value"
    }
    
    # Rule 4: PERCENT_OF_BASIC_RATE validation
    cur.execute("""
        SELECT id, add_on_id, product_code, rate_type, rate_value 
        FROM add_on_rates 
        WHERE active = true 
        AND UPPER(rate_type) = 'PERCENT_OF_BASIC_RATE'
        AND (rate_value <= 0 OR rate_value >= 100)
        LIMIT 10
    """)
    invalid_percent = cur.fetchall()
    results['rule_4_percent_range'] = {
        'pass': len(invalid_percent) == 0,
        'failing_count': len(invalid_percent),
        'failing_samples': [dict(r) for r in invalid_percent],
        'message': f"Found {len(invalid_percent)} PERCENT_OF_BASIC_RATE rows with invalid rate_value"
    }
    
    # Rule 5: POLICY_RATE should have rate_value = 0
    cur.execute("""
        SELECT id, add_on_id, product_code, rate_type, rate_value 
        FROM add_on_rates 
        WHERE active = true 
        AND UPPER(rate_type) = 'POLICY_RATE'
        AND rate_value != 0
        LIMIT 10
    """)
    invalid_policy_rate = cur.fetchall()
    results['rule_5_policy_rate_zero'] = {
        'pass': len(invalid_policy_rate) == 0,
        'failing_count': len(invalid_policy_rate),
        'failing_samples': [dict(r) for r in invalid_policy_rate],
        'message': f"Found {len(invalid_policy_rate)} POLICY_RATE rows with non-zero rate_value"
    }
    if invalid_policy_rate:
        remediation.append("UPDATE add_on_rates SET rate_value = 0 WHERE UPPER(rate_type) = 'POLICY_RATE' AND rate_value != 0;")
    
    # Rule 6: BGR/UVGS occupancy_rule
    cur.execute("""
        SELECT ar.id, am.add_on_code, ar.product_code, ar.occupancy_type 
        FROM add_on_rates ar
        JOIN add_on_master am ON ar.add_on_id = am.id
        WHERE ar.active = true 
        AND ar.product_code IN ('BGRP', 'UVGS')
        AND ar.occupancy_type != 'ONLY_1001_1001_2'
        LIMIT 10
    """)
    invalid_bgr_uvgs = cur.fetchall()
    results['rule_6_bgr_uvgs_occupancy'] = {
        'pass': len(invalid_bgr_uvgs) == 0,
        'failing_count': len(invalid_bgr_uvgs),
        'failing_samples': [dict(r) for r in invalid_bgr_uvgs],
        'message': f"Found {len(invalid_bgr_uvgs)} BGR/UVGS rows with incorrect occupancy_rule"
    }
    if invalid_bgr_uvgs:
        remediation.append("UPDATE add_on_rates SET occupancy_type = 'ONLY_1001_1001_2' WHERE product_code IN ('BGRP', 'UVGS');")
    
    # Rule 7: Others should have EXCEPT_1001_1001_2 or ALL
    cur.execute("""
        SELECT ar.id, am.add_on_code, ar.product_code, ar.occupancy_type 
        FROM add_on_rates ar
        JOIN add_on_master am ON ar.add_on_id = am.id
        WHERE ar.active = true 
        AND ar.product_code NOT IN ('BGRP', 'UVGS')
        AND ar.occupancy_type NOT IN ('EXCEPT_1001_1001_2', 'ALL')
        AND ar.occupancy_type IS NOT NULL
        LIMIT 10
    """)
    invalid_others = cur.fetchall()
    results['rule_7_others_occupancy'] = {
        'pass': len(invalid_others) == 0,
        'failing_count': len(invalid_others),
        'failing_samples': [dict(r) for r in invalid_others],
        'message': f"Found {len(invalid_others)} non-BGR/UVGS rows with incorrect occupancy_rule"
    }
    if invalid_others:
        remediation.append("UPDATE add_on_rates SET occupancy_type = 'ALL' WHERE product_code NOT IN ('BGRP', 'UVGS') AND occupancy_type IS NULL;")
    
    # Rule 8: No duplicates
    cur.execute("""
        SELECT am.add_on_code, ar.product_code, ar.occupancy_type, COUNT(*) as cnt
        FROM add_on_rates ar
        JOIN add_on_master am ON ar.add_on_id = am.id
        WHERE ar.active = true
        GROUP BY am.add_on_code, ar.product_code, ar.occupancy_type
        HAVING COUNT(*) > 1
        LIMIT 10
    """)
    duplicates = cur.fetchall()
    results['rule_8_no_duplicates'] = {
        'pass': len(duplicates) == 0,
        'failing_count': len(duplicates),
        'failing_samples': [dict(r) for r in duplicates],
        'message': f"Found {len(duplicates)} duplicate combinations"
    }
    
    # Rule 9: All add_on_codes exist in master
    cur.execute("""
        SELECT DISTINCT ar.add_on_id, ar.product_code
        FROM add_on_rates ar
        WHERE ar.active = true
        AND ar.add_on_id NOT IN (SELECT id FROM add_on_master)
        LIMIT 10
    """)
    orphaned = cur.fetchall()
    results['rule_9_master_integrity'] = {
        'pass': len(orphaned) == 0,
        'failing_count': len(orphaned),
        'failing_samples': [dict(r) for r in orphaned],
        'message': f"Found {len(orphaned)} orphaned add_on_id references"
    }
    
    # Summary
    all_pass = all(r['pass'] for r in results.values())
    
    output = {
        'all_checks_pass': all_pass,
        'checks': results,
        'remediation_sql': remediation if remediation else None
    }
    
    print(json.dumps(output, indent=2, default=str))
    
    conn.close()
    
    if not all_pass:
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
