# Fire Risk Rate API Endpoint

## Endpoint
```
GET /api/fire/risk-rate
```

## Description
Returns the Fire risk rate (per mille) based on the selected product code, IIB code, and AIFT section. This endpoint provides the backend as the single source of truth for risk rates, with no frontend calculation allowed.

## Request Parameters

### Query Parameters (All Required)

| Parameter | Type | Description | Valid Values |
|-----------|------|-------------|--------------|
| `productCode` | string | Insurance product code | `UBGR`, `BGRP`, `SFSP`, `IAR`, `BSUS`, `BLUS`, `UVUS`, `UVGR` |
| `iibCode` | string | IIB code from occupancy | Any valid IIB code from occupancies table |
| `aiftSection` | string | AIFT section from occupancy | Section identifier (e.g., "A", "Zone I", "Zone II", "Zone III") |

## Product Normalization

The API implements strict product code normalization:
- **UBGR → BGRP** (automatically converted)

All database queries use normalized product codes.

## Data Sources

### fire_iib_rates Table
Used for: **BGRP**, **SFSP**, **IAR**
- Columns: `iib_code`, `rate_per_mille`
- Query matches on: `iib_code`

### fire_bsus_rates Table
Used for: **BSUS**, **BLUS**, **UVUS**, **UVGR**
- Columns: `iib_code`, `eq_zone`, `rate_per_mille`
- Query matches on: `iib_code` AND `eq_zone` (uses `aiftSection` as `eq_zone`)
- Fallback: If exact zone match not found, returns first available rate for the IIB code

## Response Format

### Success Response (200 OK)
```json
{
  "success": true,
  "rate_per_mille": 0.15
}
```

### Not Found Response (404)
```json
{
  "success": false,
  "message": "No rate found for product BGRP, IIB code 99999, and AIFT section A"
}
```

### Bad Request Response (400)
```json
{
  "success": false,
  "message": "Invalid product code. Must be one of: BGRP, SFSP, IAR, BSUS, BLUS, UVUS, UVGR"
}
```

### Internal Server Error (500)
```json
{
  "success": false,
  "message": "Internal server error: <error details>"
}
```

## Example Requests

### Example 1: UBGR Product (Auto-normalized to BGRP)
```bash
GET /api/fire/risk-rate?productCode=UBGR&iibCode=1001&aiftSection=A
```

**Response:**
```json
{
  "success": true,
  "rate_per_mille": 0.15
}
```

### Example 2: BGRP Product
```bash
GET /api/fire/risk-rate?productCode=BGRP&iibCode=2001&aiftSection=A
```

**Response:**
```json
{
  "success": true,
  "rate_per_mille": 0.37
}
```

### Example 3: BSUS Product with Zone
```bash
GET /api/fire/risk-rate?productCode=BSUS&iibCode=1002&aiftSection=Zone%20I
```

**Response:**
```json
{
  "success": true,
  "rate_per_mille": 0.455
}
```

### Example 4: Invalid IIB Code (404)
```bash
GET /api/fire/risk-rate?productCode=BGRP&iibCode=INVALID&aiftSection=A
```

**Response:**
```json
{
  "success": false,
  "message": "No rate found for product BGRP, IIB code INVALID, and AIFT section A"
}
```

## Frontend Integration

### Auto-populating Risk Rate Field

When a user selects a risk description in the frontend:

1. Extract `iibCode` and `aiftSection` from the selected risk/occupancy
2. Get the current `productCode` 
3. Call this API endpoint
4. Populate the read-only "Risk Rate (‰)" field with the returned `rate_per_mille`

### Example JavaScript/Flutter Code

```javascript
async function fetchRiskRate(productCode, iibCode, aiftSection) {
  const url = new URL('/api/fire/risk-rate', API_BASE_URL);
  url.searchParams.append('productCode', productCode);
  url.searchParams.append('iibCode', iibCode);
  url.searchParams.append('aiftSection', aiftSection);
  
  try {
    const response = await fetch(url);
    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        return data.rate_per_mille;
      }
    }
    // Handle error
    return null;
  } catch (error) {
    console.error('Failed to fetch risk rate:', error);
    return null;
  }
}
```

## Testing

Comprehensive test suite available at: `tests/test_fire_risk_rate.py`

Run tests with:
```bash
python -m pytest tests/test_fire_risk_rate.py -v
```

### Test Coverage

✅ UBGR → BGRP normalization  
✅ Valid IIB code returns correct rate  
✅ Invalid combination returns 404  
✅ Response keys exactly match contract  
✅ All product types (BGRP, SFSP, IAR, BSUS, BLUS, UVUS, UVGR)  
✅ Case-insensitive product code handling  
✅ Whitespace handling  
✅ Missing parameter validation  
✅ Error response format  
✅ Rate precision validation  

## Business Rules

1. **No Frontend Calculation**: All risk rate logic is handled by the backend
2. **Product Normalization**: UBGR is automatically converted to BGRP
3. **Exact Match Required**: Query must match on product_code, iib_code, and (for BSUS products) eq_zone
4. **404 on No Match**: Returns 404 if no rate is found for the given combination
5. **Zone Fallback**: For BSUS products, if exact zone match not found, returns first available rate with a warning

## Database Schema

### fire_iib_rates
```sql
CREATE TABLE fire_iib_rates (
    iib_code VARCHAR(20) PRIMARY KEY,
    rate_per_mille NUMERIC(10, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### fire_bsus_rates
```sql
CREATE TABLE fire_bsus_rates (
    iib_code VARCHAR(20) NOT NULL,
    eq_zone VARCHAR(20) NOT NULL,
    rate_per_mille NUMERIC(10, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (iib_code, eq_zone)
);
```

## Constraints

❌ Do NOT modify occupancies table  
❌ Do NOT embed rates in risk-description API  
❌ Do NOT break existing `/api/fire/calculate` endpoint  
✅ Backend is single source of truth  
✅ Production-ready with comprehensive error handling  

## Deployment

This endpoint is automatically registered in `app/main.py` and will be available when the application starts.

No additional configuration required.

## Monitoring & Logging

The endpoint logs:
- ✅ Successful rate lookups with details
- ⚠️ Zone fallback warnings (for BSUS products)
- ⚠️ 404 responses (no rate found)
- 🔥 500 errors with full stack trace

Example log output:
```
INFO: ✅ Rate found: 0.15‰ for productCode=BGRP, iibCode=1001, aiftSection=A
WARNING: Could not match zone 'Unknown Zone', using first available rate for IIB 1002
WARNING: No rate found for productCode=BGRP, iibCode=INVALID, aiftSection=A
```

## Version History

- **v1.0.0** (2025-12-17): Initial implementation
  - Support for all Fire LOB products
  - Product normalization (UBGR → BGRP)
  - Comprehensive error handling
  - Full test coverage
