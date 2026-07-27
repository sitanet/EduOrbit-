import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from backend.apps.inventory.models import AssetCategory, Asset, AssetDepreciation
from backend.apps.efbm.services.accounting import JournalPostingService
from backend.apps.core.services.notifications import UnifiedNotificationService

class AssetRegistrationService:
    """
    Enterprise Asset Registration & Capitalization Engine.
    """
    @classmethod
    @transaction.atomic
    def register_asset(cls, school, category, name, purchase_cost, useful_life_years=5):
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
            useful_life_years=useful_life_years
        )

        # Capitalize Asset in GL (Debit Fixed Asset, Credit Cash/Accounts Payable)
        JournalPostingService.post_journal_entry(
            school=school,
            event_type="asset_capitalization",
            debit_account=f"Fixed Assets ({category.name})",
            credit_account="Accounts Payable (Equipment Vendor)",
            amount=cost
        )

        # Send Asset Creation Alert
        UnifiedNotificationService.send_notification(
            recipient="Asset Manager",
            title="Capital Asset Registered",
            message=f"Fixed Asset #{asset.asset_number} ({name}) registered and capitalized for ${cost}.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "asset_id": str(asset.id),
            "asset_number": asset.asset_number,
            "name": asset.name,
            "purchase_cost": float(asset.purchase_cost),
            "useful_life_years": asset.useful_life_years
        }


class DepreciationService:
    """
    Automated Straight-Line Depreciation Engine with General Ledger Integration.
    """
    @classmethod
    @transaction.atomic
    def run_monthly_depreciation(cls, school, asset):
        tenant = school.tenant
        
        # Monthly straight-line calculation: Annual / 12
        annual_depr = Decimal(str(asset.purchase_cost)) / Decimal(str(asset.useful_life_years))
        monthly_depr = round(annual_depr / Decimal('12.0'), 2)

        if asset.current_value <= Decimal('0.00'):
            return {
                "status": "warning",
                "message": f"Asset #{asset.asset_number} is fully depreciated."
            }

        depr_amount = min(monthly_depr, asset.current_value)

        # Update current value
        asset.current_value -= depr_amount
        asset.save()

        # Record Depreciation Audit Log
        depr_log = AssetDepreciation.objects.create(
            tenant=tenant,
            asset=asset,
            calculation_date=timezone.now().date(),
            depreciation_amount=depr_amount
        )

        # GL Accounting Post (Debit Depreciation Expense, Credit Accumulated Depreciation)
        JournalPostingService.post_journal_entry(
            school=school,
            event_type="asset_depreciation",
            debit_account="Depreciation Expense",
            credit_account=f"Accumulated Depreciation ({asset.category.name})",
            amount=depr_amount
        )

        return {
            "status": "success",
            "asset_number": asset.asset_number,
            "monthly_depreciation": float(depr_amount),
            "new_book_value": float(asset.current_value),
            "depreciation_id": str(depr_log.id)
        }
