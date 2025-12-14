# Risk Rate Resolution - Verification Checklist

## ✅ Code Changes Completed

- [x] Enhanced `get_basic_rate_per_mille()` with explicit error messages
- [x] Enhanced `get_occupancy_details()` to include `section_aift`
- [x] Added `occupancyId` to `RiskDescriptionResponse` schema
- [x] Added `risk_rate` and `rate_source` to `CalculationMeta` schema
- [x] Updated risk descriptions endpoint to include `occupancyId`
- [x] Updated occupancies endpoint to include `occupancy_type`
- [x] Updated premium calculation service to populate `risk_rate` and `rate_source`

## 🧪 Testing Checklist

### Database Verification
```bash
python verify_db_data.py
```
Expected: Shows occupancies and product_basic_rates data

### Unit Tests
```bash
python test_risk_rate_resolution.py
```
Expected: All tests pass, rates are fetched correctly

### API Integration Tests
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload

# Terminal 2: Run tests
python test_api_risk_rate.py
```
Expected:
- ✅ Risk descriptions include `occupancyId`
- ✅ Premium calculation returns `risk_rate` > 0
- ✅ `rate_source` = "product_basic_rates"
- ✅ Error handling works for missing rates

## 📋 Manual Verification Steps

### Step 1: Check Risk Descriptions Endpoint
```bash
curl "http://localhost:8000/master/risk-descriptions?productCode=UBGR"
```
Verify response includes:
- [ ] `occupancyId` (integer, PRIMARY KEY)
- [ ] `iibCode` (string)
- [ ] `riskDescription` (string)
- [ ] `occupancyType` (string)
- [ ] `aiftSection` (string)

### Step 2: Check Premium Calculation
```bash
curl -X POST "http://localhost:8000/fire/ubgr/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "productCode": "UBGR",
    "occupancyCode": "1001",
    "buildingSI": 1000000,
    "contentsSI": 200000,
    "terrorismSI": 1200000,
    "addOns": [],
    "paSelection": {"proposer": true, "spouse": false},
    "discountPercentage": 0,
    "loadingPercentage": 0,
    "policyPeriod": 1
  }'
```
Verify response includes:
- [ ] `meta.applied_rate` > 0
- [ ] `meta.risk_rate` > 0 (same as applied_rate)
- [ ] `meta.rate_source` = "product_basic_rates"
- [ ] `meta.terrorism_rate` > 0
- [ ] `breakdown.basic_premium` > 0

### Step 3: Check Error Handling
```bash
curl -X POST "http://localhost:8000/fire/ubgr/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "productCode": "UBGR",
    "occupancyCode": "9999",
    "buildingSI": 1000000,
    "contentsSI": 0,
    "terrorismSI": 1000000,
    "addOns": [],
    "paSelection": {"proposer": false, "spouse": false},
    "discountPercentage": 0,
    "loadingPercentage": 0,
    "policyPeriod": 1
  }'
```
Verify response:
- [ ] HTTP 400 status
- [ ] Error message contains "not configured"
- [ ] Error message mentions specific product and occupancy

## 🔍 Log Verification

Start the backend and check logs for:

### Successful Rate Lookup:
```
✅ Basic Rate Lookup: UBGR/1001 (OccID: 1, Type: Residential) → 1.5‰
📋 Occupancy Details: 1001 → ID=1, Type=Residential, Section=I
```

### Failed Rate Lookup:
```
❌ Base risk rate not configured for product 'UBGR' + occupancy '9999'. 
   Please configure in product_basic_rates table.
```

## 🗄️ Database Verification

### Check Occupancies Table:
```sql
SELECT id, iib_code, occupancy_type, section_aift 
FROM occupancies 
WHERE iib_code IN ('1001', '1001_2')
LIMIT 5;
```
Expected: At least 2 rows (1001, 1001_2)

### Check Product Basic Rates:
```sql
SELECT pbr.product_code, pbr.basic_rate, o.iib_code, o.occupancy_type
FROM product_basic_rates pbr
JOIN occupancies o ON pbr.occupancy_id = o.id
WHERE pbr.product_code IN ('UBGR', 'BGRP', 'UVGR', 'UVGS')
  AND o.iib_code = '1001';
```
Expected: At least 4 rows (one for each product)

### Check Join Integrity:
```sql
-- Verify all rates have valid occupancy_id references
SELECT COUNT(*) as orphaned_rates
FROM product_basic_rates pbr
LEFT JOIN occupancies o ON pbr.occupancy_id = o.id
WHERE o.id IS NULL;
```
Expected: 0 (no orphaned rates)

## 📊 Expected Results Summary

### API Response Structure:
```json
{
  "success": true,
  "message": "UBGR Premium Calculated Successfully",
  "productCode": "UBGR",
  "breakdown": {
    "basic_premium": 1800.00,
    "add_on_premium": 7.00,
    "discount_amount": 0.00,
    "sub_total": 1807.00,
    "loading_amount": 0.00,
    "terrorism_premium": 84.00,
    "net_premium": 1891.00,
    "cgst": 170.19,
    "sgst": 170.19,
    "stamp_duty": 1.00,
    "gross_premium": 2232.38
  },
  "meta": {
    "applied_rate": 1.5,
    "risk_rate": 1.5,
    "rate_source": "product_basic_rates",
    "terrorism_rate": 0.07,
    "occupancy_code": "1001",
    "product_code": "UBGR"
  }
}
```

### Key Validations:
- ✅ `meta.risk_rate` is NOT 0
- ✅ `meta.risk_rate` equals `meta.applied_rate`
- ✅ `meta.rate_source` is "product_basic_rates"
- ✅ `breakdown.basic_premium` is calculated correctly
- ✅ Error messages are explicit when rate missing

## 🚀 Production Deployment Checklist

Before deploying to production:

- [ ] All unit tests pass
- [ ] All API tests pass
- [ ] Database has rates for UBGR/BGRP/UVGR/UVGS
- [ ] Error messages are explicit and helpful
- [ ] Logs show emoji indicators correctly
- [ ] No hardcoded rates in code
- [ ] No default to 0 for missing rates
- [ ] Frontend updated to display `risk_rate` from API

## 📝 Notes

### If Risk Rate Shows 0:
1. Check database: `python verify_db_data.py`
2. Verify rate exists in `product_basic_rates` table
3. Check logs for error messages
4. Ensure `occupancy_id` FK is correct

### If Error Messages Not Explicit:
1. Check `app/services/rating_engine.py`
2. Verify `get_basic_rate_per_mille()` raises ValueError with explicit message
3. Check API endpoint error handling

### If Rate Source Missing:
1. Check `app/schemas/fire_premium.py` - `CalculationMeta` should have `rate_source`
2. Check `app/services/fire_premium_service.py` - should populate `rate_source`

## ✅ Sign-Off

Once all items are checked:
- [ ] Code review completed
- [ ] All tests passing
- [ ] Database verified
- [ ] API responses correct
- [ ] Error handling working
- [ ] Documentation updated
- [ ] Ready for deployment

---
**Implementation Date**: 2025-12-14
**Implemented By**: Senior Backend Engineer
**Status**: ✅ COMPLETE
