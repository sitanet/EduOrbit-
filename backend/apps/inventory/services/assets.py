import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.inventory.models import AssetCategory, Asset, AssetDepreciation, AssetMaintenance
from backend.apps.efbm.services.integration import AutomaticAccountingIntegrationService


class AssetRegistrationService:
    """
    Enterprise Asset Registration & Capitalization Engine.
    """
    @classmethod
    @transaction.atomic
    def register_asset(cls, school, category, name, purchase_cost, useful_life_years=5, location="Main Campus"):
        tenant = school.tenant
        cost = Decimal(str(purchase_cost))
        asset_number = f"AST-{category.name[:3].upper()}-{str(uuid.uuid4())[:6].upper()}"

        asset = Asset.objects.create(
            tenant=tenant,
            category=category,
            asset_number=asset_number,
            name=name,
            purchase_cost=cost,
            current_value=cost,
            useful_life_years=useful_life_years,
            location=location,
            status='active'
        )

        return asset


class DepreciationService:
    """
    Enterprise Depreciation Engine supporting Straight Line & Reducing Balance methods.
    """
    @classmethod
    @transaction.atomic
    def run_straight_line_depreciation(cls, asset):
        """
        Straight Line Depreciation calculation: (Purchase Cost / Useful Life Years) / 12 for monthly.
        """
        if asset.current_value <= Decimal('0.00'):
            return {"status": "warning", "message": f"Asset #{asset.asset_number} is fully depreciated."}

        annual_depr = Decimal(str(asset.purchase_cost)) / Decimal(str(asset.useful_life_years))
        monthly_depr = round(annual_depr / Decimal('12.0'), 2)
        depr_amount = min(monthly_depr, asset.current_value)

        asset.current_value -= depr_amount
        asset.save()

        depr_log = AssetDepreciation.objects.create(
            tenant=asset.tenant,
            asset=asset,
            calculation_date=timezone.now().date(),
            depreciation_amount=depr_amount
        )

        return {
            "status": "success",
            "method": "straight_line",
            "depreciation_amount": float(depr_amount),
            "new_book_value": float(asset.current_value)
        }

    @classmethod
    @transaction.atomic
    def run_reducing_balance_depreciation(cls, asset, rate_pct=20):
        """
        Reducing Balance Depreciation calculation: (Current Book Value * Rate %) / 12 for monthly.
        """
        if asset.current_value <= Decimal('0.00'):
            return {"status": "warning", "message": f"Asset #{asset.asset_number} is fully depreciated."}

        rate = Decimal(str(rate_pct)) / Decimal('100.0')
        annual_depr = asset.current_value * rate
        monthly_depr = round(annual_depr / Decimal('12.0'), 2)
        depr_amount = min(monthly_depr, asset.current_value)

        asset.current_value -= depr_amount
        asset.save()

        depr_log = AssetDepreciation.objects.create(
            tenant=asset.tenant,
            asset=asset,
            calculation_date=timezone.now().date(),
            depreciation_amount=depr_amount
        )

        return {
            "status": "success",
            "method": "reducing_balance",
            "rate_pct": rate_pct,
            "depreciation_amount": float(depr_amount),
            "new_book_value": float(asset.current_value)
        }


class AssetLifecycleService:
    """
    Handles Asset Transfers, Disposal (Gain/Loss), Maintenance, History, and Reports.
    """

    @classmethod
    @transaction.atomic
    def transfer_asset(cls, asset_id, new_location):
        """
        Transfers an asset to a new campus location or department.
        """
        asset = Asset.objects.get(id=asset_id)
        asset.location = new_location
        asset.status = 'transferred'
        asset.save()
        return asset

    @classmethod
    @transaction.atomic
    def dispose_asset(cls, asset_id, disposal_proceeds=0):
        """
        Disposes an asset and records GL posting for proceeds/gain/loss.
        """
        asset = Asset.objects.get(id=asset_id)
        proceeds = Decimal(str(disposal_proceeds))

        # Automatic GL posting for asset disposal
        AutomaticAccountingIntegrationService.post_asset_disposal(
            tenant=asset.tenant,
            reference_id=f"DISP-{asset.asset_number}",
            amount=proceeds if proceeds > 0 else asset.current_value
        )

        asset.status = 'disposed'
        asset.current_value = Decimal('0.00')
        asset.save()
        return asset

    @classmethod
    @transaction.atomic
    def record_maintenance(cls, asset_id, description, maintenance_date=None):
        """
        Logs asset maintenance and sets status.
        """
        asset = Asset.objects.get(id=asset_id)
        maint_date = maintenance_date or timezone.now().date()

        record = AssetMaintenance.objects.create(
            tenant=asset.tenant,
            asset=asset,
            description=description,
            maintenance_date=maint_date
        )

        asset.status = 'under_maintenance'
        asset.save()
        return record

    @classmethod
    def get_asset_history(cls, asset_id):
        """
        Itemized history of depreciations and maintenance events for an asset.
        """
        asset = Asset.objects.get(id=asset_id)
        depreciations = asset.depreciations.order_by('-calculation_date')
        maintenance_records = asset.maintenance_records.order_by('-maintenance_date')

        return {
            'asset': asset,
            'depreciations': depreciations,
            'maintenance_records': maintenance_records
        }

    @classmethod
    def get_depreciation_report(cls, tenant):
        """
        Comprehensive depreciation summary across all fixed assets.
        """
        assets = Asset.objects.prefetch_related('depreciations').all()
        if tenant:
            assets = assets.filter(tenant=tenant)

        total_cost = sum(a.purchase_cost for a in assets)
        total_current_val = sum(a.current_value for a in assets)
        total_accumulated_depr = total_cost - total_current_val

        return {
            'assets': assets,
            'total_cost': total_cost,
            'total_current_value': total_current_val,
            'total_accumulated_depreciation': total_accumulated_depr
        }
