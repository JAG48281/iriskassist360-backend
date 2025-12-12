# Frontend Integration For iRiskAssist360 Rating Engine

This package contains all necessary files and instructions to connect the frontend UI with the production Rating Engine API.

## A. Installation

1.  **Environment Setup**:
    Copy the contents of `env-example.txt` into your local `.env` file (e.g., `.env.local`).
    ```bash
    VITE_API_BASE_URL=https://web-production-afeec.up.railway.app
    ```

2.  **API Service**:
    Copy `src/services/ratingApi.ts` to your frontend source:
    ```bash
    cp src/services/ratingApi.ts ../iriskassist360_frontend/src/services/
    ```

3.  **Documentation**:
    Copy `guide.md` to your docs folder for team reference:
    ```bash
    cp guide.md ../iriskassist360_frontend/docs/
    ```

## B. Integration Instructions (Per Product)

### 1. Bharat Griha Raksha (BGRP) & UVGS (Home)

*   **Logic**:
    *   **Terrorism**: Auto-select 'Yes' for BGRP. Force 'No' for UVGS.
    *   **Payload**: Pass `paProposer`, `paSpouse`, `terrorismCover`.
    *   **Add-ons**: Not applicable in standard flow (managed via covers).

*   **Implementation**:
    See `guide.md` Section 2.B for the exact payload construction.

### 2. Standard Fire (SFSP, IAR, BLUSP, BSUSP)

*   **Logic**:
    *   **Occupancy**: Pass strict occupancy string (e.g. "Shop", "Warehouse").
    *   **Co-operative Society**: If selected, **disable all add-on checkboxes**.
    *   **Add-ons**: Map selected internal codes to the `add_ons` array:
        ```js
        add_ons: [{ code: 'STFI' }, { code: 'EQ' }] // etc.
        ```
    *   **Rounding**: Backend handles rounding, simply display `gross_premium`.

### 3. Displaying Results

*   **Breakdown**: Use the generic renderer provided in `guide.md` Section 2.C to show all line items returned by the backend.
*   **Total**: Always use `gross_premium` or `total_premium` from the response.

## C. Testing

### Test Payload (BGRP)
```json
{
  "product_code": "BGRP",
  "buildingSI": 2000000,
  "contentsSI": 500000,
  "terrorismCover": "Yes",
  "paProposer": "Yes",
  "discountPercentage": 0
}
```

### Curl Command
```bash
curl -X POST "https://web-production-afeec.up.railway.app/irisk/fire/uiic/bgrp/calculate" \
  -H "Content-Type: application/json" \
  -d '{"buildingSI":2000000, "contentsSI":0, "terrorismCover":"Yes", "discountPercentage":0}'
```

### Expected Response
```json
{
  "success": true,
  "data": {
    "net_premium": 564.0,
    "gst": 101.52,
    "gross_premium": 665.52,
    "breakdown": {
      "firePremium": 375.0,
      "terrorismPremium": 175.0,
      "paPremium": 14.0
    }
  }
}
```
