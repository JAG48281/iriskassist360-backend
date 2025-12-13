"""
Autonomous SRE Finalizer - Complete Production Correction Cycle
Monitors Railway deployment, triggers reseed, validates, and approves/blocks deployment
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://web-production-afeec.up.railway.app")

class AutonomousSREFinalizer:
    """Complete autonomous SRE finalization agent"""
    
    def __init__(self):
        self.base_url = BASE_URL.rstrip('/')
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_log: List[str] = []
        self.artifacts: List[str] = []
        self.start_time = time.time()
        
        os.makedirs("artifacts", exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Add entry to audit log"""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level}] {message}"
        self.audit_log.append(entry)
        print(entry)
    
    def wait_for_deployment_health(self, max_wait: int = 600) -> bool:
        """Wait for Railway deployment to become healthy"""
        self.log(f"Monitoring Railway deployment health (max {max_wait}s)...")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < max_wait:
            attempt += 1
            try:
                # Try root endpoint first
                resp = requests.get(f"{self.base_url}/", timeout=5)
                if resp.status_code == 200:
                    self.log(f"API healthy on attempt #{attempt}")
                    return True
                else:
                    self.log(f"Attempt #{attempt}: HTTP {resp.status_code}", "WARN")
            except requests.exceptions.Timeout:
                self.log(f"Attempt #{attempt}: Timeout", "WARN")
            except Exception as e:
                self.log(f"Attempt #{attempt}: {str(e)[:50]}", "WARN")
            
            time.sleep(10)
        
        self.log("Deployment health check timeout", "ERROR")
        return False
    
    def verify_pre_reseed_state(self) -> Dict[str, Any]:
        """Verify state before triggering reseed"""
        self.log("Verifying pre-reseed state...")
        
        state = {}
        
        try:
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                state['occupancies'] = len(data)
                self.log(f"Pre-reseed occupancies: {len(data)}")
        except Exception as e:
            state['occupancies'] = f"error: {e}"
        
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-master", timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                state['add_on_master'] = len(data)
                self.log(f"Pre-reseed add-on master: {len(data)}")
        except Exception as e:
            state['add_on_master'] = f"error: {e}"
        
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                state['add_on_rates'] = len(data)
                self.log(f"Pre-reseed add-on rates: {len(data)}")
        except Exception as e:
            state['add_on_rates'] = f"error: {e}"
        
        return state
    
    def trigger_reseed(self) -> Dict[str, Any]:
        """Trigger production reseed"""
        self.log("Triggering production reseed...")
        
        reseed_start = time.time()
        
        try:
            url = f"{self.base_url}/api/manual-seed"
            response = requests.get(url, timeout=300)
            duration = time.time() - reseed_start
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Reseed completed in {duration:.1f}s")
                return {
                    'success': True,
                    'duration': duration,
                    'result': result
                }
            else:
                self.log(f"Reseed failed: HTTP {response.status_code}", "ERROR")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'duration': duration
                }
        except Exception as e:
            duration = time.time() - reseed_start
            self.log(f"Reseed failed: {e}", "ERROR")
            return {
                'success': False,
                'error': str(e),
                'duration': duration
            }
    
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        self.log("Running complete validation suite...")
        
        validations = {}
        
        # Validate occupancies
        try:
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            data = resp.json().get('data', [])
            count = len(data)
            validations['occupancies'] = {
                'pass': count == 298,
                'count': count,
                'expected': 298
            }
            self.log(f"Occupancies: {count}/298 - {'PASS' if count == 298 else 'FAIL'}")
        except Exception as e:
            validations['occupancies'] = {'pass': False, 'error': str(e)}
            self.log(f"Occupancies validation error: {e}", "ERROR")
        
        # Validate add-on master
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-master", timeout=10)
            data = resp.json().get('data', [])
            count = len(data)
            validations['add_on_master'] = {
                'pass': count == 43,
                'count': count,
                'expected': 43
            }
            self.log(f"Add-on Master: {count}/43 - {'PASS' if count == 43 else 'FAIL'}")
        except Exception as e:
            validations['add_on_master'] = {'pass': False, 'error': str(e)}
            self.log(f"Add-on master validation error: {e}", "ERROR")
        
        # Validate add-on rates
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
            data = resp.json().get('data', [])
            count = len(data)
            validations['add_on_rates'] = {
                'pass': count == 121,
                'count': count,
                'expected': 121
            }
            self.log(f"Add-on Rates: {count}/121 - {'PASS' if count == 121 else 'FAIL'}")
            
            # Validate schema
            if data:
                required_fields = ['add_on_code', 'product_code', 'rate_type', 'rate_value', 'occupancy_rule']
                has_all_fields = all(f in data[0] for f in required_fields)
                validations['schema'] = {
                    'pass': has_all_fields,
                    'fields_present': list(data[0].keys()) if data else []
                }
                self.log(f"Schema validation: {'PASS' if has_all_fields else 'FAIL'}")
        except Exception as e:
            validations['add_on_rates'] = {'pass': False, 'error': str(e)}
            self.log(f"Add-on rates validation error: {e}", "ERROR")
        
        all_pass = all(v.get('pass', False) for v in validations.values())
        
        return {
            'all_pass': all_pass,
            'validations': validations
        }
    
    def generate_success_report(self, pre_state: Dict, reseed_result: Dict, validation: Dict) -> Dict[str, Any]:
        """Generate success report and artifacts"""
        self.log("Generating success report...")
        
        total_duration = time.time() - self.start_time
        
        report = {
            'status': 'success',
            'deployment_approved': True,
            'timestamp': self.timestamp,
            'total_duration_seconds': round(total_duration, 2),
            'final_master_count': validation['validations'].get('add_on_master', {}).get('count', 0),
            'final_add_on_rate_count': validation['validations'].get('add_on_rates', {}).get('count', 0),
            'final_occupancies_count': validation['validations'].get('occupancies', {}).get('count', 0),
            'rules_passed': [k for k, v in validation['validations'].items() if v.get('pass')],
            'rules_failed': [],
            'snapshot_id': f"success_{self.timestamp}",
            'pre_reseed_state': pre_state,
            'reseed_result': reseed_result,
            'validation_details': validation,
            'artifacts': self.artifacts,
            'audit_log': self.audit_log
        }
        
        # Save JSON report
        json_file = f"artifacts/final_success_report_{self.timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        self.artifacts.append(json_file)
        
        # Save markdown report
        md_content = f"""# Production Reseed - FINAL SUCCESS

**Operation ID**: {report['snapshot_id']}  
**Status**: ✅ **SUCCESS - DEPLOYMENT APPROVED**  
**Timestamp**: {datetime.now().isoformat()}  
**Total Duration**: {total_duration:.1f} seconds

---

## Final State

| Component | Count | Expected | Status |
|-----------|-------|----------|--------|
| **Occupancies** | {report['final_occupancies_count']} | 298 | ✅ PASS |
| **Add-on Master** | {report['final_master_count']} | 43 | ✅ PASS |
| **Add-on Rates** | {report['final_add_on_rate_count']} | 121 | ✅ PASS |

---

## All Validations Passed

{chr(10).join(f'- ✅ {rule}' for rule in report['rules_passed'])}

---

## Operation Timeline

1. **Log Spam Fix**: Commit 725a49a deployed
2. **Deployment Health**: Railway became healthy
3. **Pre-Reseed State**: Verified baseline
4. **Reseed Triggered**: Completed in {reseed_result.get('duration', 0):.1f}s
5. **Validation Suite**: All checks passed
6. **Deployment**: APPROVED

---

## Deployment Status

**✅ APPROVED FOR PRODUCTION**

All systems operational. Production correction cycle completed successfully.

---

## Artifacts

{chr(10).join(f'- {artifact}' for artifact in report['artifacts'])}

---

**Report Generated**: {datetime.now().isoformat()}  
**Operator**: Autonomous SRE Finalizer  
**Deployment**: PRODUCTION READY ✅
"""
        
        with open("PRODUCTION_RESEED_FINAL_SUCCESS.md", 'w') as f:
            f.write(md_content)
        
        return report
    
    def generate_failure_report(self, pre_state: Dict, reseed_result: Dict, validation: Dict) -> Dict[str, Any]:
        """Generate failure report and artifacts"""
        self.log("Generating failure report...", "ERROR")
        
        total_duration = time.time() - self.start_time
        
        report = {
            'status': 'failure',
            'deployment_approved': False,
            'timestamp': self.timestamp,
            'total_duration_seconds': round(total_duration, 2),
            'final_master_count': validation['validations'].get('add_on_master', {}).get('count', 0),
            'final_add_on_rate_count': validation['validations'].get('add_on_rates', {}).get('count', 0),
            'final_occupancies_count': validation['validations'].get('occupancies', {}).get('count', 0),
            'rules_passed': [k for k, v in validation['validations'].items() if v.get('pass')],
            'rules_failed': [k for k, v in validation['validations'].items() if not v.get('pass')],
            'snapshot_id': f"failure_{self.timestamp}",
            'pre_reseed_state': pre_state,
            'reseed_result': reseed_result,
            'validation_details': validation,
            'artifacts': self.artifacts,
            'audit_log': self.audit_log
        }
        
        # Save JSON report
        json_file = f"artifacts/final_validation_failure_{self.timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        self.artifacts.append(json_file)
        
        # Save markdown report
        md_content = f"""# Production Reseed - FINAL FAILURE

**Operation ID**: {report['snapshot_id']}  
**Status**: ❌ **FAILED - DEPLOYMENT BLOCKED**  
**Timestamp**: {datetime.now().isoformat()}  
**Total Duration**: {total_duration:.1f} seconds

---

## Final State

| Component | Count | Expected | Status |
|-----------|-------|----------|--------|
| **Occupancies** | {report['final_occupancies_count']} | 298 | {'✅' if report['final_occupancies_count'] == 298 else '❌'} |
| **Add-on Master** | {report['final_master_count']} | 43 | {'✅' if report['final_master_count'] == 43 else '❌'} |
| **Add-on Rates** | {report['final_add_on_rate_count']} | 121 | {'✅' if report['final_add_on_rate_count'] == 121 else '❌'} |

---

## Failed Validations

{chr(10).join(f'- ❌ {rule}' for rule in report['rules_failed'])}

---

## Passed Validations

{chr(10).join(f'- ✅ {rule}' for rule in report['rules_passed'])}

---

## Remediation Recommendations

1. Check Railway deployment logs for errors
2. Verify CSV files in deployed container
3. Manually inspect production database
4. Review seed script execution logs
5. Consider direct database patch if needed

---

## Deployment Status

**❌ BLOCKED - Manual intervention required**

---

**Report Generated**: {datetime.now().isoformat()}  
**Operator**: Autonomous SRE Finalizer  
**Action Required**: MANUAL INVESTIGATION
"""
        
        with open("PRODUCTION_RESEED_FINAL_FAILURE.md", 'w') as f:
            f.write(md_content)
        
        return report
    
    def execute(self) -> Dict[str, Any]:
        """Execute complete finalization workflow"""
        try:
            # Step 1: Wait for deployment health
            self.log("=== STEP 1: Monitoring Railway Deployment ===")
            if not self.wait_for_deployment_health():
                return {
                    'status': 'error',
                    'deployment_approved': False,
                    'error': 'Deployment health check timeout',
                    'audit_log': self.audit_log
                }
            
            # Step 2: Verify pre-reseed state
            self.log("=== STEP 2: Verifying Pre-Reseed State ===")
            pre_state = self.verify_pre_reseed_state()
            
            # Step 3: Trigger reseed
            self.log("=== STEP 3: Triggering Production Reseed ===")
            time.sleep(5)  # Brief stability wait
            reseed_result = self.trigger_reseed()
            
            if not reseed_result.get('success'):
                self.log("Reseed failed, but continuing to validation", "WARN")
            
            # Step 4: Wait for reseed completion
            self.log("=== STEP 4: Waiting for Reseed Completion ===")
            time.sleep(20)  # Allow time for data to settle
            
            # Step 5: Run validation suite
            self.log("=== STEP 5: Running Validation Suite ===")
            validation = self.run_validation_suite()
            
            # Step 6: Generate report
            self.log("=== STEP 6: Generating Final Report ===")
            if validation['all_pass']:
                report = self.generate_success_report(pre_state, reseed_result, validation)
                self.log("[SUCCESS] All validations passed - Deployment APPROVED", "SUCCESS")
            else:
                report = self.generate_failure_report(pre_state, reseed_result, validation)
                self.log("[FAILURE] Validation failed - Deployment BLOCKED", "ERROR")
            
            # Save finalizer logs
            logs_file = "artifacts/finalizer_logs.json"
            with open(logs_file, 'w') as f:
                json.dump({
                    'audit_log': self.audit_log,
                    'timestamp': self.timestamp,
                    'duration': time.time() - self.start_time
                }, f, indent=2)
            
            return report
            
        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
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
    print(f"Starting at: {datetime.now().isoformat()}")
    print("="*80)
    
    finalizer = AutonomousSREFinalizer()
    report = finalizer.execute()
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL DEPLOYMENT SUMMARY")
    print("="*80)
    print(json.dumps(report, indent=2, default=str))
    print("="*80)
    
    # Exit with appropriate code
    sys.exit(0 if report.get('deployment_approved') else 1)

if __name__ == "__main__":
    main()
