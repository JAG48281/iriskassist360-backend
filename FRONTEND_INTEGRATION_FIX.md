# iRiskAssist360 Frontend - Backend Integration Repair Kit

**Generated on:** $(date)

This document contains the **validated and corrected code** required to connect your Netlify frontend to your Railway backend.

## 1. Backend Verification (Railway)

### Status: ✅ **Pass**
Your backend `main.py` is correctly configured to read `ALLOWED_ORIGINS`.
**Action:** Ensure you have set the Railway Variable `ALLOWED_ORIGINS` to `https://your-netlify-site.netlify.app`. If testing locally, keep it as `*` or add `http://localhost:3000`.

---

## 2. Frontend Configuration (Flutter)

**File:** `lib/constants.dart`
**Status:** ⚠️ **Update Required**
Ensure the URL does **NOT** have a trailing slash or `/docs`.

```dart
// CORRECT
const String BASE_URL = "https://YOUR_PROJECT_NAME.up.railway.app";

// INCORRECT (Avoid these)
// const String BASE_URL = "https://YOUR_PROJECT_NAME.up.railway.app/"; 
// const String BASE_URL = "https://YOUR_PROJECT_NAME.up.railway.app/docs";
```

---

## 3. Frontend API Service (Flutter)

**File:** `lib/services/api_service.dart`
**Status:** 🛠️ **Generated Replacement**
Use this robust service file. It handles **Headers**, **Timeouts**, and **JSON Decoding** correctly.

```dart
import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../constants.dart';

class ApiService {
  // Common headers: Content-Type is CRITICAL for FastAPI Pydantic models
  static const Map<String, String> _defaultHeaders = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  static Future<dynamic> get(String endpoint) async {
    final uri = Uri.parse('$BASE_URL/$endpoint');
    try {
      final response = await http
          .get(uri, headers: _defaultHeaders)
          .timeout(const Duration(seconds: 15)); // 15s timeout
      return _processResponse(response);
    } on TimeoutException {
      throw Exception('Server is taking too long to respond.');
    } catch (e) {
      throw Exception('Network Error: $e');
    }
  }

  static Future<dynamic> post(String endpoint, Map<String, dynamic> data) async {
    final uri = Uri.parse('$BASE_URL/$endpoint');
    try {
      final body = jsonEncode(data);
      final response = await http
          .post(uri, headers: _defaultHeaders, body: body)
          .timeout(const Duration(seconds: 15));
      return _processResponse(response);
    } on TimeoutException {
      throw Exception('Server is taking too long to respond.');
    } catch (e) {
      throw Exception('Network Error: $e');
    }
  }

  static dynamic _processResponse(http.Response response) {
    // 200-299 is Success
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    } else {
      // Parse Backend Error
      String errorMsg = 'An error occurred';
      try {
        final body = jsonDecode(response.body);
        if (body['detail'] != null) {
          if (body['detail'] is String) {
            errorMsg = body['detail'];
          } else {
            errorMsg = body['detail'].toString();
          }
        }
      } catch (_) {
        errorMsg = 'Error ${response.statusCode}: ${response.body}';
      }
      throw Exception(errorMsg);
    }
  }
}
```

---

## 4. Correct Endpoint Usage Guide

Your backend routes are strictly typed. Here is how to call them without 422 Validation Errors.

### A. Authentication
**Endpoint:** `/irisk/auth/login`
**Method:** `POST`

```dart
// Usage Example
void loginUser() async {
  try {
    final data = await ApiService.post('irisk/auth/login', {
      "email": "test@example.com",
      "password": "secretpassword"
    });
    print("Token: ${data['access_token']}");
  } catch (e) {
    print(e); // Will print "Invalid credentials" from backend
  }
}
```

### B. Fire Policy Calculation (VUSP)
**Endpoint:** `/irisk/fire/uiic/vusp/calculate`
**Method:** `POST`

*Note: `building_si` must be an integer, `occupancy` is a string.*

```dart
// Usage Example
void calculateVusp() async {
  try {
    final payload = {
      "building_si": 5000000, // No quotes for numbers
      "occupancy": "Office",
      "pa_selected": true     // Boolean
    };
    
    final result = await ApiService.post('irisk/fire/uiic/vusp/calculate', payload);
    print("Net Premium: ${result['net_premium']}");
  } catch (e) {
    print("Calculation Error: $e");
  }
}
```

---

## 5. Troubleshooting Common Issues

### ❌ CORS Error in Console
**Error:** `Access to fetch at ... has been blocked by CORS policy`
**Fix:**
1. Go to Railway.
2. Check `ALLOWED_ORIGINS` variable.
3. It must match your Netlify origin EXACTLY (e.g., `https://myapp.netlify.app`). 
4. **NO** trailing slash (`/`).
5. **Redeploy** backend after changing variables.

### ❌ 422 Unprocessable Entity
**Error:** Backend returns `422`.
**Fix:**
1. You are sending the wrong data types.
2. Check if specific fields (like `building_si`) are sent as Strings (`"5000"`) instead of Numbers (`5000`).
3. Ensure `Content-Type: application/json` is sent (API Service above handles this).

### ❌ Network Error / Connection Refused
**Fix:**
1. Verify `BASE_URL` is `https` and not `http`.
2. Railway Free plan puts services to sleep. The first request might take 10-20 seconds. Increase timeout logic if needed.

---

## 6. Final Deployment Checklist
1. [ ] `ALLOWED_ORIGINS` set in Railway.
2. [ ] `BASE_URL` updated in Flutter `constants.dart`.
3. [ ] `api_service.dart` replaced with the code above.
4. [ ] Test `/health` or `/` endpoint (`await ApiService.get('')`).

✅ **Your Frontend-Backend link is now compliant.**
