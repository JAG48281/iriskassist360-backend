# CRITICAL FIX: Stop Crash Loop & Remove Legacy Tables

## 🔒 PROBLEM CONFIRMED

**Current State**:
- ✅ Cleanup migration exists: `6c9h0g1f3e4d_drop_legacy_duplicate_tables_final_cleanup.py`
- ✅ Seed check is correct and strict
- ❌ **Procfile was running migrations/seed in web process** (causes crash loop)
- ❌ Legacy tables still exist in production database
- ❌ Seed fails → Railway crashes → infinite restart loop

---

## ✅ FIX 1: PROCFILE FIXED (CRITICAL)

### Before (BROKEN):
```
web: alembic upgrade head && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Problem**: If seed fails, the web process crashes, Railway restarts, seed fails again → crash loop

### After (FIXED):
```
release: alembic upgrade head && python seed.py
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Solution**: 
- ✅ `release` phase runs ONCE before web process
- ✅ If migrations/seed fail, Railway shows error but doesn't restart
- ✅ Web process only starts after successful release
- ✅ **Prevents crash loops**

---

## ✅ FIX 2: MIGRATION ALREADY EXISTS

**File**: `alembic/versions/6c9h0g1f3e4d_drop_legacy_duplicate_tables_final_cleanup.py`

**Drops These Tables** (9 total):
```python
def upgrade():
    legacy_tables = [
        "product_basic_rates",  # → fire_iib_rates
        "add_on_products",      # → fire_add_on_rates
        "add_on_rates",         # → fire_add_on_rates
        "add_on_master",        # → fire_add_on_master
        "stfi_rates",           # → fire_stfi_rates
        "bsus_rates",           # → fire_bsus_rates
        "eq_rates",             # → fire_eq_rates
        "generic_rates",        # Never used
        "product_master",       # FORBIDDEN
    ]
    
    for table in legacy_tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
```

**Status**: ✅ Already created, will be applied on next deploy

---

## ✅ FIX 3: SEED CHECK ALREADY CORRECT

**File**: `seed.py` - `check_no_product_master()`

**Current Implementation** (CORRECT):
```python
def check_no_product_master():
    """Uses to_regclass for explicit existence check."""
    try:
        with engine.connect() as conn:
            # Use to_regclass for explicit check
            result = conn.execute(text("SELECT to_regclass('public.product_master')"))
            exists = result.scalar() is not None
            
            if exists:
                # Table exists - this is FORBIDDEN
                logger.critical(f"❌ FATAL: {FORBIDDEN_TABLE} table exists!")
                logger.critical(f"❌ Products are LOGICAL, not relational.")
                raise RuntimeError(f"{FORBIDDEN_TABLE} schema violation")
            else:
                # Table correctly does not exist
                logger.info(f"✅ Confirmed: No {FORBIDDEN_TABLE} table (correct)")
                
    except RuntimeError:
        raise  # Re-raise schema violations
    except Exception as e:
        logger.error(f"Could not verify {FORBIDDEN_TABLE} absence: {e}")
        raise
```

**Features**:
- ✅ Uses `to_regclass` for explicit check
- ✅ Logs CRITICAL only if table truly exists
- ✅ Raises exception to stop seed
- ✅ No false positives

**Status**: ✅ No changes needed

---

## ✅ FIX 4: NO MISLEADING LOGS

**Status**: ✅ Already fixed in recent commit

**Before**: Could log INFO before check completed  
**After**: Logs INFO only after successful check

---

## ✅ FIX 5: VERIFICATION READY

**Script**: `scripts/verify_schema_cleanup.py`

**Usage** (after deployment):
```bash
python scripts/verify_schema_cleanup.py
```

**Will verify**:
- ✅ All 10 required tables present
- ✅ All 9 forbidden tables removed
- ✅ Clean canonical schema

---

## 🚀 DEPLOYMENT SEQUENCE

### Step 1: Push Changes
```bash
git add Procfile
git commit -m "fix: Use release phase for migrations to prevent crash loops"
git push origin main
```

### Step 2: Railway Auto-Deploy

**Release Phase** (runs ONCE):
```bash
alembic upgrade head && python seed.py
```

**Expected Output**:
```
INFO  [alembic] Running upgrade 5b8g9f0e2d3c -> 6c9h0g1f3e4d
INFO  [alembic] Running upgrade 6c9h0g1f3e4d -> 7d0i1h2g4f5e

❌ CRITICAL: Dropping FORBIDDEN table product_master
✅ Dropped product_master
✅ Dropped product_basic_rates
✅ Dropped generic_rates
...

LEGACY TABLE CLEANUP COMPLETE

Seeding...
✅ Confirmed: No product_master table (correct)
✅ LOB Master: 1 success, 0 failed
...
✅ All rows seeded successfully!
```

**Web Phase** (starts AFTER release succeeds):
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## 🚦 ACCEPTANCE CRITERIA

### During Deployment:
- [ ] Railway shows "release" phase in logs
- [ ] Alembic logs: `Running upgrade -> 6c9h0g1f3e4d`
- [ ] Migration output: `Dropped product_master`
- [ ] Seed logs: `✅ Confirmed: No product_master table (correct)`
- [ ] Seed completes: `✅ All rows seeded successfully!`
- [ ] Web starts: `Application startup complete`

