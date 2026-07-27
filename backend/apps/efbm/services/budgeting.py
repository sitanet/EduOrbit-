from decimal import Decimal
from django.db import transaction
from backend.apps.efbm.models import Budget, BudgetItem
from backend.apps.core.services.notifications import UnifiedNotificationService

class BudgetService:
    """
    Enterprise Financial Budgeting & Planning Engine.
    """
    @classmethod
    @transaction.atomic
    def create_budget(cls, school, academic_year, name, items_list):
        tenant = school.tenant

        budget = Budget.objects.create(
            tenant=tenant,
            school=school,
            academic_year=academic_year,
            name=name,
            status='draft'
        )

        total_alloc = Decimal('0.00')

        for item_data in items_list:
            amt = Decimal(str(item_data.get('allocated_amount', 0.00)))
            BudgetItem.objects.create(
                tenant=tenant,
                budget=budget,
                category_name=item_data.get('category_name', 'General Operating'),
                allocated_amount=amt
            )
            total_alloc += amt

        budget.total_allocated = total_alloc
        budget.save()

        return {
            "status": "success",
            "budget_id": str(budget.id),
            "name": budget.name,
            "total_allocated": float(total_alloc),
            "status_name": budget.status
        }

    @classmethod
    @transaction.atomic
    def approve_budget(cls, budget):
        budget.status = 'approved'
        budget.save()

        UnifiedNotificationService.send_notification(
            recipient="Finance Director",
            title="Budget Approved",
            message=f"Annual Budget '{budget.name}' (${budget.total_allocated}) has been officially approved and activated.",
            channels=['in_app', 'email']
        )

        return {
            "status": "success",
            "budget_id": str(budget.id),
            "name": budget.name,
            "status_name": budget.status
        }


class BudgetControlService:
    """
    Real-Time Budget Control & Over-Budget Prevention Engine.
    """
    @classmethod
    @transaction.atomic
    def reserve_commitment(cls, budget_item, amount):
        amt = Decimal(str(amount))
        available = budget_item.allocated_amount - (budget_item.committed_amount + budget_item.spent_amount)

        if amt > available:
            return {
                "status": "error",
                "message": f"Hard Budget Stop: Requested ${amt} exceeds available balance ${available} for {budget_item.category_name}."
            }

        budget_item.committed_amount += amt
        budget_item.save()

        # Update Parent Budget Summary
        budget = budget_item.budget
        budget.total_committed += amt
        budget.save()

        return {
            "status": "success",
            "category_name": budget_item.category_name,
            "committed_amount": float(amt),
            "remaining_available": float(budget_item.allocated_amount - (budget_item.committed_amount + budget_item.spent_amount))
        }

    @classmethod
    @transaction.atomic
    def record_actual_expense(cls, budget_item, amount):
        amt = Decimal(str(amount))

        # Convert commitment to spent
        if budget_item.committed_amount >= amt:
            budget_item.committed_amount -= amt
            budget_item.budget.total_committed -= amt

        budget_item.spent_amount += amt
        budget_item.save()

        budget = budget_item.budget
        budget.total_spent += amt
        budget.save()

        return {
            "status": "success",
            "category_name": budget_item.category_name,
            "spent_amount": float(amt),
            "remaining_available": float(budget_item.allocated_amount - (budget_item.committed_amount + budget_item.spent_amount))
        }

    @classmethod
    def get_budget_utilization(cls, budget):
        total_alloc = budget.total_allocated or Decimal('1.00')
        total_used = budget.total_spent + budget.total_committed
        utilization_pct = round(float((total_used / total_alloc) * Decimal('100.0')), 2)

        items_breakdown = []
        for item in budget.items.all():
            avail = item.allocated_amount - (item.committed_amount + item.spent_amount)
            items_breakdown.append({
                "category_name": item.category_name,
                "allocated": float(item.allocated_amount),
                "committed": float(item.committed_amount),
                "spent": float(item.spent_amount),
                "available": float(avail)
            })

        return {
            "budget_name": budget.name,
            "total_allocated": float(budget.total_allocated),
            "total_committed": float(budget.total_committed),
            "total_spent": float(budget.total_spent),
            "total_available": float(budget.total_allocated - total_used),
            "utilization_percentage": utilization_pct,
            "items": items_breakdown
        }
