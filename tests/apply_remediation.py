import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Apply remediation
print("Applying remediation: Setting policy_rate values to 0...")
cur.execute("UPDATE add_on_rates SET rate_value = 0 WHERE UPPER(rate_type) = 'POLICY_RATE' AND rate_value != 0")
affected = cur.rowcount
print(f"Updated {affected} rows")

conn.commit()
conn.close()

print("✅ Remediation complete")
