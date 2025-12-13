# BGRP Railway Compatibility & Audit Report

## 1. Rate Audit (Python-Based)
Executed `scripts/audit_terrorism_rates.py` against the configured database.
- **Detected**: Multiple slabs for BGRP/Residential (ID 1081, 1122, 1147).
- **Result**: Confirmed all rates are **0.07**. No invalid rates found.
- **Status**: Database is compliant.

## 2. Logic Updates
### `app/services/rating_engine.py`
- Updated `get_terrorism_rate_per_mille`:
  - Added strict TSI range filtering (`si_min <= tsi <= si_max`).
  - Enforced deterministic ordering (`ORDER BY si_min DESC`).
  - Removed implicit fallback logic.

### `app/routers/fire/uiic_fire.py`
- Updated `UBGRRequest`:
  - Made `contentsSI` optional (default `0.0`) to prevent 422 errors.
- Confirmed `calculate_bgrp` strictly aggregates `net = fire + terrorism`.

## 3. Startup Safety Check
- Added `@app.on_event("startup")` in `app/main.py`.
- **Logic**: Performs a live query for BGRP/1001/1Cr TSI upon startup.
- **Enforcement**: If rate != 0.07, raises `RuntimeError` and aborts startup. This prevents silent regressions in production.

## 4. Final Verification
Executed `scripts/verify_bgrp.py` with 1 Crore TSI:
```
Fire:       1500.0 (Correct)
Terrorism:   700.0 (Correct 0.07 rate)
Net:        2200.0 (Correct Aggregation)
GST:         396.0 (Correct 18%)
Result:     ✅ VERIFICATION SUCCESS
```

## 5. Deployment
- Changes are applied to the codebase.
- Database audit confirms rates are correct.
- Startup check will protect the deployment.
- **Action**: Restart/Deploy to Railway to finalize.
