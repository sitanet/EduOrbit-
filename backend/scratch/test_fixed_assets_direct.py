import os
import sys
import django

sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
django.setup()

from decimal import Decimal
from backend.apps.tenants.models import Tenant, School
from backend.apps.inventory.models import AssetCategory, Asset
from backend.apps.inventory.services.assets import (
    AssetRegistrationService, DepreciationService, AssetLifecycleService
)

def run_tests():
    print("--- Running Fixed Assets Direct Verification ---")

    tenant = Tenant.objects.first() or Tenant.objects.create(name="Asset Tenant Direct")
    school = School.objects.filter(tenant=tenant).first() or School.objects.create(tenant=tenant, name="Academy High")

    category = AssetCategory.objects.create(tenant=tenant, name="IT Hardware")

    # 1. Test Asset Registration
    asset = AssetRegistrationService.register_asset(
        school=school,
        category=category,
        name="Dell PowerEdge Server R750",
        purchase_cost=Decimal("12000.00"),
        useful_life_years=5,
        location="Data Center A"
    )
    assert asset.current_value == Decimal("12000.00"), "Asset registration current value mismatch!"
    print(f"[PASS] Asset Registration Verified. Asset #: {asset.asset_number}, Cost: ${asset.purchase_cost}")

    # 2. Test Straight Line Depreciation
    sl_res = DepreciationService.run_straight_line_depreciation(asset=asset)
    assert sl_res['status'] == "success", "Straight line depreciation failure!"
    assert asset.current_value < Decimal("12000.00"), "Straight line book value update failure!"
    print(f"[PASS] Straight Line Depreciation Verified. Monthly Depr: ${sl_res['depreciation_amount']}, New Book Value: ${sl_res['new_book_value']}")

    # 3. Test Reducing Balance Depreciation
    rb_res = DepreciationService.run_reducing_balance_depreciation(asset=asset, rate_pct=20)
    assert rb_res['status'] == "success", "Reducing balance depreciation failure!"
    print(f"[PASS] Reducing Balance Depreciation (20%) Verified. Monthly Depr: ${rb_res['depreciation_amount']}, New Book Value: ${rb_res['new_book_value']}")

    # 4. Test Asset Transfer
    transferred = AssetLifecycleService.transfer_asset(asset_id=asset.id, new_location="Campus B Server Room")
    assert transferred.location == "Campus B Server Room", "Asset transfer location mismatch!"
    assert transferred.status == "transferred", "Asset transfer status mismatch!"
    print(f"[PASS] Asset Transfer Verified. New Location: {transferred.location}")

    # 5. Test Asset Maintenance Record
    maint = AssetLifecycleService.record_maintenance(asset_id=asset.id, description="Annual RAID Controller Firmware Upgrade")
    asset.refresh_from_db()
    assert asset.status == "under_maintenance", "Asset maintenance status update failure!"
    print(f"[PASS] Asset Maintenance Record Verified. Status: {asset.status}")

    # 6. Test Asset Disposal
    disposed = AssetLifecycleService.dispose_asset(asset_id=asset.id, disposal_proceeds=5000)
    assert disposed.status == "disposed", "Asset disposal status mismatch!"
    assert disposed.current_value == Decimal("0.00"), "Asset disposal book value zeroing mismatch!"
    print(f"[PASS] Asset Disposal Verified. Status: {disposed.status}, Book Value: ${disposed.current_value}")

    # 7. Test Depreciation Summary Report
    report = AssetLifecycleService.get_depreciation_report(tenant=tenant)
    assert report['total_cost'] >= Decimal("12000.00"), "Depreciation report cost mismatch!"
    print(f"[PASS] Depreciation Summary Report Verified. Total Cost: ${report['total_cost']}, Total Accum Depr: ${report['total_accumulated_depreciation']}")

    print("--- ALL FIXED ASSETS VERIFICATION TESTS PASSED CLEANLY! ---")

if __name__ == "__main__":
    run_tests()
