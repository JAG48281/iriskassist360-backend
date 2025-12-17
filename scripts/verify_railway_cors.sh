#!/bin/bash
# Railway Deployment Verification Script
# Run this AFTER Railway deployment completes

echo "=================================================="
echo "Railway CORS Fix - Deployment Verification"
echo "=================================================="
echo ""

# Configuration
RAILWAY_URL="https://web-production-afeec.up.railway.app"
ENDPOINT="/api/master/risk-descriptions"
ORIGIN="http://localhost:57328"

echo "🔍 Testing CORS configuration..."
echo ""

# Test 1: OPTIONS Preflight
echo "1️⃣ Testing OPTIONS preflight..."
echo "   URL: ${RAILWAY_URL}${ENDPOINT}"
echo "   Origin: ${ORIGIN}"
echo ""

OPTIONS_RESPONSE=$(curl -X OPTIONS \
  "${RAILWAY_URL}${ENDPOINT}" \
  -H "Origin: ${ORIGIN}" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: content-type" \
  -i -s)

echo "$OPTIONS_RESPONSE"
echo ""

# Check for 200 OK
if echo "$OPTIONS_RESPONSE" | grep -q "HTTP.*200"; then
    echo "✅ OPTIONS returned 200 OK"
else
    echo "❌ FAIL: OPTIONS did not return 200"
    echo "   Check Railway logs for errors"
    exit 1
fi

# Check for CORS headers
if echo "$OPTIONS_RESPONSE" | grep -qi "access-control-allow-origin"; then
    echo "✅ CORS headers present"
else
    echo "❌ FAIL: CORS headers missing"
    exit 1
fi

echo ""
echo "=================================================="
echo ""

# Test 2: GET Request
echo "2️⃣ Testing GET request..."
echo "   URL: ${RAILWAY_URL}${ENDPOINT}?productCode=BGRP"
echo ""

GET_RESPONSE=$(curl -X GET \
  "${RAILWAY_URL}${ENDPOINT}?productCode=BGRP" \
  -H "Origin: ${ORIGIN}" \
  -i -s)

echo "$GET_RESPONSE"
echo ""

# Check for 200 OK
if echo "$GET_RESPONSE" | grep -q "HTTP.*200"; then
    echo "✅ GET returned 200 OK"
else
    echo "❌ FAIL: GET did not return 200"
    exit 1
fi

# Check for JSON data
if echo "$GET_RESPONSE" | grep -q '"success".*true'; then
    echo "✅ Response contains valid JSON"
else
    echo "❌ FAIL: Invalid response format"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ ALL TESTS PASSED"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Test in browser (Chrome DevTools → Network)"
echo "2. Verify Flutter Web dropdown loads"
echo "3. Check console for NO CORS errors"
echo ""
