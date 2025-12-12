#!/bin/bash
# Local CI Validation Script
# Run this before pushing to validate your changes locally

set -e  # Exit on error

echo "========================================="
echo "Local CI Validation"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q pytest pytest-cov flake8 black

# Run linting
echo -e "\n${YELLOW}Running linting checks...${NC}"
flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics || {
    echo -e "${RED}❌ Linting failed${NC}"
    exit 1
}

# Check code formatting
echo -e "\n${YELLOW}Checking code formatting...${NC}"
black --check app tests || {
    echo -e "${YELLOW}⚠️  Code formatting issues found. Run 'black app tests' to fix${NC}"
}

# Run Alembic check
echo -e "\n${YELLOW}Checking Alembic migrations...${NC}"
alembic check || {
    echo -e "${RED}❌ Alembic migrations have issues${NC}"
    exit 1
}

# Run database validation (if DATABASE_URL is set)
if [ ! -z "$DATABASE_URL" ]; then
    echo -e "\n${YELLOW}Validating database schema...${NC}"
    python tests/validate_addon_rates.py || {
        echo -e "${RED}❌ Database validation failed${NC}"
        exit 1
    }
fi

# Run tests
echo -e "\n${YELLOW}Running test suite...${NC}"
pytest tests/ -v --tb=short || {
    echo -e "${RED}❌ Tests failed${NC}"
    exit 1
}

# Validate production API (if BASE_URL is set)
if [ ! -z "$BASE_URL" ]; then
    echo -e "\n${YELLOW}Validating production API...${NC}"
    python tests/validate_production_schema.py || {
        echo -e "${RED}❌ Production API validation failed${NC}"
        exit 1
    }
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ All local validations passed!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nYou can safely push your changes."
