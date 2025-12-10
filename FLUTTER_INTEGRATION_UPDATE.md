# Flutter Integration Update

**Date:** $(date)

This document contains the standard **Dart** code required to integrate with the new standardized FastAPI backend.

## 1. ApiService (`lib/services/api_service.dart`)
Replace your existing file with this robust version.

```dart
import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
// Ensure you have a constants.dart with: const String BASE_URL = "https://web-production-afeec.up.railway.app";
import '../constants.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  ApiException(this.message, {this.statusCode});
  @override
  String toString() => message;
}

class ApiService {
  static const Map<String, String> _headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  static Future<dynamic> get(String endpoint) async {
    final url = Uri.parse('$BASE_URL/$endpoint');
    print("➡️ GET $url");
    try {
      final response = await http
          .get(url, headers: _headers)
          .timeout(const Duration(seconds: 30));
      print("⬅️ ${response.statusCode}");
      return _processResponse(response);
    } on TimeoutException {
      throw ApiException("Connection timed out");
    } catch (e) {
      throw ApiException("Network Error: $e");
    }
  }

  static Future<dynamic> post(String endpoint, Map<String, dynamic> data) async {
    final url = Uri.parse('$BASE_URL/$endpoint');
    print("➡️ POST $url");
    try {
      final response = await http
          .post(url, headers: _headers, body: jsonEncode(data))
          .timeout(const Duration(seconds: 30));
      print("⬅️ ${response.statusCode}");
      return _processResponse(response);
    } on TimeoutException {
      throw ApiException("Connection timed out");
    } catch (e) {
      throw ApiException("Network Error: $e");
    }
  }

  static dynamic _processResponse(http.Response response) {
    // 1. Decode Body
    final body = jsonDecode(response.body);

    // 2. Check Standard "success" key
    if (body is Map<String, dynamic>) {
      if (body['success'] == true) {
        // Return the inner 'data'
        return body['data'];
      } else {
        // Backend returned success: false
        throw ApiException(body['message'] ?? "Unknown Error", statusCode: response.statusCode);
      }
    }
    
    // Fallback if schema doesn't match
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    } else {
      throw ApiException("Request failed with ${response.statusCode}", statusCode: response.statusCode);
    }
  }
}
```

## 2. Feature Services

### A. AuthService (`lib/services/auth_service.dart`)
```dart
import 'api_service.dart';

class AuthService {
  static Future<void> sendOtp(String mobile) async {
    await ApiService.post('irisk/auth/send-otp', {"mobile": mobile});
  }

  static Future<Map<String, dynamic>> verifyOtp(String mobile, String otp) async {
    return await ApiService.post('irisk/auth/verify-otp', {"mobile": mobile, "otp": otp});
  }
}
```

### B. PremiumCalculationService (`lib/services/premium_calculation_service.dart`)
```dart
import 'api_service.dart';

class PremiumCalculationService {
  // UVGS
  static Future<Map<String, dynamic>> calculateUvgs(Map<String, dynamic> payload) async {
    return await ApiService.post('api/premium/uvgs/calculate', payload);
  }
  
  // Fire Policies (VUSP, BSUSP, etc.)
  static Future<Map<String, dynamic>> calculateFire(String product, Map<String, dynamic> payload) async {
    // product should be one of: vusp, bsusp, blusp, bgrp, sfsp, iar
    return await ApiService.post('irisk/fire/uiic/$product/calculate', payload);
  }
  
  // PDF
  static Future<Map<String, dynamic>> generatePdf(Map<String, dynamic> payload) async {
    return await ApiService.post('irisk/fire/uiic/calculate/pdf', payload);
  }
}
```

### C. RatesService (`lib/services/rates_service.dart`)
```dart
import 'api_service.dart';

class RatesService {
  static Future<List<dynamic>> getUbgrRates() async {
    try {
      final data = await ApiService.get('api/rates/ubgr');
      return data as List<dynamic>;
    } catch (e) {
      print("Rates Fallback Warning: $e");
      return []; // Return empty list instead of crashing UI
    }
  }

  static Future<List<dynamic>> getUvgsRates() async {
    try {
      final data = await ApiService.get('api/rates/uvgs');
      return data as List<dynamic>;
    } catch (e) {
      return [];
    }
  }
}
```

## 3. Integration Tests to Run
Run these checks in your running Flutter App.

1.  **Auth**: Send OTP to valid mobile `1234567890`. Verify console prints `➡️ POST .../send-otp`.
2.  **Fire Calc**: Go to VUSP Calculator, enter `5000` SI. Verify result is shown.
3.  **Rates**: Open Rate Viewer. Verify data loads or at least empty table (no crash).
