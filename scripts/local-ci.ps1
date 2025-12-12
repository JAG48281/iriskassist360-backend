# Local CI Validation Script (PowerShell)
# Run this before pushing to validate your changes locally

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Local CI Validation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
pip install -q pytest pytest-cov flake8 black

# Run linting
Write-Host "`nRunning linting checks..." -ForegroundColor Yellow
$lintResult = flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Linting failed" -ForegroundColor Red
    exit 1
}

# Check code formatting
Write-Host "`nChecking code formatting..." -ForegroundColor Yellow
black --check app tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Code formatting issues found. Run 'black app tests' to fix" -ForegroundColor Yellow
}

# Run Alembic check
Write-Host "`nChecking Alembic migrations..." -ForegroundColor Yellow
alembic check
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Alembic migrations have issues" -ForegroundColor Red
    exit 1
}

# Run database validation (if DATABASE_URL is set)
if ($env:DATABASE_URL) {
    Write-Host "`nValidating database schema..." -ForegroundColor Yellow
    python tests/validate_addon_rates.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Database validation failed" -ForegroundColor Red
        exit 1
    }
}

# Run tests
Write-Host "`nRunning test suite..." -ForegroundColor Yellow
pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed" -ForegroundColor Red
    exit 1
}

# Validate production API (if BASE_URL is set)
if ($env:BASE_URL) {
    Write-Host "`nValidating production API..." -ForegroundColor Yellow
    python tests/validate_production_schema.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Production API validation failed" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "✅ All local validations passed!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "`nYou can safely push your changes." -ForegroundColor Green
