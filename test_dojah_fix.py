#!/usr/bin/env python3
"""
DOJAH KYC FIX VERIFICATION SCRIPT
Tests that the fixes are properly applied
"""

import os
import sys

# Add Django project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from backend.apps.hr.models.employee import EmployeeProfile
from backend.apps.hr.services.kyc import get_kyc_provider

def test_database_fields():
    """Test that statutory fields exist in EmployeeProfile model"""
    print("\n" + "="*60)
    print("TEST 1: DATABASE SCHEMA VERIFICATION")
    print("="*60)
    
    required_fields = ['nhf_number', 'nhis_number', 'nsitf_number']
    model_fields = [f.name for f in EmployeeProfile._meta.get_fields()]
    
    for field in required_fields:
        if field in model_fields:
            print(f"✅ {field:20} → EXISTS")
        else:
            print(f"❌ {field:20} → MISSING")
            return False
    
    print("\n✅ All statutory fields present in database schema")
    return True

def test_kyc_provider():
    """Test KYC provider selection logic"""
    print("\n" + "="*60)
    print("TEST 2: KYC PROVIDER SELECTION")
    print("="*60)
    
    provider = get_kyc_provider()
    provider_name = provider.__class__.__name__
    
    print(f"Current Provider: {provider_name}")
    
    if provider_name == "SandboxKYCProvider":
        print("⚠️  SANDBOX MODE: Using demo data (Natasha Romanoff)")
        print("   To enable LIVE mode:")
        print("   1. Add DOJAH_API_KEY to backend/.env")
        print("   2. Add DOJAH_APP_ID to backend/.env")
        print("   3. Restart Django server")
    elif provider_name == "DojahKYCProvider":
        print("✅ PRODUCTION MODE: Using real Dojah API")
        print("   Real Nigerian NIMC/BVN data will be returned")
    else:
        print(f"❌ UNKNOWN PROVIDER: {provider_name}")
        return False
    
    return True

def test_provider_response_structure():
    """Test that provider returns correct data structure"""
    print("\n" + "="*60)
    print("TEST 3: API RESPONSE STRUCTURE")
    print("="*60)
    
    provider = get_kyc_provider()
    
    # Test with valid 11-digit NIN
    test_nin = "12345678901"
    response = provider.verify_nin(test_nin)
    
    print(f"Test NIN: {test_nin}")
    print(f"Response Keys: {list(response.keys())}")
    
    required_keys = ['status', 'is_verified', 'provider', 'data']
    for key in required_keys:
        if key in response:
            print(f"✅ {key:15} → Present")
        else:
            print(f"❌ {key:15} → MISSING")
            return False
    
    # Check data structure
    if 'data' in response and response['data']:
        data_keys = list(response['data'].keys())
        print(f"\nData Keys: {data_keys}")
        
        expected_data_keys = ['full_name', 'dob', 'timestamp']
        for key in expected_data_keys:
            if key in data_keys:
                print(f"✅ data.{key:12} → Present")
            else:
                print(f"❌ data.{key:12} → MISSING")
    
    print(f"\n📊 Sample Response:")
    print(f"   Provider: {response.get('provider')}")
    print(f"   Verified: {response.get('is_verified')}")
    print(f"   Full Name: {response.get('data', {}).get('full_name', 'N/A')}")
    print(f"   DOB: {response.get('data', {}).get('dob', 'N/A')}")
    print(f"   Timestamp: {response.get('data', {}).get('timestamp', 'N/A')}")
    
    return True

def main():
    print("\n" + "="*60)
    print("DOJAH KYC FIX VERIFICATION SCRIPT")
    print("="*60)
    print("This script verifies that all fixes have been applied correctly")
    
    tests = [
        ("Database Schema", test_database_fields),
        ("KYC Provider Selection", test_kyc_provider),
        ("API Response Structure", test_provider_response_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nNext Steps:")
        print("1. Add Dojah production credentials to backend/.env")
        print("2. Restart Django server")
        print("3. Test KYC verification in browser")
        print("4. Verify real data appears (not 'Natasha Romanoff')")
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the error messages above")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
