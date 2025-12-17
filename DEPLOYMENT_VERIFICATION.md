# Railway CORS Fix - Deployment & Verification Guide

## 🎯 Current Status

✅ Code committed and pushed to GitHub (commit: `cb5142f`)  
✅ STRICT CORS configuration implemented  
✅ All tests passing locally (17/17)  
⏳ **Waiting for Railway deployment**

---

## 📋 Step-by-Step Deployment

### Step 1: Trigger Railway Deployment

Railway auto-deploys when you push to main, but you can force a redeploy:

#### Option A: Railway Dashboard (Recommended)
1. Go to: https://railway.app/dashboard
2. Select your project: `iriskassist360-backend`
3. Click on the service/deployment
4. Click **"Deploy"** → **"Redeploy"**
5. Wait for deployment to complete (watch the logs)

#### Option B: Railway CLI
```bash
railway restart
```

#### Option C: Git Force Push
```bash
git commit --allow-empty -m "deploy: force Railway redeploy"
git push origin main
```

### Step 2: Monitor Deployment

Watch Railway logs in real-time:
```bash
railway logs --follow
```

**Look for**:
```
✅ Startup Check: BGRP Terrorism Rate verified as 0.07
✅ CORS middleware configured
🔄 OPTIONS preflight for: /api/master/risk-descriptions
```

**Wait for**:
```
INFO: Application startup complete
```

---

## ✅ Verification Steps (After Deployment)

### Step 1: Automated Verification Script

Run the verification script:
```bash
bash scripts/verify_railway_cors.sh
```

This will test:
- ✅ OPTIONS request returns 200 OK
- ✅ CORS headers present
- ✅ GET request returns data
- ✅ Response format is valid JSON

**Expected Output**:
```
✅ OPTIONS returned 200 OK
✅ CORS headers present
✅ GET returned 200 OK
✅ Response contains valid JSON
✅ ALL TESTS PASSED
```

### Step 2: Manual cURL Tests

#### Test OPTIONS Preflight:
```bash
curl -X OPTIONS \
  https://web-production-afeec.up.railway.app/api/master/risk-descriptions \
  -H "Origin: http://localhost:57328" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Expected Response Headers**:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:57328
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: *
Access-Control-Max-Age: 86400
```

**🚫 NOT Expected**:
- `502 Bad Gateway`
- `405 Method Not Allowed`
- `Access-Control-Allow-Credentials: true` (we removed this)

#### Test GET Request:
```bash
curl -X GET \
  "https://web-production-afeec.up.railway.app/api/master/risk-descriptions?productCode=BGRP" \
  -H "Origin: http://localhost:57328"
```

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "description": "Dwellings",
      "occupancy_type": "Residential",
      "aift_section": "III",
      "iib_code": "1001"
    }
  ]
}
```

### Step 3: Browser Verification (FINAL)

**Chrome DevTools**:
1. Open Flutter Web app: http://localhost:57328 (or your port)
2. Press F12 to open DevTools
3. Go to **Network** tab
4. Click "Preserve log"
5. Navigate to Fire LOB form

**Expected Network Sequence**:
```
Name                           Method   Status   Size
/api/master/risk-descriptions  OPTIONS  200 OK   0 B
/api/master/risk-descriptions  GET      200 OK   ~5 KB
```

**Click on OPTIONS request**:
- **Headers** tab:
  - Request URL: `https://web-production-afeec.up.railway.app/api/master/risk-descriptions`
  - Request Method: `OPTIONS`
  - Status Code: `200 OK`
  
- **Response Headers**:
  - `access-control-allow-origin: http://localhost:57328`
  - `access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH`
  - `access-control-allow-headers: *`

**Click on GET request**:
- **Preview** tab: Should show JSON data structure
- **Response** tab: Should show `{"success": true, "data": [...]}`

**Console Tab**:
- ✅ NO red errors
- ✅ NO "CORS policy" errors
- ✅ NO "Failed to fetch" errors

