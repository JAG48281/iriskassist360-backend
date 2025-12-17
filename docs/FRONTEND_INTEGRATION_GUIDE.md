# Fire Risk Rate API - Frontend Integration Guide

## 🎯 Quick Start

### Endpoint
```
GET /api/fire/risk-rate
```

### When to Call
Call this endpoint **immediately after** the user selects a risk description from the dropdown.

---

## 📋 Step-by-Step Integration

### 1. **Capture Risk Selection**
When user selects a risk description, extract:
- `iibCode` from the selected risk/occupancy
- `aiftSection` from the selected risk/occupancy  
- `productCode` from the current policy form (e.g., "BGRP", "UBGR", "BSUS")

### 2. **Make API Call**
```javascript
const response = await fetch(
  `/api/fire/risk-rate?productCode=${productCode}&iibCode=${iibCode}&aiftSection=${aiftSection}`
);
```

### 3. **Handle Response**

#### Success (200):
```json
{
  "success": true,
  "rate_per_mille": 0.15
}
```

**Action**: Update the read-only "Risk Rate (‰)" field with `rate_per_mille`

#### Error (404 - Rate Not Found):
```json
{
  "detail": {
    "success": false,
    "message": "No rate found for..."
  }
}
```

**Action**: Show error message to user, leave field empty or show "—"

#### Error (400 - Invalid Input):
```json
{
  "detail": {
    "success": false,
    "message": "Invalid product code..."
  }
}
```

**Action**: This should not happen in normal flow. Log error for debugging.

---

## 💻 Code Examples

### Flutter/Dart Example

```dart
Future<double?> fetchRiskRate(String productCode, String iibCode, String aiftSection) async {
  try {
    final url = Uri.parse('$apiBaseUrl/api/fire/risk-rate').replace(queryParameters: {
      'productCode': productCode,
      'iibCode': iibCode,
      'aiftSection': aiftSection,
    });
    
    final response = await http.get(url);
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        return data['rate_per_mille'].toDouble();
      }
    } else if (response.statusCode == 404) {
      // No rate found for this combination
      final error = jsonDecode(response.body);
      print('Rate not found: ${error['detail']['message']}');
      return null;
    } else {
      print('Error: ${response.statusCode}');
      return null;
    }
  } catch (e) {
    print('Exception fetching risk rate: $e');
    return null;
  }
  return null;
}

// Usage in UI
void onRiskSelected(Risk selectedRisk) {
  setState(() {
    _selectedRisk = selectedRisk;
    _isLoadingRate = true;
  });
  
  fetchRiskRate(_productCode, selectedRisk.iibCode, selectedRisk.aiftSection).then((rate) {
    setState(() {
      _riskRate = rate;
      _isLoadingRate = false;
    });
  });
}
```

### JavaScript/React Example

```javascript
async function fetchRiskRate(productCode, iibCode, aiftSection) {
  try {
    const params = new URLSearchParams({
      productCode,
      iibCode,
      aiftSection
    });
    
    const response = await fetch(`/api/fire/risk-rate?${params}`);
    const data = await response.json();
    
    if (response.ok && data.success) {
      return data.rate_per_mille;
    } else if (response.status === 404) {
      console.warn('Rate not found:', data.detail.message);
      return null;
    } else {
      console.error('Error fetching rate:', data);
      return null;
    }
  } catch (error) {
    console.error('Exception:', error);
    return null;
  }
}

// Usage in component
const handleRiskSelection = async (selectedRisk) => {
  setIsLoadingRate(true);
  const rate = await fetchRiskRate(
    productCode,
    selectedRisk.iibCode,
    selectedRisk.aiftSection
  );
  setRiskRate(rate);
  setIsLoadingRate(false);
};
```

---

## 🎨 UI Behavior

### Before Selection
```
Risk Rate (‰): —
```

### During API Call
```
Risk Rate (‰): Loading...
```

### After Success
```
Risk Rate (‰): 0.15
```

### After 404 (No Rate Found)
```
Risk Rate (‰): Not Available
[Show error message: "No rate found for this combination"]
```

---

## ⚠️ Important Notes

### 1. **No Calculation Allowed**
❌ **NEVER** calculate or infer the risk rate on the frontend  
✅ **ALWAYS** use the value from the API

### 2. **Read-Only Field**
The Risk Rate field must be:
- ✅ Read-only (user cannot edit)
- ✅ Auto-populated from API response
- ✅ Cleared when risk selection changes

