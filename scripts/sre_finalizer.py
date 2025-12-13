"""
Autonomous SRE Finalizer
Completes production correction cycle with full validation
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://web-production-afeec.up.railway.app")

class SREFinalizer:
    """Autonomous SRE agent to finalize production deployment"""
    
    def __init__(self):
        self.base_url = BASE_URL.rstrip('/')
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_log: List[str] = []
        self.artifacts: List[str] = []
    
    def log(self, message: str, level: str = "INFO"):
        """Add entry to audit log"""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level}] {message}"
        self.audit_log.append(entry)
        print(entry)
    
    def wait_for_deployment(self, max_wait: int = 300) -> bool:
        """Wait for Railway deployment to complete"""
        self.log(f"Waiting for Railway deployment (max {max_wait}s)...")
        
        start_time = time.time()
        consecutive_success = 0
        
        while time.time() - start_time < max_wait:
            try:
                resp = requests.get(f"{self.base_url}/", timeout=10)
                if resp.status_code == 200:
                    consecutive_success += 1
                    self.log(f"API responding (success #{consecutive_success})")
                    
                    if consecutive_success >= 3:
                        self.log("Deployment appears stable")
                        return True
                else:
                    consecutive_success = 0
                    self.log(f"API returned {resp.status_code}, waiting...", "WARN")
            except Exception as e:
                consecutive_success = 0
                self.log(f"API not ready: {str(e)[:50]}", "WARN")
            
            time.sleep(10)
        
        self.log("Deployment wait timeout", "ERROR")
        return False
    
    def verify_deployment_freshness(self) -> Dict[str, Any]:
        """Verify deployment has fresh data"""
        self.log("Verifying deployment freshness...")
        
        results = {}
        
        # Check occupancies
        try:
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                results['occupancies'] = {
                    'status': 'pass' if len(data) == 298 else 'fail',
                    'count': len(data),
                    'expected': 298
                }
                self.log(f"Occupancies: {len(data)}/298")
            else:
                results['occupancies'] = {'status': 'fail', 'error': f"HTTP {resp.status_code}"}
        except Exception as e:
            results['occupancies'] = {'status': 'fail', 'error': str(e)}
        
        # Check add-on master
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-master", timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                results['add_on_master'] = {
                    'status': 'pass' if len(data) == 43 else 'fail',
                    'count': len(data),
                    'expected': 43
                }
                self.log(f"Add-on Master: {len(data)}/43")
            else:
                results['add_on_master'] = {'status': 'fail', 'error': f"HTTP {resp.status_code}"}
        except Exception as e:
            results['add_on_master'] = {'status': 'fail', 'error': str(e)}
        
        return results
    
    def trigger_reseed(self) -> Dict[str, Any]:
        """Trigger production reseed"""
        self.log("Triggering production reseed...")
        
        start_time = time.time()
        
        try:
            url = f"{self.base_url}/api/manual-seed"
            response = requests.get(url, timeout=300)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Reseed completed in {duration:.1f}s: {result}")
                return {
                    'success': True,
                    'duration': duration,
                    'result': result
                }
            else:
                self.log(f"Reseed failed: {response.status_code}", "ERROR")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'duration': duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"Reseed failed: {e}", "ERROR")
            return {
                'success': False,
                'error': str(e),
                'duration': duration
            }
    
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        self.log("Running complete validation suite...")
        
        results = {}
        
        # Validate occupancies
        try:
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            data = resp.json().get('data', [])
            results['occupancies'] = {
                'pass': len(data) == 298,
                'count': len(data),
                'expected': 298
            }
        except Exception as e:
            results['occupancies'] = {'pass': False, 'error': str(e)}
        
        # Validate add-on master
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-master", timeout=10)
            data = resp.json().get('data', [])
            results['add_on_master'] = {
                'pass': len(data) == 43,
                'count': len(data),
                'expected': 43
            }
        except Exception as e:
            results['add_on_master'] = {'pass': False, 'error': str(e)}
        
        # Validate add-on rates
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
            data = resp.json().get('data', [])
            results['add_on_rates'] = {
                'pass': len(data) == 121,
                'count': len(data),
                'expected': 121
            }
        except Exception as e:
            results['add_on_rates'] = {'pass': False, 'error': str(e)}
        
        # Check schema
        if results.get('add_on_rates', {}).get('pass'):
            try:
                resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
                data = resp.json().get('data', [])
                if data:
                    required_fields = ['add_on_code', 'product_code', 'rate_type', 'rate_value', 'occupancy_rule']
                    has_fields = all(f in data[0] for f in required_fields)
                    results['schema_validation'] = {'pass': has_fields}
            except:
                results['schema_validation'] = {'pass': False}
        
        all_pass = all(r.get('pass', False) for r in results.values())
        
        return {
            'all_pass': all_pass,
            'validations': results
        }
    
    def generate_success_report(self, validation: Dict) -> Dict[str, Any]:
        """Generate success report"""
        report = {
            'status': 'success',
            'deployment_approved': True,
            'timestamp': self.timestamp,
            'final_master_count': validation['validations'].get('add_on_master', {}).get('count', 0),
            'final_add_on_rate_count': validation['validations'].get('add_on_rates', {}).get('count', 0),
            'final_occupancies_count': validation['validations'].get('occupancies', {}).get('count', 0),
            'rules_passed': [k for k, v in validation['validations'].items() if v.get('pass')],
            'rules_failed': [],
            'snapshot_id': f"final_success_{self.timestamp}",
            'artifacts': self.artifacts,
            'audit_log': self.audit_log
        }
        
        # Save report
        report_file = f"artifacts/final_success_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        self.artifacts.append(report_file)
        
        # Write success document
        with open("PRODUCTION_RESEED_FINAL_SUCCESS.md", 'w') as f:
            f.write(f"""# Production Reseed - FINAL SUCCESS

