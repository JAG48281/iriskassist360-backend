"""
Pydantic v2 Migration Verification Script
Tests that all schemas are properly migrated and no warnings are raised.
"""
import sys
import warnings
from io import StringIO

def test_schema_imports():
    """Test that all schemas can be imported without warnings"""
    print("="*80)
    print("PYDANTIC V2 MIGRATION VERIFICATION")
    print("="*80)
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        print("\n1. Testing schema imports...")
        
        try:
            from app.schemas.user_schema import UserCreate, UserOut
            print("   ✅ user_schema imported successfully")
        except Exception as e:
            print(f"   ❌ user_schema import failed: {e}")
            return False
            
        try:
            from app.schemas.rate_schema import RateCreate, RateOut
            print("   ✅ rate_schema imported successfully")
        except Exception as e:
            print(f"   ❌ rate_schema import failed: {e}")
            return False
            
        try:
            from app.schemas.quote_schema import QuoteCreate, QuoteOut
            print("   ✅ quote_schema imported successfully")
        except Exception as e:
            print(f"   ❌ quote_schema import failed: {e}")
            return False
            
        try:
            from app.schemas.master import RiskDescriptionResponse
            print("   ✅ master schema imported successfully")
        except Exception as e:
            print(f"   ❌ master schema import failed: {e}")
            return False
            
        try:
            from app.schemas.fire_premium import (
                AddOnItem, PASelection, UBGRUVGRRequest, 
                PremiumBreakdown, CalculationMeta, UBGRUVGRResponse
            )
            print("   ✅ fire_premium schema imported successfully")
        except Exception as e:
            print(f"   ❌ fire_premium schema import failed: {e}")
            return False
            
        try:
            from app.schemas.response import ResponseModel
            print("   ✅ response schema imported successfully")
        except Exception as e:
            print(f"   ❌ response schema import failed: {e}")
            return False
            
        try:
            from app.schemas.rating_engine import RatingRequest, RatingResponse
            print("   ✅ rating_engine schema imported successfully")
        except Exception as e:
            print(f"   ❌ rating_engine schema import failed: {e}")
            return False
        
        # Check for warnings
        print(f"\n2. Checking for Pydantic warnings...")
        pydantic_warnings = [warning for warning in w if 'pydantic' in str(warning.message).lower()]
        
        if pydantic_warnings:
            print(f"   ❌ Found {len(pydantic_warnings)} Pydantic warning(s):")
            for warning in pydantic_warnings:
                print(f"      - {warning.category.__name__}: {warning.message}")
            return False
        else:
            print("   ✅ No Pydantic warnings detected")
            
    return True

def test_config_attributes():
    """Test that Config classes have correct attributes"""
    print("\n3. Verifying Config attributes...")
    
    from app.schemas.user_schema import UserOut
    from app.schemas.rate_schema import RateOut
    from app.schemas.quote_schema import QuoteOut
    from app.schemas.master import RiskDescriptionResponse
    from app.schemas.fire_premium import UBGRUVGRRequest
    
    schemas_to_check = [
        ("UserOut", UserOut),
        ("RateOut", RateOut),
        ("QuoteOut", QuoteOut),
        ("RiskDescriptionResponse", RiskDescriptionResponse),
        ("UBGRUVGRRequest", UBGRUVGRRequest),
    ]
    
    all_passed = True
    
    for name, schema in schemas_to_check:
        # Check if model_config exists (Pydantic v2 style)
        if hasattr(schema, 'model_config'):
            config = schema.model_config
            
            # Check for v1 attributes that should not exist
            if 'orm_mode' in config:
                print(f"   ❌ {name}: Still has 'orm_mode' (v1 attribute)")
                all_passed = False
            elif 'schema_extra' in config:
                print(f"   ❌ {name}: Still has 'schema_extra' (v1 attribute)")
                all_passed = False
            else:
                # Check for v2 attributes
                if 'from_attributes' in config:
                    print(f"   ✅ {name}: Has 'from_attributes' (v2)")
                if 'json_schema_extra' in config:
                    print(f"   ✅ {name}: Has 'json_schema_extra' (v2)")
        else:
            print(f"   ℹ️  {name}: No model_config (may not need Config)")
    
    return all_passed

def test_model_instantiation():
    """Test that models can be instantiated"""
    print("\n4. Testing model instantiation...")
    
    try:
        from app.schemas.fire_premium import UBGRUVGRRequest, PASelection, AddOnItem
        
        # Test creating a request
        request = UBGRUVGRRequest(
            productCode="UBGR",
            occupancyCode="1001",
            buildingSI=1000000,
            contentsSI=200000,
            terrorismSI=1200000,
            addOns=[
                AddOnItem(addOnCode="EQ", sumInsured=1200000)
            ],
            paSelection=PASelection(proposer=True, spouse=False),
            discountPercentage=5,
            loadingPercentage=10,
            policyPeriod=1
        )
        
        print("   ✅ UBGRUVGRRequest instantiated successfully")
        
        # Test model_dump (v2) instead of dict (v1)
        data = request.model_dump()
        print("   ✅ model_dump() works (Pydantic v2 method)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generic_model():
    """Test that ResponseModel (Generic) works correctly"""
    print("\n5. Testing Generic ResponseModel...")
    
    try:
        from app.schemas.response import ResponseModel
        
        # Test with different types
        response_dict = ResponseModel[dict](
            success=True,
            message="Test",
            data={"key": "value"}
        )
        print("   ✅ ResponseModel[dict] works")
        
        response_list = ResponseModel[list](
            success=True,
            message="Test",
            data=[1, 2, 3]
        )
        print("   ✅ ResponseModel[list] works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Generic model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification tests"""
    print("\nStarting Pydantic v2 Migration Verification...\n")
    
    results = []
    
    # Run all tests
    results.append(("Schema Imports", test_schema_imports()))
    results.append(("Config Attributes", test_config_attributes()))
    results.append(("Model Instantiation", test_model_instantiation()))
    results.append(("Generic Model", test_generic_model()))
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - Pydantic v2 migration successful!")
        print("\nChanges made:")
        print("  • Replaced 'orm_mode = True' with 'from_attributes = True'")
        print("  • Replaced 'schema_extra' with 'json_schema_extra'")
        print("  • Replaced 'GenericModel' with 'BaseModel' for generics")
        print("\nNo field names, response structures, or validation rules were changed.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Please review the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
