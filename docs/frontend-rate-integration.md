# Frontend Rating Integration Guide

This document outlines the API endpoints and integration patterns for the Insurance Rating Engine.

## Overview

The backend exposes two types of rating endpoints:
1.  **Product-Specific Endpoints**: Tailored for specific UIIC products (Fire, etc.) with internal rate lookups.
2.  **Generic Rating Engine**: A primitive calculator that accepts raw rates and loadings/discounts (use for custom logic).

---

## 1. Product-Specific Endpoints (Fire)

These endpoints handle rate lookup based on occupancy and product logic.

### **Base URL**: `/irisk/fire/uiic`

### **Common Response Format**

All endpoints return a standardized `ResponseModel` structure:

```json
{
  "success": true,
  "message": "Premium Calculated",
  "data": {
    "brand": "iRiskAssist360",
    "product": "Product Name",
    "rate_applied": 0.15,
    "building_si": 1000000,
    "basic_premium": 150.0,
    "terrorism_premium": 70.0,
    "pa_premium": 0,
    "net_premium": 220.0,
    "gst": 39.6,
    "gross_premium": 259.6,
    "breakdown": { ... } // (Optional extra details)
  }
}
```

---

### **A. Bharat Griha Raksha (BGRP)**

*Use for Home Insurance.*

*   **Endpoint:** `POST /bgrp/calculate`
*   **Field Mapping:**

| UI Field | API Field | Type | Notes |
|---|---|---|---|
| Building Sum Insured | `buildingSI` | Float | **CamelCase** |
| Contents Sum Insured | `contentsSI` | Float | **CamelCase** |
| Terrorism Cover? | `terrorismCover` | String | "Yes" or "No" |
| Proposer PA Cover? | `paProposer` | String | "Yes" or "No" |
| Spouse PA Cover? | `paSpouse` | String | "Yes" or "No" |
| Discount % | `discountPercentage` | Float | 0 to 100 |

*   **Example Body:**

```json
{
  "buildingSI": 2000000,
  "contentsSI": 500000,
  "terrorismCover": "Yes",
  "paProposer": "Yes",
  "paSpouse": "No",
  "discountPercentage": 10
}
```

### **B. Standard Fire (SFSP, IAR, BLUSP, BSUSP, VUSP)**

*Use for Commercial/Industrial Insurance.*

*   **Endpoints:**
    *   `/sfsp/calculate`
    *   `/iar/calculate`
    *   `/blusp/calculate`
    *   `/bsusp/calculate`
    *   `/vusp/calculate`

*   **Field Mapping:**

| UI Field | API Field | Type | Notes |
|---|---|---|---|
| Building Sum Insured | `building_si` | Integer | **snake_case** |
| Occupancy (Dropdown) | `occupancy` | String | e.g. "Warehouse", "Shop" |
| PA Selected? | `pa_selected` | Boolean | `true` or `false` |

*   **Example Body (SFSP):**

```json
{
  "building_si": 1000000,
  "occupancy": "Warehouse",
  "pa_selected": false
}
```

---

## 2. Generic Rating Engine

*Use for manual calculations or debugging where rate is known.*

*   **Endpoint:** `POST /api/rating/calculate`
*   **Payload:**

```json
{
  "product_name": "Test Product",
  "sum_insured": 100000,
  "rate": 1.5,
  "discounts_pct": [10, 5], 
  "loadings_pct": []
}
```
*   **Note**: Rate is per-mille (e.g. 1.5 = 1.5/1000).

---

## Rendering & Rules

### **Add-on Breakdown**
Currently, add-on specific logic is implicitly handled in product endpoints (e.g., Terrorism in BGR). For generic add-on rendering, inspection `data.breakdown` object if available.

### **Rounding Rules**
*   All currency values (Premiums, GST) are rounded to **2 decimal places**.
*   Rounding Method: `ROUND_HALF_UP` (standard financial rounding).

### **Gross Premium Display**
Display `data.gross_premium` as the "Total Payable".
Ensure you display `data.gst` separately as "GST (18%)".

---

## Manual Testing (Curl)

```bash
# Test BGRP (Home)
curl -X POST "https://your-app.railway.app/irisk/fire/uiic/bgrp/calculate" \
  -H "Content-Type: application/json" \
  -d '{"buildingSI": 1000000, "contentsSI": 0, "terrorismCover": "Yes", "discountPercentage": 0}'

# Test SFSP (Commercial)
curl -X POST "https://your-app.railway.app/irisk/fire/uiic/sfsp/calculate" \
  -H "Content-Type: application/json" \
  -d '{"building_si": 1000000, "occupancy": "Warehouse", "pa_selected": false}'
```
