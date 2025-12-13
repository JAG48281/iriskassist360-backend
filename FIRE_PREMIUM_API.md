# Fire Insurance Premium Calculation API

## Overview
Authoritative premium calculation engine for UBGR/UVGR/UVGS Fire insurance products.

## Products Supported
- **UBGR** - United Bharat Griha Raksha (with Terrorism)
- **UVGR** - United Value Griha Raksha (with Terrorism)
- **UVGS** - Udyam Value Griha Suraksha (NO Terrorism)

## API Endpoints

### 1. UBGR Premium Calculation
```
POST /api/fire/ubgr/calculate
```

### 2. UVGR Premium Calculation
```
POST /api/fire/uvgr/calculate
```

### 3. UVGS Premium Calculation
```
POST /api/fire/uvgs/calculate
```

## Request Schema

```json
{
  "productCode": "UBGR",
  "occupancyCode": "1001",
  "buildingSI": 1000000,
  "contentsSI": 200000,
  "addOns": [
    {
      "addOnCode": "EQ",
      "sumInsured": 1200000
    }
  ],
  "paSelection": {
    "proposer": true,
    "spouse": false
  },
  "discountPercentage": 5,
  "loadingPercentage": 10
}
```

## Calculation Flow (STRICT)

### Step 1: Basic Fire Premium
```
Basic Fire Premium = Total SI × Basic Rate / 1000
```
- Total SI = Building SI + Contents SI
- Basic Rate fetched from `product_basic_rates` table

### Step 2: Add-On Premium
```
Add-On Premium = Sum of all add-on premiums + PA premiums
```
- Each add-on calculated based on rate type (per_mille, percentage, fixed)
- PA premiums are flat rates from database

### Step 3: Discount
```
Discount Amount = (Basic Fire Premium + Add-On Premium) × Discount %
```
**CRITICAL**: Discount applies ONLY to (Basic Fire + Add-On)

### Step 4: Subtotal
```
Subtotal = (Basic Fire Premium + Add-On Premium) - Discount Amount
```

### Step 5: Loading
```
Loading Amount = Subtotal × Loading %
```
**CRITICAL**: Loading applies ONLY to Subtotal

### Step 6: Terrorism Premium (UBGR/UVGR only)
```
Terrorism Premium = Total SI × Terrorism Rate / 1000
```
**CRITICAL**: 
- Terrorism is added AFTER Loading
- Terrorism is EXCLUDED from Discount and Loading calculations
- UVGS does NOT have terrorism premium

### Step 7: Net Premium
```
UBGR/UVGR: Net Premium = Subtotal + Loading Amount + Terrorism Premium
UVGS:      Net Premium = Subtotal + Loading Amount
```

### Step 8: Taxes & Gross Premium
```
CGST = Net Premium × 9%
SGST = Net Premium × 9%
Stamp Duty = ₹1 (fixed)
Gross Premium = Net Premium + CGST + SGST + Stamp Duty
```

## Response Schema

```json
{
  "success": true,
  "message": "UBGR Premium Calculated Successfully",
  "productCode": "UBGR",
  "breakdown": {
    "basicFirePremium": 180.0,
    "addOnPremium": 0.0,
    "discountAmount": 0.0,
    "subtotal": 180.0,
    "loadingAmount": 0.0,
    "terrorismPremium": 84.0,
    "netPremium": 264.0,
    "cgst": 23.76,
    "sgst": 23.76,
    "stampDuty": 1.0,
    "grossPremium": 312.52,
    "totalSI": 1200000.0,
    "basicFireRate": 0.15,
    "terrorismRate": 0.07,
    "addOnDetails": []
  }
}
```

## Business Rules

### 1. Discount Rule
- Applies ONLY on: `(Basic Fire Premium + Add-On Premium)`
- Does NOT apply on: Terrorism Premium

### 2. Loading Rule
- Applies ONLY on: `Subtotal` (after discount)
- Does NOT apply on: Terrorism Premium

### 3. Terrorism Rule
- **UBGR/UVGR**: Terrorism applicable, added AFTER loading
- **UVGS**: Terrorism NOT applicable, must be null/zero
- Terrorism rate: 0.07‰ for Residential (1001, 1001_2)

### 4. Rate Sources
- All rates MUST come from database
- No hardcoded rates allowed
- Basic Rate: `product_basic_rates` table
- Terrorism Rate: `terrorism_slabs` table
- Add-On Rates: `add_on_rates` table

## Validation

### Request Validation
- Product Code must be UBGR, UVGR, or UVGS
- Occupancy Code must exist in database
- Sum Insured must be > 0
- Discount/Loading percentages: 0-100

### Calculation Validation
- Basic rate must be found for product/occupancy
- Terrorism rate must be found for UBGR/UVGR
- All calculations rounded to 2 decimal places
- Net Premium must reconcile exactly

## Error Handling

### 400 Bad Request
- Invalid product code
- Invalid occupancy code
- Missing required fields
- Rate not found in database

### 500 Internal Server Error
- Database connection failure
- Unexpected calculation error

## Testing

### Test Case 1: Basic Calculation
```bash
curl -X POST http://localhost:8000/api/fire/ubgr/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "productCode": "UBGR",
    "occupancyCode": "1001",
    "buildingSI": 1000000,
    "contentsSI": 200000,
    "addOns": [],
    "paSelection": {"proposer": false, "spouse": false},
    "discountPercentage": 0,
    "loadingPercentage": 0
  }'
```

### Test Case 2: With Discount & Loading
```bash
curl -X POST http://localhost:8000/api/fire/ubgr/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "productCode": "UBGR",
    "occupancyCode": "1001",
    "buildingSI": 1000000,
    "contentsSI": 200000,
    "addOns": [],
    "paSelection": {"proposer": true, "spouse": true},
    "discountPercentage": 10,
    "loadingPercentage": 15
  }'
```

### Test Case 3: UVGS (No Terrorism)
```bash
curl -X POST http://localhost:8000/api/fire/uvgs/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "productCode": "UVGS",
    "occupancyCode": "1001",
    "buildingSI": 1000000,
    "contentsSI": 200000,
    "addOns": [],
    "paSelection": {"proposer": false, "spouse": false},
    "discountPercentage": 0,
    "loadingPercentage": 0
  }'
```

## Implementation Files

- **Schema**: `app/schemas/fire_premium.py`
- **Service**: `app/services/fire_premium_service.py`
- **Router**: `app/routers/fire/fire_premium.py`
- **Seed Data**: `seed.py` (UBGR/UVGR products and rates)

## Database Tables Used

1. `product_master` - Product definitions
2. `occupancies` - Occupancy/Risk descriptions
3. `product_basic_rates` - Basic fire rates
4. `terrorism_slabs` - Terrorism rates by occupancy type
5. `add_on_rates` - Add-on premium rates
6. `add_on_master` - Add-on definitions

## Notes

- Backend is the SINGLE source of truth for premiums
- Frontend must NOT calculate premiums
- All calculations are deterministic and auditable
- Rounding uses standard ROUND_HALF_UP to 2 decimal places