### 3. **Product Code Mapping**
The API accepts these product codes:
- `UBGR` (auto-normalized to `BGRP`)
- `BGRP`
- `SFSP`
- `IAR`
- `BSUS`
- `BLUS`
- `UVUS`
- `UVGR`

**Note**: If your UI uses `UBGR`, the backend will automatically normalize it to `BGRP`.

### 4. **Error Handling**
Always handle these scenarios:
- ✅ API call succeeds → Display rate
- ✅ Rate not found (404) → Show "Not Available"
- ✅ Network error → Show error message
- ✅ Invalid parameters (400) → Should not happen, log for debugging

---

## 🧪 Test Cases for Frontend

### Test 1: Basic Flow
1. Select risk description
2. Verify API is called with correct parameters
3. Verify rate field is populated

### Test 2: Product Normalization
1. Set product to "UBGR"
2. Select risk
3. Verify rate is returned (UBGR → BGRP conversion)

### Test 3: Error Handling
1. Mock 404 response
2. Verify error message is shown
3. Verify field shows "Not Available" or "—"

### Test 4: Loading State
1. Select risk
2. Verify loading indicator appears
3. Wait for response
4. Verify loading indicator disappears

### Test 5: Risk Change
1. Select first risk → rate populates
2. Select different risk → rate updates
3. Verify old rate is cleared before new rate loads

---

## 📊 Expected Rates (Sample Data)

For testing, here are some known rates:

| Product | IIB Code | Section | Expected Rate |
|---------|----------|---------|---------------|
| BGRP | 1001 | A | 0.15 |
| BGRP | 1002 | A | 0.22 |
| BGRP | 2001 | A | 0.37 |
| SFSP | 3006 | A | 0.52 |
| BSUS | 1002 | Zone I | 0.455 |
| BSUS | 1003 | Zone II | 0.445 |

---

## 🐛 Troubleshooting

### Issue: Getting 404 for valid IIB code
**Possible Causes**:
- IIB code doesn't exist in database
- Product/IIB combination not available
- Wrong section/zone for BSUS products

**Solution**: Verify the IIB code exists in the database for that product type

### Issue: Getting 400 Invalid Product Code
**Possible Causes**:
- Sending unsupported product code
- Typo in product code

**Solution**: Verify product code is one of: UBGR, BGRP, SFSP, IAR, BSUS, BLUS, UVUS, UVGR

### Issue: Getting 422 Missing Parameters
**Possible Causes**:
- Not sending all required parameters
- Parameter name typo

**Solution**: Ensure all three parameters are sent: `productCode`, `iibCode`, `aiftSection`

---

## 📱 API Testing Tools

### Test with cURL
```bash
curl -X GET "http://localhost:8000/api/fire/risk-rate?productCode=BGRP&iibCode=1001&aiftSection=A"
```

### Test with Browser
```
http://localhost:8000/api/fire/risk-rate?productCode=BGRP&iibCode=1001&aiftSection=A
```

### Test with Postman
```
Method: GET
URL: http://localhost:8000/api/fire/risk-rate
Params:
  - productCode: BGRP
  - iibCode: 1001
  - aiftSection: A
```

---

## ✅ Integration Checklist

Before deploying frontend changes:

- [ ] API endpoint is accessible
- [ ] Risk selection triggers API call
- [ ] Loading state is shown during API call
- [ ] Rate field is auto-populated on success
- [ ] Error message shown on 404
- [ ] Field is read-only
- [ ] Rate updates when risk selection changes
- [ ] Old rate is cleared before new rate loads
- [ ] No frontend calculation of rate
- [ ] Error handling tested (network errors, 404, etc.)

---

## 🚀 Go Live Checklist

- [ ] Integration tested in development
- [ ] API endpoint tested in staging
- [ ] All error scenarios handled
- [ ] UI/UX reviewed and approved
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Accessibility tested
- [ ] Cross-browser tested

---

## 📞 Support

If you encounter issues:
1. Check backend logs for errors
2. Verify database has rates for the IIB code
3. Test API endpoint directly with cURL
4. Check API documentation at `/docs`

**Backend Endpoint Documentation**: See `docs/API_FIRE_RISK_RATE.md`

---

**Last Updated**: 2025-12-17  
**API Version**: 1.0.0  
**Status**: ✅ Production Ready
