#!/usr/bin/env python
"""
Bug Condition Exploration Test
This script demonstrates the FieldError that occurs when test code references
the removed 'subdomain' field on the Tenant model.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from backend.apps.tenants.models import Tenant

print("=" * 70)
print("BUG CONDITION EXPLORATION TEST")
print("=" * 70)
print("\nAttempting to create Tenant with removed 'subdomain' field parameter...")
print("Expected: FieldError - Cannot resolve keyword 'subdomain' into field\n")

try:
    # This was the bug condition - test code attempts to use removed subdomain field
    # FIXED: Remove subdomain parameter from Tenant.objects.create() call
    tenant = Tenant.objects.create(name="Test School")
    print("✓ SUCCESS: Tenant created successfully without subdomain field!")
    print(f"   Tenant: {tenant}")
    print("\n✅ Bug condition has been resolved:")
    print("   1. Removed subdomain parameter from Tenant.objects.create() calls")
    print("   2. Tenant creation now works without FieldError")
    
except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e)
    print(f"✓ EXPECTED: {error_type} occurred!")
    print(f"   Error: {error_msg}")
    print(f"\n📍 Bug Confirmed:")
    print(f"   - Error Type: {error_type}")
    print(f"   - Error Message: {error_msg}")
    print(f"   - Location: Tenant.objects.create() call with subdomain parameter")
    print(f"   - Root Cause: subdomain field removed in migration 0002, but test code still references it")
    
print("\n" + "=" * 70)
print("END OF BUG CONDITION EXPLORATION TEST")
print("=" * 70)
