# Frontend Integration Guide: Rating Engine

This guide provides the necessary code snippets and logic to integrate your frontend UI (React/Vite) with the newly deployed backend rating engine.

## 1. Setup

### A. Environment Variable
Ensure your frontend project (`.env.local` or similar) has the backend URL:
```bash
VITE_API_BASE_URL=http://localhost:8000
# For Production:
# VITE_API_BASE_URL=https://your-railway-app.app
```

### B. Add API Service
Copy `src/services/ratingApi.ts` from this folder into your frontend `src/services/` directory.

---

## 2. Integration Logic (Premium Calculation Screens)

Apply the following changes to your **Product UI Components** (e.g., `BgrpScreen.tsx`, `SfspScreen.tsx`).

### A. Validation & Co-op Rules
Before calling the API, ensure rules are respected.

```typescript
// Example State
const [occupancy, setOccupancy] = useState<string>('');
const [addons, setAddons] = useState<string[]>([]);

// Rule: Disable Add-ons for Co-operative Society
useEffect(() => {
  if (occupancy === 'Co-operative society') {
    // Clear and Disable
    setAddons([]); 
  }
}, [occupancy]);

// ... In your render ...
<AddOnCheckbox 
  disabled={occupancy === 'Co-operative society'} 
  checked={addons.includes('Earthquake')}
  ... 
/>
```

### B. Calling the API
Use the exported `calculatePremium` function inside your "Calculate" button handler.

```typescript
import { calculatePremium, RatingResponse } from '../../services/ratingApi';
import { useState } from 'react';

// ... inside Component ...

const [isLoading, setIsLoading] = useState(false);
const [result, setResult] = useState<RatingResponse | null>(null);
const [error, setError] = useState<string | null>(null);

const handleCalculate = async () => {
  // 1. Validation
  if (buildingSI < 0 || contentsSI < 0) {
    setError("Sum Insured cannot be negative.");
    return;
  }
  
  setError(null);
  setIsLoading(true);

  try {
    // 2. Construct Payload
    // Note: STFI/EQ logic is usually implicit in backend for standard products, 
    // but explicit toggles can be passed if your UI has them.
    // For BGRP, 'terrorism' is a specific toggle.
    
    // Auto-calculate Terrorism SI (usually Total SI) if needed, 
    // but backend handles rate application on provided SI.
    
    const payload = {
      product_code: 'BGRP', // or from props
      buildingSI: Number(buildingSI),
      contentsSI: Number(contentsSI),
      
      // BGRP Specifics
      terrorismCover: terrorismSelected ? 'Yes' : 'No', // "Yes" | "No" standard
      paProposer: paSelf ? 'Yes' : 'No',
      paSpouse: paSpouse ? 'Yes' : 'No',
      
      // Generic / Commercial Fields
      occupancy: occupancy, // e.g. "Warehouse"
      policy_period_years: tenure, // 1, 5, 10
      
      discountPercentage: Number(discount),
      
      // Addons (for generic engine, specific products might ignore this array and look at explicit fields)
      add_ons: addons.map(code => ({ code })),
    };

    // 3. Call API
    const response = await calculatePremium(payload);
    setResult(response);
    
  } catch (err: any) {
    console.error("Rating Error", err);
    // Show backend specific message if available
    const msg = err.detail || err.message || "Calculation failed";
    setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
  } finally {
    setIsLoading(false);
  }
};
```

### C. Displaying Results (The Breakdown)

Render the response data. Note the field names might vary slightly between generic/specific endpoints, but `ratingApi.ts` types cover them.

```tsx
{result && result.data && (
  <div className="premium-summary p-4 border rounded bg-gray-50 mt-4">
    <h3 className="font-bold text-lg mb-2">Premium Breakdown</h3>
    
    <div className="flex justify-between">
      <span>Base Premium (Fire/Structure):</span>
      <span>₹{result.data.breakdown?.firePremium || result.data.breakdown?.base || 0}</span>
    </div>

    {/* Terrorism - Conditional Rendering */}
    {(result.data.breakdown?.terrorismPremium || 0) > 0 && (
       <div className="flex justify-between">
         <span>Terrorism Premium:</span>
         <span>₹{result.data.breakdown?.terrorismPremium}</span>
       </div>
    )}
    
    {/* Generic Add-ons Breakdown */}
    {/* If generic engine returns specific add-on lines in breakdown */}
    {Object.entries(result.data.breakdown || {}).map(([key, val]) => {
        if(['firePremium', 'base', 'terrorismPremium', 'gst', 'loadings', 'discounts'].includes(key)) return null;
        return (
          <div key={key} className="flex justify-between text-sm text-gray-600">
             <span className="capitalize">{key.replace('_', ' ')}:</span>
             <span>₹{val}</span>
          </div>
        )
    })}

    <div className="divider my-2 border-t"></div>

    <div className="flex justify-between font-semibold">
      <span>Net Premium:</span>
      <span>₹{result.data.netPremium || result.data.net_premium}</span>
    </div>
    
    <div className="flex justify-between text-sm">
      <span>GST (18%):</span>
      <span>₹{result.data.gst || 0}</span>
    </div>

    <div className="divider my-2 border-t"></div>

    <div className="flex justify-between font-bold text-xl text-primary">
      <span>Total Payable:</span>
      <span>₹{result.data.gross_premium || result.data.total_premium}</span>
    </div>
  </div>
)}
```

---

## 3. Specific Business Rules to Implement in UI

1.  **Terrorism & UVGS**:
    *   If Product is **UVGS**, hide the Terrorism toggle or force it to `false`.
    *   If Product is **BGRP**, default Terrorism to `true` (User can toggle).
    
2.  **Co-operative Society**:
    *   If `occupancy === 'Co-operative society'`, ensure `addons` list is empty before sending.

3.  **Loading/Discount**:
    *   Send as straightforward Percentage (0-100).
