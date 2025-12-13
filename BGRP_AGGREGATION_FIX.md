# BGRP Aggregation Fix Report

## 1. Issue Resolved
- **Problem**: Net Premium for BGRP was incorrectly excluding the terrorism premium, despite backend logic calculating it.
- **Root Cause**: The terrorism premium was calculated conditionally or not added during the final aggregation step in `calculate_bgrp`.
- **Requirements**:
  - Terrorism must rely on DB rate.
  - Net Premium = Fire + Terrorism (Always).
  - No conditions on checkbox.

## 2. Implementation Details
- **File**: `app/routers/fire/uiic_fire.py`
- **Logic Change**: 
  - Calculated `terrorismPremium` unconditionally using `get_terrorism_rate_per_mille`.
  - Updated aggregation: `netPremium = discounted_base + terrorismPremium`.
  - Added explicit hard log: `BGRP BACKEND DEBUG | fire=..., terrorism=..., net=...`.
  - Updated Response Schema to include explicit `firePremium` and `terrorismPremium` keys.

## 3. Verification
Executed test script with 1 Crore Building SI:
```
RESPONSE DATA:
  Fire Premium: 1500.0   (0.15 per mille)
  Terrorism Premium: 1000.0 (0.10 per mille)
  Net Premium: 2500.0
AGGREGATION CHECK PASS: 2500.0 == 1500.0 + 1000.0
```

## 4. Status
✅ **FIXED & VERIFIED**.
The backend now correctly aggregates terrorism into the final premium for BGRP.
Please restart the backend service.
