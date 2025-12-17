"""
GUARD RAIL: NO product_master ENFORCEMENT
This script ensures product_master is never referenced in the codebase.
"""
import os
import sys

FORBIDDEN_PATTERN = "product_master"
FORBIDDEN_TABLE = "product_master"

# Files to check
PYTHON_EXTENSIONS = [".py"]
EXCLUDE_DIRS = ["venv", ".venv", "env", "__pycache__", ".git", "alembic/versions"]
EXCLUDE_FILES = ["check_no_product_master.py"]  # This file

def check_file(filepath):
    """Check if file contains forbidden pattern"""
    violations = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if FORBIDDEN_PATTERN in line.lower():
                    # Allow comments that say "NO product_master"
                    if "NO product_master" in line or "no product_master" in line:
                        continue
                    if "product_master is not part of schema" in line:
                        continue
                    violations.append((line_num, line.strip()))
    except Exception as e:
        print(f"⚠️  Could not read {filepath}: {e}")
    
    return violations

def main():
    print("=" * 60)
    print("GUARD RAIL: Checking for product_master references")
    print("=" * 60)
    print(f"Forbidden pattern: {FORBIDDEN_PATTERN}")
    print()
    
    total_violations = 0
    violation_files = []
    
    # Walk through codebase
    for root, dirs, files in os.walk("."):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            # Only check Python files
            if not any(file.endswith(ext) for ext in PYTHON_EXTENSIONS):
                continue
            
            # Skip excluded files
            if file in EXCLUDE_FILES:
                continue
            
            filepath = os.path.join(root, file)
            violations = check_file(filepath)
            
            if violations:
                total_violations += len(violations)
                violation_files.append((filepath, violations))
    
    # Report
    if total_violations == 0:
        print("✅ ✅ ✅ NO VIOLATIONS FOUND ✅ ✅ ✅")
        print()
        print("✅ No product_master references exist in codebase")
        print("✅ Products are LOGICAL, not relational")
        print("✅ System is clean and compliant")
        return 0
    else:
        print(f"❌ ❌ ❌ FOUND {total_violations} VIOLATIONS ❌ ❌ ❌")
        print()
        
        for filepath, violations in violation_files:
            print(f"\n❌ {filepath}:")
            for line_num, line in violations:
                print(f"   Line {line_num}: {line}")
        
        print()
        print("=" * 60)
        print("CRITICAL ERROR: product_master references found!")
        print("Products must be LOGICAL, not relational.")
        print("Remove ALL product_master dependencies immediately.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
