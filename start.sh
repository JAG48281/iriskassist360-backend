#!/bin/bash
set -e

echo "-------------------------------------"
echo "STARTING DEPLOYMENT SCRIPT"
echo "-------------------------------------"

echo "Current Directory:"
pwd
echo "Directory Contents:"
ls -la

echo "-------------------------------------"
echo "STEP 1: DATABASE MIGRATIONS"
echo "-------------------------------------"
alembic upgrade head

echo "-------------------------------------"
echo "STEP 2: SEEDING DATA"
echo "-------------------------------------"
if [ -f "seed.py" ]; then
    echo "Found seed.py, executing..."
    python -u seed.py
else
    echo "ERROR: seed.py NOT FOUND!"
    exit 1
fi

echo "-------------------------------------"
echo "STEP 3: STARTING APPLICATION"
echo "-------------------------------------"
uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers
