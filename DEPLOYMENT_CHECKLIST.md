# UBGR Risk Rate Auto-fill Fix - Deployment Checklist

## ✅ Changes Summary

### Modified Files
1. **`app/routers/unified_calculate.py`**
   - Fixed risk rate fetching logic for UBGR product
   - Added 2-step resolution: occupancyId → iib_code → risk_rate
   - Removed unused `get_basic_rate_per_mille` import
   - Cleaned up debug code and fallback mechanisms

### Test Files Created
1. **`test_simple.py`** - Quick database query test
2. **`test_calculate_endpoint.py`** - API integration test
3. **`test_ubgr_comprehensive.py`** - Full test suite (5 test cases)
4. **`tests/test_ubgr_risk_rate_fix.py`** - Unit test

### Documentation Created
1. **`UBGR_RISK_RATE_FIX.md`** - Complete problem analysis and solution documentation

## ✅ Pre-Deployment Verification

### 1. Syntax Check
```bash
python -m py_compile app/routers/unified_calculate.py
```
**Status**: ✅ PASSED

### 2. Database Tests
```bash
python test_simple.py
```
**Expected Output**:
```
Occupancy ID: 597, IIB Code: 1001
Risk Rate: 0.1500‰
✅ Test PASSED
```
**Status**: ✅ PASSED

### 3. Comprehensive Test Suite
```bash
python test_ubgr_comprehensive.py
```
**Tests**:
- ✅ Schema verification (fire_iib_rates structure)
- ✅ Data integrity (UBGR rates exist)
- ✅ Occupancy resolution (ID → IIB code mapping)
- ✅ End-to-end flow (complete resolution chain)
- ✅ Multiple occupancies (all UBGR occupancies resolved)

**Status**: ✅ ALL TESTS PASSED

## 📋 Deployment Steps

### Step 1: Commit Changes
```bash
git add app/routers/unified_calculate.py
git add UBGR_RISK_RATE_FIX.md
git add DEPLOYMENT_CHECKLIST.md
git commit -m "fix(ubgr): resolve occupancyId to iib_code for risk rate auto-fill

BREAKING CHANGE: Fixed missing risk rate for UBGR product

- Previously: /calculate endpoint used occupancyId directly as iib_code
- Now: Properly resolves occupancyId → iib_code → fire_iib_rates lookup
- Adheres to business rule: UBGR queries ONLY fire_iib_rates table
- Tested: All 5 test cases passing

Closes: UBGR-RISK-RATE-AUTOFILL
"
```

### Step 2: Push to Repository
```bash
git push origin main
```

### Step 3: Verify Railway Deployment (if auto-deploy enabled)
- Watch Railway logs for successful deployment
- Check that migrations run successfully
- Verify app starts without errors

### Step 4: Production Smoke Test
```bash
# Test the deployed API
curl -X POST https://your-railway-app.railway.app/calculate \
  -H "Content-Type: application/json" \
  -d '{"occupancyId": 597, "productCode": "UBGR"}'
```

**Expected Response**:
```json
{
  "meta": {
    "risk_rate": 0.15,
    "calculation_id": "calc_597_...",
    "timestamp": "2025-12-17T..."
  },
  "status": "success",
  "message": "Risk rate calculated successfully"
}
```

### Step 5: Frontend Integration Test
- Have frontend team test with actual UI
- Verify Risk Rate (per mille) field auto-fills after IIB Code selection
- Confirm value matches expected rate from database

## 🔍 Monitoring

### Log Messages to Watch For

**Success Indicators** (should appear in logs):
```
✅ "🔍 Resolved: occupancyId=597 -> iib_code=1001"
✅ "✅ UBGR Risk Rate: iib_code=1001, rate=0.15‰ (source: fire_iib_rates)"
✅ "✅ Risk rate calculated: 0.15‰"
```

**Error Indicators** (should NOT appear):
```
❌ "❌ Occupancy ID {id} not found"
❌ "❌ No rate in fire_iib_rates for iib_code={code}"
❌ "🔥 Error fetching risk rate"
```

## 🎯 Success Criteria

- [ ] Code compiles without syntax errors
- [ ] All 5 test cases pass
- [ ] Deployment succeeds on Railway
- [ ] API returns 200 OK with risk_rate in response
- [ ] Frontend displays risk rate correctly
- [ ] No errors in production logs

## 🔄 Rollback Plan (if needed)

If the deployment causes issues:

### Option 1: Git Revert
```bash
git revert HEAD
git push origin main
```

### Option 2: Manual Fix
The old logic can be restored by reverting `app/routers/unified_calculate.py` to use:
```python
risk_rate = float(get_basic_rate_per_mille(product_code=product_code, occupancy_id=request.occupancyId))
```

However, this will restore the bug. Better to fix forward with a patch.

## 📞 Support Information

### Key Files for Debugging
- **Endpoint**: `app/routers/unified_calculate.py` (lines 50-85)
- **Database**: `fire_iib_rates` table (iib_code, rate_per_mille)
- **Occupancies**: `occupancies` table (id, iib_code)

### Database Queries for Support
```sql
-- Check if rate exists for an IIB code
SELECT * FROM fire_iib_rates WHERE iib_code = '1001';

-- Check occupancy resolution
SELECT id, iib_code, risk_description 
FROM occupancies 
WHERE id = 597;

-- Full resolution check
SELECT o.id, o.iib_code, f.rate_per_mille
FROM occupancies o
LEFT JOIN fire_iib_rates f ON o.iib_code = f.iib_code
WHERE o.id = 597;
```

## 📊 Performance Impact

- **Response Time**: No significant change (added 1 extra query)
- **Database Load**: Minimal (simple indexed lookups)
- **Error Rate**: Should DECREASE (proper resolution reduces 404s)

## 🎉 Deployment Status

- [x] Code Review Complete
- [x] Tests Passing (5/5)
- [x] Documentation Updated
- [ ] Deployed to Production
- [ ] Frontend Verified
- [ ] Monitoring Confirmed

---

**Last Updated**: 2025-12-17  
**Engineer**: Senior FastAPI Backend Team  
**Ticket**: UBGR-RISK-RATE-AUTOFILL
