"""
Safe Production Reseed via API Endpoint
Triggers Railway's manual reseed and validates results
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://web-production-afeec.up.railway.app")

class SafeProductionReseed:
    """Safely triggers production reseed and validates"""
    
    def __init__(self):
        self.base_url = BASE_URL.rstrip('/')
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_log = []
        self.artifacts = []
    
    def log(self, message: str, level: str = "INFO"):
        """Add entry to audit log"""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level}] {message}"
        self.audit_log.append(entry)
        print(entry)
    
    def check_pre_reseed_state(self) -> Dict[str, Any]:
        """Check current state before reseed"""
        self.log("Checking pre-reseed state...")
        
        try:
            # Check occupancies
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            occ_data = resp.json().get('data', [])
            occ_count = len(occ_data)
            
            # Check add-on rates
            resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
            rates_data = resp.json().get('data', [])
            rates_count = len(rates_data)
            
            state = {
                'occupancies_count': occ_count,
                'add_on_rates_count': rates_count,
                'timestamp': self.timestamp
            }
            
            self.log(f"Pre-reseed: Occupancies={occ_count}, Add-on Rates={rates_count}")
            
            # Save pre-state
            pre_file = f"artifacts/pre_reseed_state_{self.timestamp}.json"
            with open(pre_file, 'w') as f:
                json.dump(state, f, indent=2)
            self.artifacts.append(pre_file)
            
            return state
            
        except Exception as e:
            self.log(f"Pre-check failed: {e}", "ERROR")
            return {'error': str(e)}
    
    def trigger_reseed(self) -> Dict[str, Any]:
        """Trigger manual reseed via API endpoint"""
        self.log("Triggering production reseed...")
        
        try:
            url = f"{self.base_url}/api/manual-seed"
            self.log(f"POST {url}")
            
            response = requests.get(url, timeout=300)  # 5 minute timeout
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Reseed completed: {result}")
                return {'success': True, 'result': result}
            else:
                self.log(f"Reseed failed: {response.status_code} - {response.text}", "ERROR")
                return {'success': False, 'status_code': response.status_code, 'error': response.text}
                
        except requests.exceptions.Timeout:
            self.log("Reseed timeout - may still be running", "WARN")
            return {'success': False, 'error': 'Timeout after 5 minutes'}
        except Exception as e:
            self.log(f"Reseed trigger failed: {e}", "ERROR")
            return {'success': False, 'error': str(e)}
    
    def wait_for_stability(self, seconds: int = 10):
        """Wait for database to stabilize after reseed"""
        self.log(f"Waiting {seconds} seconds for database to stabilize...")
        time.sleep(seconds)
    
    def validate_post_reseed(self) -> Dict[str, Any]:
        """Validate state after reseed"""
        self.log("Validating post-reseed state...")
        
        results = {}
        
        # Validate occupancies
        try:
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            data = resp.json().get('data', [])
            count = len(data)
            
            results['occupancies'] = {
                'pass': count == 298,
                'count': count,
                'expected': 298,
                'has_required_fields': all(
                    k in data[0] for k in ['iib_code', 'section', 'description']
                ) if data else False
            }
            self.log(f"Occupancies: {count}/298 - {'PASS' if results['occupancies']['pass'] else 'FAIL'}")
        except Exception as e:
            results['occupancies'] = {'pass': False, 'error': str(e)}
            self.log(f"Occupancies validation failed: {e}", "ERROR")
        
        # Validate add-on rates
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
            data = resp.json().get('data', [])
            count = len(data)
            
            results['add_on_rates'] = {
                'pass': count == 121,
                'count': count,
                'expected': 121,
                'has_required_fields': all(
                    k in data[0] for k in ['add_on_code', 'product_code', 'rate_type', 'rate_value', 'occupancy_rule']
                ) if data else False
            }
            self.log(f"Add-on Rates: {count}/121 - {'PASS' if results['add_on_rates']['pass'] else 'FAIL'}")
        except Exception as e:
            results['add_on_rates'] = {'pass': False, 'error': str(e)}
            self.log(f"Add-on rates validation failed: {e}", "ERROR")
        
        # Check all endpoints
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-master", timeout=10)
            data = resp.json().get('data', [])
            results['add_on_master'] = {'count': len(data)}
            self.log(f"Add-on Master: {len(data)} codes")
        except:
            pass
        
        all_pass = all(r.get('pass', False) for r in [results.get('occupancies', {}), results.get('add_on_rates', {})])
        
        return {
            'all_pass': all_pass,
            'validations': results
        }
    
    def generate_report(self, pre_state: Dict, reseed_result: Dict, post_validation: Dict) -> Dict[str, Any]:
        """Generate final validation report"""
        
        all_pass = post_validation.get('all_pass', False)
        
        report = {
            'status': 'success' if all_pass else 'failed',
            'timestamp': self.timestamp,
            'method': 'api_triggered_reseed',
            'pre_reseed_state': pre_state,
            'reseed_result': reseed_result,
            'post_validation': post_validation,
            'add_on_rates_count': post_validation.get('validations', {}).get('add_on_rates', {}).get('count', 0),
            'occupancies_count': post_validation.get('validations', {}).get('occupancies', {}).get('count', 0),
            'artifacts': self.artifacts,
            'audit_log': self.audit_log,
            'deployment_approved': all_pass
        }
        
        # Save report
        report_file = f"artifacts/reseed_validation_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.artifacts.append(report_file)
        self.log(f"Report saved: {report_file}")
        
        return report
    
    def execute(self) -> Dict[str, Any]:
        """Execute safe reseed workflow"""
        try:
            # Step 1: Check pre-state
            pre_state = self.check_pre_reseed_state()
            
            if 'error' in pre_state:
                return {'status': 'error', 'error': 'Pre-check failed', 'details': pre_state}
            
            # Step 2: Trigger reseed
            reseed_result = self.trigger_reseed()
            
            # Step 3: Wait for stability
            self.wait_for_stability(15)
            
            # Step 4: Validate
            post_validation = self.validate_post_reseed()
            
            # Step 5: Generate report
            report = self.generate_report(pre_state, reseed_result, post_validation)
            
            # Step 6: Log outcome
            if report['status'] == 'success':
                self.log("[SUCCESS] All validations passed - Deployment approved")
            else:
                self.log("[FAILED] Validation failed - Deployment blocked", "ERROR")
            
            return report
            
        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
            return {
                'status': 'error',
                'error': str(e),
                'audit_log': self.audit_log
            }

def main():
    print("="*80)
    print("SAFE PRODUCTION RESEED")
    print("="*80)
    
    reseeder = SafeProductionReseed()
    report = reseeder.execute()
    
    # Print summary
    print("\n" + "="*80)
    print("RESEED SUMMARY")
    print("="*80)
    print(json.dumps(report, indent=2, default=str))
    
    # Exit with appropriate code
    sys.exit(0 if report['status'] == 'success' else 1)

if __name__ == "__main__":
    main()
