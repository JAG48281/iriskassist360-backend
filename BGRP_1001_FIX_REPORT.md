# BGRP 1001 Occupancy Fix Report

## 1. Issue Resolved
- **Problem**: BGRP must use Occupancy Code `1001` (Residential) strictly, but system was using `101`. Terrorism rate was 0.10, required 0.07.
- **Root Cause**: Database had duplicate occupancies (`101` and `1001`). Rates were attached to `101`. Code referenced `101`.
- **Fix Applied**: 
  1. Migrated all rates (Basic, STFI, EQ, BSUS) from Occupancy `101` to `1001`.
  2. Deleted redundant Occupancy `101`.
  3. Updated `terrorism_slabs` rate to **0.07** for BGRP.
  4. Updated Backend Logic to strictly use `1001` and enforce validation.

## 2. Code Changes
- **`app/services/rating_engine.py`**:
  - `get_terrorism_rate_per_mille` defaults to `"1001"`.
  - Added logging for selected Occupancy Code and Rate.
- **`app/routers/fire/uiic_fire.py`**:
  - Strictly sets `occupancy_code = "1001"`.
  - Validates terrorism rate is **0.07** (tolerance 0.00001).
  - Response includes strict breakdown:
    ```json
    "breakdown": {
        "fireRate": 0.15,
        "terrorismRate": 0.07,
        "occupancyCode": 1001
    }
    ```

## 3. Verification Results
Test Simulation (TSI 10,000,000):
```
Fire Premium:       1,500.0  (Rate 0.15)
Terrorism Premium:    700.0  (Rate 0.07)
Net Premium:        2,200.0  (Correct Sum)
Occupancy Code:     1001     (Correct)
Status:             SUCCESS
```

## 4. Next Steps
- **Deploy**: Push changes to Railway.
- **Restart**: Backend service must restart to pick up code changes (DB changes are persisted).
