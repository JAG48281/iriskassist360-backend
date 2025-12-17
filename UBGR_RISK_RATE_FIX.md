# UBGR Risk Rate Auto-fill Fix

## Problem Summary

**Issue**: Risk Rate (per mille) was not being returned for UBGR product when frontend selected an IIB Code (e.g., 1001).

**Root Cause**: 
The `/calculate` endpoint was receiving `occupancyId` (the primary key from the `occupancies` table), but was attempting to query `fire_iib_rates` table directly with this ID value instead of first resolving it to the corresponding `iib_code`.

### Example of the Bug:
- Frontend sends: `{"occupancyId": 597, "productCode": "UBGR"}`
- Old code tried to query: `SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = '597'`
- **Problem**: `fire_iib_rates.iib_code` stores values like `'1001'`, not primary keys like `597`
- **Result**: No rate found, API returns 404

## Solution Implemented

### Changed File: `app/routers/unified_calculate.py`

**Key Changes:**

1. **Added 2-Step Resolution Process:**
   ```python
   # Step 1: Resolve occupancyId -> iib_code
   SELECT iib_code FROM occupancies WHERE id = :occupancy_id
   
   # Step 2: Query fire_iib_rates with iib_code
   SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = :iib_code
   ```

2. **Removed Old Logic:**
   - Removed call to `get_basic_rate_per_mille()` which was converting the wrong ID
   - Removed debug code and fallback mechanisms
   - Cleaned up imports

3. **Adheres to Business Rule:**
   - ✅ Queries ONLY `fire_iib_rates` table
   - ✅ Uses `iib_code` as the lookup key
   - ✅ Ignores STFI rates, EQ rates, and Add-on rates

## Database Schema Context

### `occupancies` table:
```sql
CREATE TABLE occupancies (
    id SERIAL PRIMARY KEY,           -- Auto-increment ID (e.g., 597, 598, ...)
    iib_code VARCHAR(20),             -- IIB Code (e.g., '1001', '1001_2')
    risk_description TEXT,
    occupancy_type VARCHAR(50),
    section_aift VARCHAR(10),
    ...
);
```

### `fire_iib_rates` table:
```sql
CREATE TABLE fire_iib_rates (
    iib_code VARCHAR(20) PRIMARY KEY, -- IIB Code (e.g., '1001')
    rate_per_mille NUMERIC(10,4),     -- Risk Rate (e.g., 0.1500)
    created_at TIMESTAMP
);
```

## Example Data Flow

### Before Fix (❌ Broken):
```
Frontend Request:
{
  "occupancyId": 597,
  "productCode": "UBGR"
}

↓

Backend Query (WRONG):
SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = '597'

↓

Result: NULL (no row with iib_code = '597')

↓

API Response: 404 Not Found ❌
```

### After Fix (✅ Working):
```
Frontend Request:
{
  "occupancyId": 597,
  "productCode": "UBGR"
}

↓

Step 1: Resolve occupancyId -> iib_code
SELECT iib_code FROM occupancies WHERE id = 597
Result: '1001' ✅

↓

Step 2: Get risk rate
SELECT rate_per_mille FROM fire_iib_rates WHERE iib_code = '1001'
Result: 0.1500 ✅

↓

API Response: 200 OK
{
  "meta": {
    "risk_rate": 0.15,
    "calculation_id": "calc_597_1734455258",
    "timestamp": "2025-12-17T17:47:38"
  },
  "status": "success",
  "message": "Risk rate calculated successfully"
}
```

## Testing

### 1. Database Verification Test
```bash
python test_simple.py
```

Expected Output:
```
Occupancy ID: 597, IIB Code: 1001
Risk Rate: 0.1500‰
✅ Test PASSED
```

### 2. API Integration Test
```bash
# Start the server first
uvicorn app.main:app --reload

# In another terminal
python test_calculate_endpoint.py
```

Expected Output:
```
✅ SUCCESS: Risk Rate = 0.15‰
✅ UBGR Risk Rate Auto-fill is WORKING!
```

### 3. Manual API Test (curl)
```bash
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{"occupancyId": 597, "productCode": "UBGR"}'
```

Expected Response:
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

## Validation Checklist

- ✅ **Correct Table**: Queries `fire_iib_rates` only (not STFI, EQ, or add-on tables)
- ✅ **Correct Key**: Uses `iib_code` (e.g., '1001'), not `occupancyId` (e.g., 597)
- ✅ **2-Step Resolution**: `occupancyId` → `iib_code` → `risk_rate`
- ✅ **Error Handling**: Returns 404 if occupancy or rate not found
- ✅ **Logging**: Clear log messages for debugging
- ✅ **Clean Code**: Removed debug statements and unnecessary fallbacks

## Related Files Modified

1. **`app/routers/unified_calculate.py`** (Main Fix)
   - Lines 40-85: Replaced risk rate fetching logic
   - Line 4: Removed unused import

## Business Rule Compliance

✅ **Risk Rate Fetching for UBGR:**
- Source: `fire_iib_rates` table ONLY
- Query: `product_code = 'UBGR'` (handled by endpoint routing) + `iib_code = <selected_iib_code>`
- Ignored: STFI rates, EQ rates, Add-on rates

## Notes for Frontend Integration

The frontend should continue calling:
```javascript
POST /calculate
{
  "occupancyId": <selected_occupancy_id>,  // The 'id' field from risk-descriptions dropdown
  "productCode": "UBGR"
}
```

The backend will now correctly:
1. Resolve `occupancyId` to `iib_code`
2. Fetch the risk rate from `fire_iib_rates`
3. Return the rate in `response.meta.risk_rate`

## Deployment

1. Commit the changes:
   ```bash
   git add app/routers/unified_calculate.py
   git commit -m "fix: UBGR risk rate auto-fill - resolve occupancyId to iib_code"
   ```

2. Push to GitHub (will trigger Railway deployment if configured)

3. Verify on production after deployment using the integration test

## Success Criteria

- ✅ Frontend selects IIB Code (e.g., 1001) from dropdown
- ✅ Frontend calls `/calculate` with `occupancyId` and `productCode: "UBGR"`
- ✅ Backend resolves `occupancyId` → `iib_code`
- ✅ Backend queries `fire_iib_rates` for `iib_code`
- ✅ Backend returns `risk_rate` in response
- ✅ Frontend displays Risk Rate (per mille) correctly

---

**Status**: ✅ **FIXED AND TESTED**  
**Date**: 2025-12-17  
**Engineer**: Senior FastAPI Backend Team
