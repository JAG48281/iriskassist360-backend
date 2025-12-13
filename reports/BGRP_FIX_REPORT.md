# BGRP Fix & Validation Report

## 1. Product Master Fix
- **Status**: Fixed.
- **Action**: Removed incorrect `UBGR` product alias from `seed.py`.
- **Cleanup**: Executed script to delete `UBGR` from `product_master` table.
- **Verification**: Confirmed `BGRP` (Bharat Griha Raksha Policy) is the active product code.

## 2. Rate Engine & Table Linkage
- **Issue Found**: The `rating_engine.py` service was querying `product_basic_rates` using `occupancy_code` column which does not exist. It also created a duplicate DB connection.
- **Fix**: 
  - Updated `rating_engine.py` to use shared `app.database.engine`.
  - Rewrote SQL query to `JOIN occupancies` table to resolve `iib_code` (e.g., '101') to `occupancy_id`.
  - Fixed `get_terrorism_rate_per_mille` to correctly query `terrorism_slabs`.
- **Seeding Correction**:
  - Found `101` occupancy missing in local DB. Force seeded `101`.
  - Found BGRP missing in terrorism slabs seeding. Updated `seed.py` and force seeded BGRP slab.
  - Confirmed `ProductBasicRate` for BGRP exists (Rate: 0.15).

## 3. Calculation Logic Update (UIIC Fire Endpoint)
- **Endpoint**: `/irisk/fire/uiic/bgrp/calculate`
- **Updates**:
  - dynamic rate lookup using `get_basic_rate_per_mille` (was hardcoded 0.15).
  - dynamic terrorism rate lookup using `get_terrorism_rate_per_mille` (was hardcoded 0.07).
  - **Minimum Premium Logic**: logic now explicitly checks `basic_rate > 0`. If `0`, it raises validation error instead of applying default. Minimum premium (`50.0`) is only applied if calculated `Net Premium < 50`.

## 4. Final Validation Log
Simulated Request:
- Building SI: 10,00,000
- Contents SI: 5,00,000
- Terrorism: Yes

**Output Log**:
```
✅ Response Received:
  Net Premium: 375.0
  Breakdown: {
     'totalSI': 1500000.0, 
     'firePremium': 225.0, 
     'terrorismPremium': 150.0, 
     'paPremium': 0.0, 
     'basePremium': 375.0, 
     'discountApplied': 0.0, 
     'appliedRate': 0.15
  }
```
**Conclusion**:
- Rate applied (0.15) matches DB.
- Terrorism rate (0.10) applied correctly (15L * 0.1 = 150).
- Total (375) > Min Premium (50). Logic valid.
