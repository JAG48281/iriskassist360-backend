"""
Production API Schema Validator
Validates exact row counts and field schemas for critical endpoints
"""
import os
import sys
import requests
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

class SchemaValidationError(Exception):
    """Raised when schema validation fails"""
    pass

class EndpointValidator:
    """Validates API endpoint responses against expected schemas"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.errors: List[str] = []
    
    def validate_endpoint(
        self,
        endpoint: str,
        expected_count: int,
        required_fields: List[str],
        exact_count: bool = True
    ) -> Dict[str, Any]:
        """
        Validate an endpoint's response
        
        Args:
            endpoint: API endpoint path
            expected_count: Expected number of rows
            required_fields: Required fields in each row
            exact_count: If True, count must match exactly; if False, count must be >= expected
        
        Returns:
            Validation result dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error = f"{endpoint}: HTTP {response.status_code}"
                self.errors.append(error)
                return {
                    "endpoint": endpoint,
                    "status": "FAILED",
                    "error": error
                }
            
            data = response.json()
            
            # Handle ResponseModel wrapper
            if isinstance(data, dict) and "data" in data:
                items = data["data"]
            else:
                items = data
            
            if not isinstance(items, list):
                error = f"{endpoint}: Response is not a list"
                self.errors.append(error)
                return {
                    "endpoint": endpoint,
                    "status": "FAILED",
                    "error": error
                }
            
            actual_count = len(items)
            
            # Validate count
            if exact_count:
                if actual_count != expected_count:
                    error = f"{endpoint}: Expected exactly {expected_count} rows, got {actual_count}"
                    self.errors.append(error)
                    return {
                        "endpoint": endpoint,
                        "status": "FAILED",
                        "expected_count": expected_count,
                        "actual_count": actual_count,
                        "error": error
                    }
            else:
                if actual_count < expected_count:
                    error = f"{endpoint}: Expected >= {expected_count} rows, got {actual_count}"
                    self.errors.append(error)
                    return {
                        "endpoint": endpoint,
                        "status": "FAILED",
                        "expected_count": f">= {expected_count}",
                        "actual_count": actual_count,
                        "error": error
                    }
            
            # Validate schema
            if items:
                sample = items[0]
                missing_fields = [f for f in required_fields if f not in sample]
                
                if missing_fields:
                    error = f"{endpoint}: Missing required fields: {missing_fields}"
                    self.errors.append(error)
                    return {
                        "endpoint": endpoint,
                        "status": "FAILED",
                        "actual_fields": list(sample.keys()),
                        "missing_fields": missing_fields,
                        "error": error
                    }
            
            return {
                "endpoint": endpoint,
                "status": "PASSED",
                "count": actual_count,
                "fields": list(items[0].keys()) if items else [],
                "sample": items[0] if items else None
            }
            
        except requests.exceptions.RequestException as e:
            error = f"{endpoint}: Request failed - {str(e)}"
            self.errors.append(error)
            return {
                "endpoint": endpoint,
                "status": "FAILED",
                "error": error
            }
        except Exception as e:
            error = f"{endpoint}: Unexpected error - {str(e)}"
            self.errors.append(error)
            return {
                "endpoint": endpoint,
                "status": "FAILED",
                "error": error
            }

def main():
    """Main validation function"""
    validator = EndpointValidator(BASE_URL)
    
    print(f"Validating API at: {BASE_URL}")
    print("=" * 80)
    
    # Define validation rules
    validations = [
        {
            "endpoint": "/api/occupancies",
            "expected_count": 298,
            "required_fields": ["iib_code", "section", "description"],
            "exact_count": True
        },
        {
            "endpoint": "/api/add-on-rates",
            "expected_count": 121,
            "required_fields": ["add_on_code", "product_code", "rate_type", "rate_value", "occupancy_rule"],
            "exact_count": True
        }
    ]
    
    results = []
    
    for validation in validations:
        print(f"\nValidating {validation['endpoint']}...")
        result = validator.validate_endpoint(
            validation["endpoint"],
            validation["expected_count"],
            validation["required_fields"],
            validation.get("exact_count", True)
        )
        results.append(result)
        
        if result["status"] == "PASSED":
            print(f"  [PASS] {result['count']} rows with correct schema")
        else:
            print(f"  [FAIL] {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if validator.errors:
        print("\nERRORS:")
        for error in validator.errors:
            print(f"  - {error}")
    
    # Output JSON for CI/CD
    output = {
        "base_url": BASE_URL,
        "total_validations": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
        "errors": validator.errors
    }
    
    with open("artifacts/schema_validation.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDetailed results saved to: artifacts/schema_validation.json")
    
    # Exit with error code if any validation failed
    if failed > 0:
        sys.exit(1)
    
    print("\n[SUCCESS] All validations passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()
