from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from backend.apps.efbm.models import Budget, BudgetItem


class BudgetManagementService:
    """
    Enterprise Budget Management Service for EduOrbit ERP.
    Handles Annual & Department Budgets, Approval Workflows, Budget Revisions,
    Budget vs. Actual Variance Analysis, Forecast Dashboards, and Financial Control Metrics.
    """

    @classmethod
    def get_budgets(cls, tenant, academic_year_id=None, status=None):
        """
        Retrieves annual and department budgets.
        """
        budgets = Budget.objects.prefetch_related('items').all()
        if tenant:
            budgets = budgets.filter(tenant=tenant)
        if academic_year_id:
            budgets = budgets.filter(academic_year_id=academic_year_id)
        if status:
            budgets = budgets.filter(status=status)
        return budgets.order_by('-created_at')

    @classmethod
    @transaction.atomic
    def approve_budget(cls, budget_id, user=None):
        """
        Approves a draft or submitted budget for fiscal allocation execution.
        """
        budget = Budget.objects.get(id=budget_id)
        if budget.status in ['draft', 'submitted']:
            budget.status = 'approved'
            budget.save()
        return budget

    @classmethod
    @transaction.atomic
    def revise_budget(cls, budget_id, revision_items=None, user=None):
        """
        Revises a budget by adjusting item allocations and updating totals inside an atomic transaction.
        revision_items: list of dicts [{'item_id': id, 'new_allocated': amount}]
        """
        budget = Budget.objects.get(id=budget_id)
        
        if revision_items:
            for rev in revision_items:
                item = BudgetItem.objects.get(id=rev['item_id'], budget=budget)
                item.allocated_amount = Decimal(str(rev['new_allocated']))
                item.save()

        # Recalculate total allocated
        tot = budget.items.aggregate(tot=Sum('allocated_amount'))['tot'] or Decimal('0.00')
        budget.total_allocated = tot
        budget.save()

        return budget

    @classmethod
    def get_budget_vs_actual_report(cls, budget_id):
        """
        Generates Budget vs. Actual Variance Analysis for a specific budget.
        Variance = Allocated - Spent
        Favorable if Spent <= Allocated, Unfavorable if Spent > Allocated.
        """
        budget = Budget.objects.prefetch_related('items').get(id=budget_id)
        
        items = []
        total_allocated = Decimal('0.00')
        total_spent = Decimal('0.00')
        total_variance = Decimal('0.00')

        for item in budget.items.all():
            allocated = item.allocated_amount
            spent = item.spent_amount
            variance = allocated - spent
            variance_pct = round(((variance / allocated) * 100), 2) if allocated > 0 else Decimal('0.00')
            status = 'Favorable' if spent <= allocated else 'Unfavorable'

            items.append({
                'id': item.id,
                'category_name': item.category_name,
                'allocated_amount': allocated,
                'spent_amount': spent,
                'variance_amount': variance,
                'variance_pct': variance_pct,
                'status': status
            })

            total_allocated += allocated
            total_spent += spent
            total_variance += variance

        overall_pct = round(((total_spent / total_allocated) * 100), 2) if total_allocated > 0 else Decimal('0.00')

        return {
            'budget': budget,
            'items': items,
            'total_allocated': total_allocated,
            'total_spent': total_spent,
            'total_variance': total_variance,
            'consumption_pct': overall_pct
        }

    @classmethod
    def get_budget_forecast_dashboard(cls, tenant):
        """
        Live database metrics for Budget Forecast & Variance Dashboard.
        """
        budgets = cls.get_budgets(tenant=tenant)
        
        total_allocated = sum(b.total_allocated for b in budgets)
        total_spent = sum(b.total_spent for b in budgets)
        total_remaining = total_allocated - total_spent
        overall_consumption_pct = round(((total_spent / total_allocated) * 100), 2) if total_allocated > 0 else Decimal('0.00')

        approved_count = len([b for b in budgets if b.status == 'approved'])
        pending_count = len([b for b in budgets if b.status in ['draft', 'submitted']])

        return {
            'total_allocated': total_allocated,
            'total_spent': total_spent,
            'total_remaining': total_remaining,
            'overall_consumption_pct': overall_consumption_pct,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'budgets': budgets
        }


class BudgetService:
    """
    API compatibility service for Budget lifecycle management.
    """
    @classmethod
    @transaction.atomic
    def create_budget(cls, school, academic_year, name, items_list=None):
        budget = Budget.objects.create(
            tenant=school.tenant,
            school=school,
            academic_year=academic_year,
            name=name,
            status='draft'
        )
        total = Decimal('0.00')
        if items_list:
            for item in items_list:
                amt = Decimal(str(item.get('allocated_amount', '0.00')))
                BudgetItem.objects.create(
                    tenant=school.tenant,
                    budget=budget,
                    category_name=item.get('category_name', 'General'),
                    allocated_amount=amt
                )
                total += amt

        budget.total_allocated = total
        budget.save()
        return {'id': str(budget.id), 'name': budget.name, 'total_allocated': str(total)}

    @classmethod
    @transaction.atomic
    def submit_budget(cls, budget_id):
        budget = Budget.objects.get(id=budget_id)
        budget.status = 'submitted'
        budget.save()
        return {'id': str(budget.id), 'status': budget.status}

    @classmethod
    @transaction.atomic
    def approve_budget(cls, budget_id, user=None):
        return BudgetManagementService.approve_budget(budget_id=budget_id, user=user)

    @classmethod
    @transaction.atomic
    def freeze_budget(cls, budget_id):
        budget = Budget.objects.get(id=budget_id)
        budget.status = 'frozen'
        budget.save()
        return {'id': str(budget.id), 'status': budget.status}


class BudgetControlService:
    """
    API compatibility service for Budget expenditure control.
    """
    @classmethod
    @transaction.atomic
    def commit_expense(cls, budget_id, category_name, amount):
        budget = Budget.objects.get(id=budget_id)
        item = BudgetItem.objects.filter(budget=budget, category_name__icontains=category_name).first()
        amt = Decimal(str(amount))
        if item:
            item.committed_amount += amt
            item.save()
        budget.total_committed += amt
        budget.save()
        return {'budget_id': str(budget.id), 'committed': str(budget.total_committed)}

    @classmethod
    @transaction.atomic
    def spend_expense(cls, budget_id, category_name, amount):
        budget = Budget.objects.get(id=budget_id)
        item = BudgetItem.objects.filter(budget=budget, category_name__icontains=category_name).first()
        amt = Decimal(str(amount))
        if item:
            item.spent_amount += amt
            item.save()
        budget.total_spent += amt
        budget.save()
        return {'budget_id': str(budget.id), 'spent': str(budget.total_spent)}