**Operation ID**: {report['snapshot_id']}  
**Status**: SUCCESS - DEPLOYMENT APPROVED  
**Timestamp**: {self.timestamp}

## Final State

- **Add-on Master**: {report['final_master_count']}/43 PASS
- **Add-on Rates**: {report['final_add_on_rate_count']}/121 PASS
- **Occupancies**: {report['final_occupancies_count']}/298 PASS

## All Validations Passed

{chr(10).join(f'- {rule}' for rule in report['rules_passed'])}

## Deployment Status

APPROVED FOR PRODUCTION

**All systems operational. Production correction cycle completed successfully.**
""")
        
        return report
    
    def generate_failure_report(self, validation: Dict) -> Dict[str, Any]:
        """Generate failure report"""
        report = {
            'status': 'failure',
            'deployment_approved': False,
            'timestamp': self.timestamp,
            'final_master_count': validation['validations'].get('add_on_master', {}).get('count', 0),
            'final_add_on_rate_count': validation['validations'].get('add_on_rates', {}).get('count', 0),
            'final_occupancies_count': validation['validations'].get('occupancies', {}).get('count', 0),
            'rules_passed': [k for k, v in validation['validations'].items() if v.get('pass')],
            'rules_failed': [k for k, v in validation['validations'].items() if not v.get('pass')],
            'snapshot_id': f"final_failure_{self.timestamp}",
            'artifacts': self.artifacts,
            'audit_log': self.audit_log
        }
        
        # Save report
        report_file = f"artifacts/final_validation_failure_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        self.artifacts.append(report_file)
        
        # Write failure document
        with open("PRODUCTION_RESEED_FINAL_FAILURE.md", 'w') as f:
            f.write(f"""# Production Reseed - FINAL FAILURE

**Operation ID**: {report['snapshot_id']}  
**Status**: FAILED - DEPLOYMENT BLOCKED  
**Timestamp**: {self.timestamp}

## Final State

- **Add-on Master**: {report['final_master_count']}/43
- **Add-on Rates**: {report['final_add_on_rate_count']}/121
- **Occupancies**: {report['final_occupancies_count']}/298

## Failed Validations

{chr(10).join(f'- {rule}' for rule in report['rules_failed'])}

## Passed Validations

{chr(10).join(f'- {rule}' for rule in report['rules_passed'])}

## Deployment Status

BLOCKED - Manual intervention required

## Remediation Recommendations

1. Check Railway deployment logs
2. Verify CSV files in deployed container
3. Manually inspect production database
4. Consider direct database patch
""")
        
        return report
    
    def execute(self) -> Dict[str, Any]:
        """Execute complete finalization workflow"""
        try:
            # Step 1: Wait for deployment
            if not self.wait_for_deployment():
                return {
                    'status': 'error',
                    'deployment_approved': False,
                    'error': 'Deployment timeout',
                    'audit_log': self.audit_log
                }
            
            # Step 2: Verify freshness
            freshness = self.verify_deployment_freshness()
            self.log(f"Freshness check: {freshness}")
            
            # Step 3: Trigger reseed
            time.sleep(5)
            reseed_result = self.trigger_reseed()
            
            # Step 4: Wait for stability
            time.sleep(15)
            
            # Step 5: Run validation
            validation = self.run_validation_suite()
            
            # Step 6: Generate report
            if validation['all_pass']:
                report = self.generate_success_report(validation)
                self.log("[SUCCESS] All validations passed - Deployment APPROVED", "SUCCESS")
            else:
                report = self.generate_failure_report(validation)
                self.log("[FAILURE] Validation failed - Deployment BLOCKED", "ERROR")
            
            return report
            
        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
            return {
                'status': 'error',
                'deployment_approved': False,
                'error': str(e),
                'audit_log': self.audit_log
            }

def main():
    print("="*80)
    print("AUTONOMOUS SRE FINALIZER")
    print("="*80)
    
    finalizer = SREFinalizer()
    report = finalizer.execute()
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL DEPLOYMENT SUMMARY")
    print("="*80)
    print(json.dumps(report, indent=2, default=str))
    
    # Exit with appropriate code
    sys.exit(0 if report.get('deployment_approved') else 1)

if __name__ == "__main__":
    main()