**UI Behavior**:
- ✅ Risk description dropdown populates immediately
- ✅ Loading spinner appears and disappears quickly
- ✅ Dropdown shows list of risk descriptions
- ✅ Selecting a risk auto-fills:
  - IIB Code
  - Occupancy Type
  - AIFT Section
- ✅ No retry button needed
- ✅ No error messages

---

## 🐛 Troubleshooting

### Issue: OPTIONS still returns 502

**Possible Causes**:
1. Railway hasn't deployed yet
2. Old container still running
3. Deployment failed

**Solutions**:
```bash
# Check deployment status
railway status

# Check logs for errors
railway logs

# Force restart
railway restart
```

### Issue: OPTIONS returns 404

**Possible Cause**: Route not registered

**Solution**: Verify in Railway logs:
```
🔄 OPTIONS preflight for: /api/master/risk-descriptions
```

If not found, check router registration in `app/main.py`

### Issue: CORS headers missing

**Possible Cause**: CORS middleware not applied

**Solution**: Check Railway logs for:
```
✅ CORS middleware configured
```

### Issue: Still getting CORS errors in browser

**Possible Causes**:
1. Browser cached old response
2. Wrong origin (check port number)
3. Railway not deployed

**Solutions**:
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Use Incognito/Private mode
4. Verify origin matches: `http://localhost:57328`

---

## 📊 Deployment Checklist

Before marking as complete, verify ALL of these:

### Railway Deployment
- [ ] Code pushed to GitHub
- [ ] Railway deployment triggered
- [ ] Deployment completed successfully
- [ ] New container started
- [ ] Logs show "Application startup complete"

### Backend Verification
- [ ] OPTIONS request returns 200 OK
- [ ] GET request returns valid JSON
- [ ] CORS headers present in response
- [ ] No 502 or 405 errors

### Browser Verification
- [ ] Network tab shows OPTIONS → 200
- [ ] Network tab shows GET → 200
- [ ] Console has NO CORS errors
- [ ] Console has NO "Failed to fetch" errors

### UI Verification
- [ ] Risk dropdown loads immediately
- [ ] Dropdown shows risk descriptions
- [ ] Selecting risk auto-fills fields
- [ ] No retry button needed
- [ ] Works on first try

### Cross-Platform
- [ ] Works on Chrome
- [ ] Works on Firefox
- [ ] Works on Flutter Web
- [ ] Works on mobile browser

---

## 🎉 Success Criteria

**Task is COMPLETE when**:

1. ✅ Railway deployment successful
2. ✅ cURL verification passes
3. ✅ Browser shows NO CORS errors
4. ✅ Risk dropdown works in Flutter Web
5. ✅ All checklist items verified

---

## 📝 Quick Reference

### Railway URLs
- **Production**: https://web-production-afeec.up.railway.app
- **Endpoint**: /api/master/risk-descriptions
- **Full URL**: https://web-production-afeec.up.railway.app/api/master/risk-descriptions

### Allowed Origins
- `http://localhost:57328` (Flutter Web)
- `http://localhost:50000` (Flutter Web default)
- `http://localhost:8000` (Backend dev)
- `http://localhost` (Generic)
- `https://web-production-afeec.up.railway.app` (Production)

### Test Commands
```bash
# Verify deployment
railway logs

# Test OPTIONS
bash scripts/verify_railway_cors.sh

# Manual cURL test
curl -X OPTIONS https://web-production-afeec.up.railway.app/api/master/risk-descriptions -H "Origin: http://localhost:57328" -v
```

---

## 🚀 Next Action

**You are here**: Code pushed, waiting for Railway deployment

**Next step**: 
1. Go to Railway dashboard
2. Click "Redeploy" or wait for auto-deploy
3. Run verification script after deployment
4. Test in browser

---

**Status**: ⏳ **Awaiting Railway Deployment**  
**When Complete**: ✅ **Flutter Web CORS Fixed Permanently**
