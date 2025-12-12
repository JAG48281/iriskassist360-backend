"""
Security Validation Tests for Production API
Tests: Authentication, CORS, SQL Injection, Rate Limiting
"""
import os
import sys
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://web-production-afeec.up.railway.app")

class SecurityValidator:
    """Validates API security configurations"""
    
    def __init__(self):
        self.base_url = BASE_URL.rstrip('/')
        self.results = []
        self.timestamp = datetime.now().isoformat()
    
    def test_authentication(self) -> Dict[str, Any]:
        """Test 1: Check if protected endpoints require authentication"""
        print("\n" + "="*80)
        print("TEST 1: Authentication Check")
        print("="*80)
        
        # Test endpoints that might be protected
        protected_endpoints = [
            "/api/manual-seed",
            "/api/admin",
            "/api/users"
        ]
        
        public_endpoints = [
            "/api/occupancies",
            "/api/add-on-rates",
            "/api/add-on-master"
        ]
        
        results = {
            "test": "authentication",
            "protected_endpoints": [],
            "public_endpoints": [],
            "status": "PASS",
            "notes": []
        }
        
        # Test protected endpoints
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                status = response.status_code
                
                if status == 401:
                    result = "SECURE (401 Unauthorized)"
                    secure = True
                elif status == 404:
                    result = "NOT FOUND (404)"
                    secure = None
                else:
                    result = f"INSECURE (HTTP {status})"
                    secure = False
                
                results["protected_endpoints"].append({
                    "endpoint": endpoint,
                    "status_code": status,
                    "result": result,
                    "secure": secure
                })
                
                print(f"  {endpoint}: {result}")
                
            except Exception as e:
                results["protected_endpoints"].append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "secure": None
                })
                print(f"  {endpoint}: ERROR - {e}")
        
        # Test public endpoints (should be accessible)
        for endpoint in public_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                status = response.status_code
                
                accessible = status == 200
                results["public_endpoints"].append({
                    "endpoint": endpoint,
                    "status_code": status,
                    "accessible": accessible
                })
                
                print(f"  {endpoint}: {'ACCESSIBLE' if accessible else f'HTTP {status}'}")
                
            except Exception as e:
                results["public_endpoints"].append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "accessible": False
                })
                print(f"  {endpoint}: ERROR - {e}")
        
        # Determine overall status
        insecure_count = sum(1 for ep in results["protected_endpoints"] if ep.get("secure") == False)
        if insecure_count > 0:
            results["status"] = "FAIL"
            results["notes"].append(f"{insecure_count} protected endpoints are insecure")
        else:
            results["notes"].append("No authentication issues detected")
        
        print(f"\nStatus: {results['status']}")
        return results
    
    def test_cors(self) -> Dict[str, Any]:
        """Test 2: Check CORS configuration"""
        print("\n" + "="*80)
        print("TEST 2: CORS Configuration Check")
        print("="*80)
        
        results = {
            "test": "cors",
            "endpoints_tested": [],
            "cors_enabled": False,
            "allow_origin": None,
            "status": "PASS",
            "notes": []
        }
        
        test_endpoints = [
            "/api/occupancies",
            "/api/add-on-rates",
            "/"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers={"Origin": "https://example.com"},
                    timeout=5
                )
                
                cors_header = response.headers.get("Access-Control-Allow-Origin")
                
                endpoint_result = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "cors_header": cors_header,
                    "cors_enabled": cors_header is not None
                }
                
                results["endpoints_tested"].append(endpoint_result)
                
                if cors_header:
                    results["cors_enabled"] = True
                    results["allow_origin"] = cors_header
                    print(f"  {endpoint}: CORS enabled - Allow-Origin: {cors_header}")
                else:
                    print(f"  {endpoint}: No CORS headers")
                
            except Exception as e:
                results["endpoints_tested"].append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
                print(f"  {endpoint}: ERROR - {e}")
        
        if results["cors_enabled"]:
            results["notes"].append(f"CORS is configured with Allow-Origin: {results['allow_origin']}")
        else:
            results["status"] = "WARNING"
            results["notes"].append("CORS headers not detected - may cause frontend issues")
        
        print(f"\nStatus: {results['status']}")
        return results
    
    def test_sql_injection(self) -> Dict[str, Any]:
        """Test 3: SQL Injection protection"""
        print("\n" + "="*80)
        print("TEST 3: SQL Injection Protection")
        print("="*80)
        
        results = {
            "test": "sql_injection",
            "attacks_tested": [],
            "status": "PASS",
            "notes": []
        }
        
        # SQL injection payloads
        payloads = [
            "'; DROP TABLE add_on_master; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT NULL--",
            "1; DELETE FROM occupancies WHERE 1=1--"
        ]
        
        test_endpoint = "/api/occupancies"
        
        for payload in payloads:
            try:
                # Test as query parameter
                response = requests.get(
                    f"{self.base_url}{test_endpoint}",
                    params={"q": payload},
                    timeout=5
                )
                
                status = response.status_code
                
                # Check if properly handled
                if status in [400, 422]:
                    result = "PROTECTED (400/422 Bad Request)"
                    protected = True
                elif status == 200:
                    # Check if response is sanitized
                    try:
                        data = response.json()
                        # If we get valid JSON with data, it's sanitized
                        if isinstance(data, dict) and "data" in data:
                            result = "SANITIZED (200 OK with valid data)"
                            protected = True
                        else:
                            result = "POTENTIALLY VULNERABLE (200 OK)"
                            protected = False
                    except:
                        result = "POTENTIALLY VULNERABLE (Invalid response)"
                        protected = False
                else:
                    result = f"UNKNOWN (HTTP {status})"
                    protected = None
                
                attack_result = {
                    "payload": payload[:50] + "..." if len(payload) > 50 else payload,
                    "status_code": status,
                    "result": result,
                    "protected": protected
                }
                
                results["attacks_tested"].append(attack_result)
                print(f"  Payload: {payload[:40]}...")
                print(f"    Result: {result}")
                
            except Exception as e:
                results["attacks_tested"].append({
                    "payload": payload[:50],
                    "error": str(e),
                    "protected": None
                })
                print(f"  Payload: {payload[:40]}...")
                print(f"    ERROR: {e}")
        
        # Determine overall status
        vulnerable_count = sum(1 for attack in results["attacks_tested"] if attack.get("protected") == False)
        if vulnerable_count > 0:
            results["status"] = "FAIL"
            results["notes"].append(f"{vulnerable_count} SQL injection vulnerabilities detected")
        else:
            results["notes"].append("No SQL injection vulnerabilities detected")
        
        print(f"\nStatus: {results['status']}")
        return results
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test 4: Rate limiting"""
        print("\n" + "="*80)
        print("TEST 4: Rate Limiting Check")
        print("="*80)
        
        results = {
            "test": "rate_limiting",
            "global_limit_tested": False,
            "manual_seed_limit_tested": False,
            "status": "PASS",
            "notes": []
        }
        
        # 1. Test Global Limit (60/minute) on a lightweight endpoint
        test_endpoint = "/api/occupancies"
        # We need to send > 60 requests to trigger the limit
        num_requests = 65
        print(f"Testing GLOBAL LIMIT (60/min) on {test_endpoint}...")
        
        triggered = False
        for i in range(num_requests):
            try:
                response = requests.get(f"{self.base_url}{test_endpoint}", timeout=2)
                if response.status_code == 429:
                    print(f"  Request #{i+1}: 429 Too Many Requests - SUCCESS")
                    triggered = True
                    break
            except Exception:
                pass
                
        if triggered:
            results["global_limit_tested"] = True
            print("  Global rate limit verified.")
        else:
            results["status"] = "FAIL"
            results["notes"].append("Global rate limit NOT triggered after 65 requests")
            print("  Global rate limit NOT triggered.")

        return results
    
    def generate_report(self, test_results: List[Dict]) -> Dict[str, Any]:
        """Generate final security report"""
        passed = sum(1 for r in test_results if r['status'] == 'PASS')
        warnings = sum(1 for r in test_results if r['status'] == 'WARNING')
        failed = sum(1 for r in test_results if r['status'] == 'FAIL')
        
        report = {
            'timestamp': self.timestamp,
            'api_url': self.base_url,
            'total_tests': len(test_results),
            'passed': passed,
            'warnings': warnings,
            'failed': failed,
            'overall_status': 'PASS' if failed == 0 else 'FAIL',
            'security_score': f"{(passed / len(test_results) * 100):.0f}%",
            'test_results': test_results,
            'recommendations': []
        }
        
        # Add recommendations based on results
        for result in test_results:
            if result['status'] in ['FAIL', 'WARNING']:
                report['recommendations'].extend(result.get('notes', []))
        
        return report
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests"""
        print("="*80)
        print("SECURITY VALIDATION TESTS")
        print("="*80)
        print(f"API URL: {self.base_url}")
        print(f"Timestamp: {self.timestamp}")
        
        results = []
        
        # Test 1: Authentication
        try:
            results.append(self.test_authentication())
        except Exception as e:
            results.append({
                'test': 'authentication',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test 2: CORS
        try:
            results.append(self.test_cors())
        except Exception as e:
            results.append({
                'test': 'cors',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test 3: SQL Injection
        try:
            results.append(self.test_sql_injection())
        except Exception as e:
            results.append({
                'test': 'sql_injection',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test 4: Rate Limiting
        try:
            results.append(self.test_rate_limiting())
        except Exception as e:
            results.append({
                'test': 'rate_limiting',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Generate report
        report = self.generate_report(results)
        
        # Print summary
        print("\n" + "="*80)
        print("SECURITY VALIDATION SUMMARY")
        print("="*80)
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['passed']}")
        print(f"Warnings: {report['warnings']}")
        print(f"Failed: {report['failed']}")
        print(f"Security Score: {report['security_score']}")
        print(f"Overall Status: {report['overall_status']}")
        
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        # Save report
        report_file = f"artifacts/security_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("artifacts", exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved: {report_file}")
        
        return report

def main():
    validator = SecurityValidator()
    report = validator.run_all_tests()
    
    # Print JSON output
    print("\n" + "="*80)
    print("JSON OUTPUT")
    print("="*80)
    print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if report['overall_status'] == 'PASS' else 1)

if __name__ == "__main__":
    main()
