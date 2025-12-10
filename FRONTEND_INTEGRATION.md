# Frontend Integration Guide for iRiskAssist360

This guide provides the necessary code snippets and configuration steps to connect your Flutter/Netlify frontend to the deployed FastAPI backend on Railway.

## 1. Backend Configuration (Railway)

We have updated `app/main.py` to support dynamic CORS origins.

1.  Go to your **Railway Project Dashboard**.
2.  Select the **FastAPI Service**.
3.  Go to **Variables**.
4.  Add a new variable:
    *   **Key**: `ALLOWED_ORIGINS`
    *   **Value**: `https://your-app-name.netlify.app` (Replace with your actual Netlify URL).
    *   *Note: If you want to allow local development as well, you can use: `https://your-app-name.netlify.app,http://localhost:3000`*

## 2. Flutter Frontend setup

Since your workspace currently only shows the backend, copy the following files into your Flutter project (e.g., in `lib/services/`).

### A. Dependencies

Ensure you have `http` installed in your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0  # Check for the latest version
```

### B. Constants (`lib/constants.dart`)

Create a file to store your API URL. Using `const` is efficient.

```dart
// lib/constants.dart

// 1. DEVELOPMENT: Use localhost
// const String BASE_URL = "http://127.0.0.1:8000"; 

// 2. PRODUCTION: Use your Railway URL
const String BASE_URL = "https://YOUR_BACKEND_NAME.up.railway.app";
```

### C. API Service (`lib/services/api_service.dart`)

This service handles GET/POST requests, errors, and timeouts.

```dart
import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../constants.dart';

class ApiService {
  // Common headers
  static const Map<String, String> _headers = {
    "Content-Type": "application/json",
    // "Authorization": "Bearer YOUR_TOKEN_HERE", // Add logic to inject token if needed
  };

  /// Generic GET Request
  static Future<dynamic> get(String endpoint) async {
    final uri = Uri.parse('$BASE_URL/$endpoint');
    try {
      print("GET Request: $uri");
      final response = await http
          .get(uri, headers: _headers)
          .timeout(const Duration(seconds: 10));

      return _processResponse(response);
    } on TimeoutException {
      throw Exception('Connection timed out. Please check your internet.');
    } on Exception catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Generic POST Request
  static Future<dynamic> post(String endpoint, Map<String, dynamic> data) async {
    final uri = Uri.parse('$BASE_URL/$endpoint');
    try {
      print("POST Request: $uri");
      print("Payload: $data");
      
      final response = await http
          .post(uri, headers: _headers, body: jsonEncode(data))
          .timeout(const Duration(seconds: 10));

      return _processResponse(response);
    } on TimeoutException {
      throw Exception('Connection timed out. Please check your internet.');
    } on Exception catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Handle HTTP Responses
  static dynamic _processResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      // Success
      return jsonDecode(response.body);
    } else {
      // Error from server
      print("API Error: ${response.statusCode} - ${response.body}");
      try {
        final errorBody = jsonDecode(response.body);
        throw Exception(errorBody['detail'] ?? 'Unknown error occurred');
      } catch (e) {
        throw Exception('Error ${response.statusCode}: ${response.body}');
      }
    }
  }
}
```

## 3. Usage Example

Here is how you can use the service in your Flutter widgets or controllers.

```dart
// Example: Fetching user profile
void fetchUserProfile() async {
  try {
    final data = await ApiService.get("users/me");
    print("User Data: $data");
  } catch (e) {
    print("Failed to load user: $e");
    // Show Snackbar or Alert Dialog with 'e.toString()'
  }
}

// Example: Login
void login(String email, String password) async {
  try {
    final payload = {
      "email": email,
      "password": password
    };
    final response = await ApiService.post("irisk/auth/login", payload);
    // Remove "irisk/auth/" if your BASE_URL already includes it, or adjust endpoint accordingly
    
    // Save token
    String token = response['access_token'];
    print("Login Successful! Token: $token");
  } catch (e) {
    print("Login Failed: $e");
  }
}
```

## 4. Netlify Environment Variables (Optional but Recommended)

If you are building a Flutter Web app on Netlify, you often bake the variables into the build using `--dart-define`.

1. **In Netlify Build Settings**:
   *   Build command: `flutter build web --dart-define=API_URL=https://your-backend.railway.app`
2. **In Dart Code**:
   ```dart
   const String BASE_URL = String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');
   ```

## 5. Troubleshooting

*   **CORS Errors in Browser Console**:
    *   Check if `ALLOWED_ORIGINS` in Railway matches your Netlify URL exactly (no trailing slash).
    *   Ensure you redeployed the backend after changing the code or variables.
*   **Connection Refused**:
    *   Backend might be sleeping (Railway free tier). Wait a moment.
    *   Check if the URL starts with `https://`.
*   **404 Not Found**:
    *   Check your endpoint path. Does it start with `/`? (The code above handles `BASE_URL/$endpoint` so `endpoint` should behave cleanly).
