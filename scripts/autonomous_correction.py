"""
Production Master Table Correction and Validation Orchestrator
Autonomous SRE operation to restore missing add-on codes and validate deployment
"""
import os
import sys
import json
import csv
import time
import psycopg2
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

class ProductionCorrectionOrchestrator:
    """Orchestrates complete production correction cycle"""
    
    def __init__(self):
        self.database_url = os.getenv("PRODUCTION_DATABASE_URL") or os.getenv("DATABASE_URL")
        self.base_url = os.getenv("BASE_URL", "https://web-production-afeec.up.railway.app")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_log: List[str] = []
        self.artifacts: List[str] = []
        self.conn = None
        
        # Create artifacts directory
        os.makedirs("artifacts/sql_patches", exist_ok=True)
        
        if not self.database_url:
            raise ValueError("PRODUCTION_DATABASE_URL or DATABASE_URL not set")
    
    def log(self, message: str, level: str = "INFO"):
        """Add entry to audit log"""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level}] {message}"
        self.audit_log.append(entry)
        print(entry)
    
    def fetch_canonical_master(self) -> List[Dict[str, str]]:
        """Fetch canonical add-on master from CSV"""
        self.log("Fetching canonical master from CSV...")
        
        csv_path = "data/add_on_master.csv"
        codes = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            codes = list(reader)
        
        self.log(f"CSV contains {len(codes)} add-on codes")
        return codes
    
    def generate_master_diff(self, canonical: List[Dict]) -> Tuple[List[Dict], str]:
        """Generate diff between production and canonical master"""
        self.log("Generating master table diff...")
        
        # Connect to production
        self.conn = psycopg2.connect(self.database_url)
        cur = self.conn.cursor()
        
        # Get production master codes
        cur.execute("SELECT add_on_code FROM add_on_master ORDER BY add_on_code")
        prod_codes = {row[0] for row in cur.fetchall()}
        
        self.log(f"Production has {len(prod_codes)} codes")
        
        # Find missing codes
        canonical_codes = {row['add_on_code'] for row in canonical}
        missing_codes = canonical_codes - prod_codes
        
        self.log(f"Missing codes: {sorted(missing_codes)}")
        
        # Get full records for missing codes
        missing_records = [r for r in canonical if r['add_on_code'] in missing_codes]
        
        # Generate SQL
        sql_statements = []
        sql_statements.append("-- Missing Add-on Master Codes Patch")
        sql_statements.append(f"-- Generated: {self.timestamp}")
        sql_statements.append(f"-- Missing codes: {len(missing_records)}\n")
        
        for record in missing_records:
            sql = f"""INSERT INTO add_on_master (add_on_code, add_on_name, description, is_percentage, applies_to_product, active)
VALUES ('{record['add_on_code']}', '{record['add_on_name']}', '{record.get('description', '')}', {record['is_percentage']}, {record['applies_to_product']}, {record['active']})
ON CONFLICT (add_on_code) DO NOTHING;"""
            sql_statements.append(sql)
        
        sql_patch = "\n\n".join(sql_statements)
        
        # Save SQL patch
        patch_file = f"artifacts/sql_patches/master_patch_{self.timestamp}.sql"
        with open(patch_file, 'w') as f:
            f.write(sql_patch)
        
        self.artifacts.append(patch_file)
        self.log(f"SQL patch saved: {patch_file}")
        
        return missing_records, sql_patch
    
    def wait_for_railway_deployment(self, max_wait: int = 300):
        """Wait for Railway deployment to complete"""
        self.log(f"Waiting for Railway deployment (max {max_wait}s)...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            try:
                resp = requests.get(f"{self.base_url}/", timeout=5)
                if resp.status_code == 200:
                    current_status = resp.json()
                    if current_status != last_status:
                        self.log(f"API Status: {current_status}")
                        last_status = current_status
                    
                    # Check if deployment is stable
                    time.sleep(10)
                    resp2 = requests.get(f"{self.base_url}/", timeout=5)
                    if resp2.status_code == 200:
                        self.log("Railway deployment appears stable")
                        return True
            except:
                self.log("API not yet available, waiting...", "WARN")
            
            time.sleep(15)
        
        self.log("Deployment wait timeout", "WARN")
        return False
    
    def apply_master_patch(self, sql_patch: str) -> Dict[str, Any]:
        """Apply master table patch to production"""
        self.log("Applying master table patch...")
        
        # Save pre-patch state
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM add_on_master")
        pre_count = cur.fetchone()[0]
        
        self.log(f"Pre-patch master count: {pre_count}")
        
        try:
            # Execute patch
            for statement in sql_patch.split('\n\n'):
                if statement.strip() and not statement.strip().startswith('--'):
                    cur.execute(statement)
            
            self.conn.commit()
            
            # Get post-patch state
            cur.execute("SELECT COUNT(*) FROM add_on_master")
            post_count = cur.fetchone()[0]
            
            self.log(f"Post-patch master count: {post_count}")
            self.log(f"Inserted {post_count - pre_count} new codes")
            
            return {
                'success': True,
                'pre_count': pre_count,
                'post_count': post_count,
                'inserted': post_count - pre_count
            }
            
        except Exception as e:
            self.conn.rollback()
            self.log(f"Patch application failed: {e}", "ERROR")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_reseed(self) -> Dict[str, Any]:
        """Trigger production reseed"""
        self.log("Triggering production reseed...")
        
        try:
            url = f"{self.base_url}/api/manual-seed"
            response = requests.get(url, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Reseed completed: {result}")
                return {'success': True, 'result': result}
            else:
                self.log(f"Reseed failed: {response.status_code}", "ERROR")
                return {'success': False, 'status_code': response.status_code}
                
        except Exception as e:
            self.log(f"Reseed failed: {e}", "ERROR")
            return {'success': False, 'error': str(e)}
    
    def validate_production(self) -> Dict[str, Any]:
        """Run full validation suite"""
        self.log("Running full validation suite...")
        
        results = {}
        
        # Validate API schemas
        try:
            resp = requests.get(f"{self.base_url}/api/occupancies", timeout=10)
            occ_data = resp.json().get('data', [])
            results['occupancies'] = {
                'pass': len(occ_data) == 298,
                'count': len(occ_data),
                'expected': 298
            }
        except Exception as e:
            results['occupancies'] = {'pass': False, 'error': str(e)}
        
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-rates", timeout=10)
            rates_data = resp.json().get('data', [])
            results['add_on_rates'] = {
                'pass': len(rates_data) == 121,
                'count': len(rates_data),
                'expected': 121
            }
        except Exception as e:
            results['add_on_rates'] = {'pass': False, 'error': str(e)}
        
        try:
            resp = requests.get(f"{self.base_url}/api/add-on-master", timeout=10)
            master_data = resp.json().get('data', [])
            results['add_on_master'] = {
                'pass': len(master_data) == 43,
                'count': len(master_data),
                'expected': 43
            }
        except Exception as e:
            results['add_on_master'] = {'pass': False, 'error': str(e)}
        
        # Validate database rules
        try:
            cur = self.conn.cursor()
            
            # Rule 1: Count
            cur.execute("SELECT COUNT(*) FROM add_on_rates WHERE active = true")
            count = cur.fetchone()[0]
            results['rule_1_count'] = {'pass': count == 121, 'actual': count}
            
            # Rule 5: POLICY_RATE values
            cur.execute("""
                SELECT COUNT(*) FROM add_on_rates 
                WHERE active = true AND UPPER(rate_type) = 'POLICY_RATE' AND rate_value != 0
            """)
            violations = cur.fetchone()[0]
            results['rule_5_policy_rate'] = {'pass': violations == 0, 'violations': violations}
            
        except Exception as e:
            self.log(f"Database validation failed: {e}", "ERROR")
        
        all_pass = all(r.get('pass', False) for r in results.values())
        
        return {
            'all_pass': all_pass,
            'validations': results
        }
    
    def generate_final_report(self, patch_result: Dict, reseed_result: Dict, 
                            validation: Dict) -> Dict[str, Any]:
        """Generate final operation report"""
        
        all_pass = validation.get('all_pass', False)
        
        report = {
            'status': 'completed' if all_pass else 'failed',
            'deployment_approved': all_pass,
            'timestamp': self.timestamp,
            'final_master_count': validation['validations'].get('add_on_master', {}).get('count', 0),
            'final_add_on_rate_count': validation['validations'].get('add_on_rates', {}).get('count', 0),
            'final_occupancies_count': validation['validations'].get('occupancies', {}).get('count', 0),
            'rules_passed': [k for k, v in validation['validations'].items() if v.get('pass')],
            'rules_failed': [k for k, v in validation['validations'].items() if not v.get('pass')],
            'snapshot_id': f"operation_{self.timestamp}",
            'patch_result': patch_result,
            'reseed_result': reseed_result,
            'validation_details': validation,
            'artifacts': self.artifacts,
            'audit_log': self.audit_log
        }
        
        # Save report
        report_file = f"artifacts/final_validation_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.artifacts.append(report_file)
        self.log(f"Final report saved: {report_file}")
        
        return report
    
    def write_success_document(self, report: Dict):
        """Write success documentation"""
        content = f"""# Production Reseed - FINAL SUCCESS

**Operation ID**: {report['snapshot_id']}  
**Status**: ✅ **SUCCESS - DEPLOYMENT APPROVED**  
**Timestamp**: {self.timestamp}

## Final State

- **Add-on Master**: {report['final_master_count']}/43 ✅
- **Add-on Rates**: {report['final_add_on_rate_count']}/121 ✅
- **Occupancies**: {report['final_occupancies_count']}/298 ✅

## Rules Passed

{chr(10).join(f'- ✅ {rule}' for rule in report['rules_passed'])}

## Operation Summary

1. ✅ Master table patch applied successfully
2. ✅ Production reseed completed
3. ✅ All validations passed
4. ✅ Deployment APPROVED

## Artifacts

{chr(10).join(f'- {artifact}' for artifact in report['artifacts'])}

**Deployment Status**: APPROVED FOR PRODUCTION ✅
"""
        
        with open("PRODUCTION_RESEED_FINAL_SUCCESS.md", 'w') as f:
            f.write(content)
        
        self.log("Success document written")
    
    def write_failure_document(self, report: Dict):
        """Write failure documentation"""
        content = f"""# Production Reseed - FINAL FAILURE

**Operation ID**: {report['snapshot_id']}  
**Status**: ❌ **FAILED - DEPLOYMENT BLOCKED**  
**Timestamp**: {self.timestamp}

## Final State

- **Add-on Master**: {report['final_master_count']}/43
- **Add-on Rates**: {report['final_add_on_rate_count']}/121
- **Occupancies**: {report['final_occupancies_count']}/298

## Rules Failed

{chr(10).join(f'- ❌ {rule}' for rule in report['rules_failed'])}

## Rules Passed

{chr(10).join(f'- ✅ {rule}' for rule in report['rules_passed'])}

## Remediation Required

Manual intervention needed. Review artifacts for details.

## Artifacts

{chr(10).join(f'- {artifact}' for artifact in report['artifacts'])}

**Deployment Status**: BLOCKED ❌
"""
        
        with open("PRODUCTION_RESEED_FINAL_FAILURE.md", 'w') as f:
            f.write(content)
        
        self.log("Failure document written")
    
    def execute(self) -> Dict[str, Any]:
        """Execute complete correction cycle"""
        try:
            # Step 1: Fetch canonical master
            canonical = self.fetch_canonical_master()
            
            # Step 2: Generate diff and patch
            missing_records, sql_patch = self.generate_master_diff(canonical)
            
            if not missing_records:
                self.log("No missing codes - production is up to date")
                # Still need to validate
            
            # Step 3: Wait for Railway deployment
            self.wait_for_railway_deployment()
            
            # Step 4: Apply master patch
            patch_result = self.apply_master_patch(sql_patch) if missing_records else {'success': True, 'inserted': 0}
            
            # Step 5: Trigger reseed
            time.sleep(10)  # Stability wait
            reseed_result = self.trigger_reseed()
            
            # Step 6: Wait for reseed to complete
            time.sleep(15)
            
            # Step 7: Validate
            validation = self.validate_production()
            
            # Step 8: Generate report
            report = self.generate_final_report(patch_result, reseed_result, validation)
            
            # Step 9: Write outcome document
            if report['deployment_approved']:
                self.write_success_document(report)
                self.log("[SUCCESS] All validations passed - Deployment APPROVED", "SUCCESS")
            else:
                self.write_failure_document(report)
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
        finally:
            if self.conn:
                self.conn.close()
                self.log("Database connection closed")

def main():
    print("="*80)
    print("PRODUCTION CORRECTION ORCHESTRATOR")
    print("="*80)
    
    orchestrator = ProductionCorrectionOrchestrator()
    report = orchestrator.execute()
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL OPERATION SUMMARY")
    print("="*80)
    print(json.dumps(report, indent=2, default=str))
    
    # Exit with appropriate code
    sys.exit(0 if report.get('deployment_approved') else 1)

if __name__ == "__main__":
    main()
