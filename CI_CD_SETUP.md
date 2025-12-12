# CI/CD Pipeline Setup Guide

## Overview
This CI/CD pipeline automatically validates your FastAPI backend on every push and pull request, ensuring production quality before deployment.

## Pipeline Stages

### 1. **Lint and Validate** (Always runs)
- Python syntax checking with flake8
- Code formatting validation with black
- Runs on all branches

### 2. **Local Database Tests** (Always runs)
- Spins up PostgreSQL test database
- Runs Alembic migrations
- Seeds test data
- Validates database schema (9 business rules)
- Runs full pytest suite with coverage
- Uploads coverage to Codecov

### 3. **Production API Tests** (Main branch only)
- Validates production API health
- Checks all endpoints are operational
- Validates exact row counts:
  - `/api/occupancies`: Exactly 298 rows
  - `/api/add-on-rates`: Exactly 121 rows
- Validates response schemas
- Runs integration tests against production
- Validates production database integrity

### 4. **Deployment Notification** (Always runs)
- Reports overall pipeline status
- Blocks deployment if any test fails

## GitHub Secrets Setup

Add these secrets in your GitHub repository:

1. Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

2. Add the following secrets:

   **PRODUCTION_DATABASE_URL**
   ```
   postgresql://username:password@host:port/database
   ```
   *Get this from Railway dashboard → Database → Connect*

   **CODECOV_TOKEN** (Optional, for coverage reports)
   ```
   <your-codecov-token>
   ```
   *Get this from codecov.io after linking your repo*

## Local Validation

Before pushing, run local validation:

### Windows (PowerShell):
```powershell
# Set environment variables
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/iriskassist360_db"
$env:BASE_URL="https://web-production-afeec.up.railway.app"

# Run validation
.\scripts\local-ci.ps1
```

### Linux/Mac (Bash):
```bash
# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/iriskassist360_db"
export BASE_URL="https://web-production-afeec.up.railway.app"

# Run validation
chmod +x scripts/local-ci.sh
./scripts/local-ci.sh
```

## Manual Validation Commands

### Validate Database Schema
```bash
python tests/validate_addon_rates.py
```

### Validate Production API
```bash
export BASE_URL="https://web-production-afeec.up.railway.app"
python tests/validate_production_schema.py
```

### Run Integration Tests
```bash
export BASE_URL="https://web-production-afeec.up.railway.app"
pytest tests/test_api.py -v
```

### Check Endpoints
```bash
export BASE_URL="https://web-production-afeec.up.railway.app"
python tests/check_endpoints.py
```

## Pipeline Triggers

The pipeline runs on:
- **Push** to `main` or `develop` branches
- **Pull requests** to `main` or `develop` branches
- **Manual trigger** via GitHub Actions UI

## Deployment Blocking

The pipeline will **BLOCK deployment** if:
- ❌ Any linting errors (syntax, undefined names)
- ❌ Alembic migration issues
- ❌ Database schema validation fails
- ❌ Any pytest test fails
- ❌ Production API returns wrong row counts
- ❌ Production API has schema mismatches
- ❌ Production database validation fails

## Success Criteria

All checks must pass:
- ✅ Code linting passes
- ✅ Alembic migrations apply cleanly
- ✅ Database has exactly 121 add-on rates
- ✅ All 9 business rules pass
- ✅ All pytest tests pass
- ✅ Production API health check succeeds
- ✅ `/api/occupancies` returns exactly 298 rows
- ✅ `/api/add-on-rates` returns exactly 121 rows
- ✅ Response schemas match expected fields

## Monitoring

### View Pipeline Status
1. Go to your GitHub repository
2. Click **Actions** tab
3. Select the latest workflow run
4. View detailed logs for each job

### View Test Coverage
- Coverage reports are uploaded to Codecov
- View at: `https://codecov.io/gh/YOUR_USERNAME/iriskassist360-backend`

### View Validation Reports
- Schema validation results: `artifacts/schema_validation.json`
- Test reports: `artifacts/test_report.json`
- Validation reports: `artifacts/validation_report.json`

## Troubleshooting

### Pipeline fails on "Production API Tests"
- Check Railway deployment logs
- Verify `BASE_URL` is correct
- Ensure production database is seeded
- Run manual reseed: `curl https://web-production-afeec.up.railway.app/api/manual-seed`

### Database validation fails
- Check if migrations were applied
- Verify seed data is complete
- Run local validation to debug

### Schema validation fails
- Check endpoint response format
- Verify field names match expected schema
- Review `artifacts/schema_validation.json` for details

## Best Practices

1. **Always run local validation** before pushing
2. **Review pipeline logs** if tests fail
3. **Keep secrets updated** in GitHub settings
4. **Monitor coverage trends** to maintain quality
5. **Fix failing tests immediately** - don't merge broken code

## Files Created

### CI/CD Configuration
- `.github/workflows/ci.yml` - Main GitHub Actions workflow

### Validation Scripts
- `tests/validate_production_schema.py` - Production API schema validator
- `tests/validate_addon_rates.py` - Database business rules validator
- `tests/check_endpoints.py` - Endpoint availability checker
- `tests/verify_schemas.py` - Field schema verifier
- `tests/test_api.py` - Integration test suite

### Local Validation
- `scripts/local-ci.sh` - Bash validation script
- `scripts/local-ci.ps1` - PowerShell validation script

## Next Steps

1. ✅ Commit the CI/CD files
2. ✅ Add GitHub secrets
3. ✅ Push to trigger first pipeline run
4. ✅ Monitor the Actions tab
5. ✅ Fix any issues that arise
6. ✅ Celebrate when all checks pass! 🎉
