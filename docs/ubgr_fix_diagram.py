"""
ASCII Diagram: UBGR Risk Rate Auto-fill Flow
"""

BEFORE_FIX = """
╔════════════════════════════════════════════════════════════════════╗
║                        BEFORE FIX (❌ BROKEN)                        ║
╚════════════════════════════════════════════════════════════════════╝

Frontend (Flutter)
      │
      │ POST /calculate
      │ {"occupancyId": 597, "productCode": "UBGR"}
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: app/routers/unified_calculate.py                      │
│                                                                 │
│  OLD CODE:                                                      │
│  risk_rate = get_basic_rate_per_mille(                         │
│      product_code="BGRP",                                       │
│      occupancy_id=597  ◄── WRONG! This is PRIMARY KEY, not IIB │
│  )                                                              │
└─────────────────────────────────────────────────────────────────┘
      │
      │ iib_code = str(597) = "597"
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Database Query: fire_iib_rates                                 │
│                                                                 │
│  SELECT rate_per_mille                                          │
│  FROM fire_iib_rates                                            │
│  WHERE iib_code = '597'  ◄── NO SUCH RECORD!                    │
└─────────────────────────────────────────────────────────────────┘
      │
      │ Result: NULL ❌
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Response: 404 Not Found                                        │
│  {                                                              │
│    "error": "Risk rate not found",                              │
│    "meta": {"risk_rate": null}                                  │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘

❌ Frontend cannot display Risk Rate - BROKEN!
"""

AFTER_FIX = """
╔════════════════════════════════════════════════════════════════════╗
║                        AFTER FIX (✅ WORKING)                        ║
╚════════════════════════════════════════════════════════════════════╝

Frontend (Flutter)
      │
      │ POST /calculate
      │ {"occupancyId": 597, "productCode": "UBGR"}
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: app/routers/unified_calculate.py                      │
│                                                                 │
│  NEW CODE - STEP 1: Resolve occupancyId → iib_code             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ SELECT iib_code FROM occupancies WHERE id = 597           │ │
│  │ Result: '1001' ✅                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
      │
      │ iib_code = "1001" ✅
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: app/routers/unified_calculate.py                      │
│                                                                 │
│  NEW CODE - STEP 2: Query fire_iib_rates with iib_code         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ SELECT rate_per_mille                                     │ │
│  │ FROM fire_iib_rates                                       │ │
│  │ WHERE iib_code = '1001'  ◄── CORRECT!                     │ │
│  │ Result: 0.1500 ✅                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
      │
      │ risk_rate = 0.15 ✅
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Response: 200 OK                                               │
│  {                                                              │
│    "meta": {                                                    │
│      "risk_rate": 0.15,  ◄── SUCCESS! ✅                        │
│      "calculation_id": "calc_597_1734455258",                   │
│      "timestamp": "2025-12-17T17:47:38"                         │
│    },                                                           │
│    "status": "success",                                         │
│    "message": "Risk rate calculated successfully"               │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘

✅ Frontend displays: "Risk Rate (per mille): 0.15" - WORKING!
"""

DATABASE_SCHEMA = """
╔════════════════════════════════════════════════════════════════════╗
║                         DATABASE SCHEMA                            ║
╚════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────┐       ┌──────────────────────────┐
│  occupancies                    │       │  fire_iib_rates          │
├─────────────────────────────────┤       ├──────────────────────────┤
│ id (PK)          INTEGER        │       │ iib_code (PK)  VARCHAR   │
│ iib_code         VARCHAR(20) ───┼───────┼─► rate_per_mille NUMERIC │
│ risk_description TEXT           │       │ created_at     TIMESTAMP │
│ occupancy_type   VARCHAR        │       └──────────────────────────┘
│ section_aift     VARCHAR        │
└─────────────────────────────────┘

EXAMPLE DATA:

occupancies:
┌─────┬──────────┬──────────────────────┐
│ id  │ iib_code │ risk_description     │
├─────┼──────────┼──────────────────────┤
│ 597 │ 1001     │ Dwellings (Standard) │
│ 598 │ 1001_2   │ Dwellings (Premium)  │
│ 599 │ 2001     │ Commercial Building  │
└─────┴──────────┴──────────────────────┘

fire_iib_rates:
┌──────────┬─────────────────┐
│ iib_code │ rate_per_mille  │
├──────────┼─────────────────┤
│ 1001     │ 0.1500          │
│ 1001_2   │ 0.1500          │
│ 2001     │ 0.3500          │
└──────────┴─────────────────┘

KEY INSIGHT:
- Frontend sends occupancyId (597)
- We must resolve to iib_code (1001)
- Then query fire_iib_rates with iib_code
"""

if __name__ == "__main__":
    print(BEFORE_FIX)
    print("\n\n")
    print(AFTER_FIX)
    print("\n\n")
    print(DATABASE_SCHEMA)