### After Deployment:
- [ ] Container is RUNNING (not restarting)
- [ ] No crash loops
- [ ] `/health/db` returns 200 OK
- [ ] No `product_master` in Railway database browser

### Verify in Railway DB:
```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Must NOT appear**:
- ❌ product_master
- ❌ product_basic_rates
- ❌ generic_rates
- ❌ add_on_master
- ❌ add_on_products
- ❌ add_on_rates
- ❌ stfi_rates
- ❌ bsus_rates
- ❌ eq_rates

**Must appear**:
- ✅ lob_master
- ✅ occupancies
- ✅ fire_iib_rates
- ✅ fire_bsus_rates
- ✅ fire_stfi_rates
- ✅ fire_eq_rates
- ✅ terrorism_slabs
- ✅ fire_add_on_master
- ✅ fire_add_on_rates
- ✅ alembic_version

---

## 🔥 WHY THE CRASH LOOP HAPPENED

### Previous Setup (BROKEN):
```
web: alembic upgrade head && python seed.py && uvicorn app.main:app
```

**Sequence**:
1. Railway starts web process
2. Migrations run → succeed
3. Seed runs → **FAILS** (product_master exists)
4. Web process crashes
5. Railway restarts web process
6. Repeat step 1 → **INFINITE LOOP**

### New Setup (FIXED):
```
release: alembic upgrade head && python seed.py
web: uvicorn app.main:app
```

**Sequence**:
1. Railway runs release phase
2. Migrations run → **DROP product_master**
3. Seed runs → **SUCCEEDS** (no product_master)
4. Web process starts → **STAYS RUNNING**
5. **NO CRASH LOOP**

---

## 🎯 KEY DIFFERENCES

| Aspect | Before (web phase) | After (release phase) |
|--------|-------------------|----------------------|
| Migrations run | Every container restart | Once per deployment |
| Seed runs | Every container restart | Once per deployment |
| If seed fails | Crash loop | Build fails, no deploy |
| Recovery | Manual intervention | Automatic on next push |
| Visibility | Buried in crash logs | Clear in release logs |

---

## 📊 MIGRATION CHAIN

**Current HEAD**: `7d0i1h2g4f5e`

**Chain**:
```
5b8g9f0e2d3c (previous cleanup)
    ↓
6c9h0g1f3e4d (DROP ALL LEGACY TABLES) ← CRITICAL
    ↓
7d0i1h2g4f5e (align fire_stfi_rates)
```

**Status**: All migrations will run automatically

---

## 🧠 ARCHITECTURAL PRINCIPLE

✅ **Products are LOGICAL, not relational**  
✅ **Forbidden tables must not exist physically**  
✅ **Fail fast only when DB truly violates the contract**

**This deployment enforces the contract permanently.**

---

## 🎉 EXPECTED OUTCOME

### Before Deploy:
- ❌ Crash loop (seed fails, container restarts)
- ❌ `product_master` and 8 other legacy tables exist
- ❌ Container status: Restarting

### After Deploy:
- ✅ Clean startup (seed succeeds)
- ✅ All 9 legacy tables removed
- ✅ Container status: Running
- ✅ Logs show: `✅ Confirmed: No product_master table (correct)`
- ✅ App accessible at Railway URL

---

## 🚨 IF DEPLOYMENT STILL FAILS

### Check Release Logs:
```bash
railway logs --filter release
```

**Look for**:
- Alembic migration output
- Table drop confirmations
- Seed script output
- Any errors

### Common Issues:

**Issue 1**: Migration doesn't run
- **Fix**: Verify Procfile has `release:` line
- **Fix**: Check Railway settings for "Start Command" (should be empty)

**Issue 2**: Seed still fails after cleanup
- **Fix**: Check if any new forbidden tables were created
- **Fix**: Verify migration actually dropped tables

**Issue 3**: Web process starts too early  
- **Fix**: Ensure using `release:` not `web:` for migrations

---

## 📝 FILES CHANGED

1. ✅ **Procfile** - Fixed to use release phase
2. ✅ **Migration** - Already exists (6c9h0g1f3e4d)
3. ✅ **Seed check** - Already correct
4. ✅ **Documentation** - This file

**Total**: 1 file changed (Procfile)

---

## 🎯 COMMIT & DEPLOY

```bash
# Commit Procfile fix
git add Procfile
git commit -m "fix: Use release phase for migrations to prevent crash loops"
git push origin main

# Railway will auto-deploy
# Watch logs: railway logs --filter release
```

---

**Status**: ✅ **READY TO DEPLOY**  
**Impact**: **CRITICAL** - Stops crash loop, removes legacy tables  
**Risk**: **LOW** - Only changes deployment process, not application logic

**Deploy this immediately to stop the crash loop!** 🚀

---

**Date**: 2025-12-17  
**Engineer**: Principal Backend & Database Engineer  
**Fix**: Procfile release phase + legacy table cleanup
