from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.inventory.models import AssetCategory, Asset
from backend.apps.inventory.services.assets import AssetRegistrationService, DepreciationService

class AssetRelease4TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Asset Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="Metropolis Tech Institute")
        self.category = AssetCategory.objects.create(tenant=self.tenant, name="IT Hardware")
        self.client = APIClient()

    def test_asset_registration_and_depreciation(self):
        # 1. Register Asset (Capitalization GL Journal entry)
        reg_res = AssetRegistrationService.register_asset(
            school=self.school,
            category=self.category,
            name="High Performance Server Rack",
            purchase_cost=12000.00,
            useful_life_years=5
        )
        self.assertEqual(reg_res["status"], "success")
        self.assertTrue(reg_res["asset_number"].startswith("AST-"))
        asset = Asset.objects.get(id=reg_res["asset_id"])

        # 2. Run Monthly Depreciation (Updates book value & posts GL Journal entry)
        depr_res = DepreciationService.run_monthly_depreciation(school=self.school, asset=asset)
        self.assertEqual(depr_res["status"], "success")
        self.assertEqual(depr_res["monthly_depreciation"], 200.00)
        self.assertEqual(depr_res["new_book_value"], 11800.00)

    def test_asset_api_endpoints(self):
        # 1. Register Asset API
        reg_url = '/inventory/api/v1/assets/register/'
        payload = {
            "school_id": str(self.school.id),
            "category_id": str(self.category.id),
            "name": "Smart Interactive Board",
            "purchase_cost": 3600.00,
            "useful_life_years": 3
        }
        resp = self.client.post(reg_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        asset_id = resp.data["data"]["asset_id"]

        # 2. Run Depreciation API
        depr_url = '/inventory/api/v1/assets/depreciation/run/'
        depr_payload = {
            "school_id": str(self.school.id),
            "asset_id": asset_id
        }
        depr_resp = self.client.post(depr_url, depr_payload, format='json')
        self.assertEqual(depr_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(depr_resp.data["status"], "success")
        self.assertEqual(depr_resp.data["data"]["monthly_depreciation"], 100.00)
