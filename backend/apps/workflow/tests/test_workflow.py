from django.test import TestCase
from django.utils import timezone
import uuid
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.workflow.models import (
    WorkflowDefinition, WorkflowVersion, WorkflowStep, WorkflowInstance, WorkflowTask, WorkflowApproval, ApprovalDelegation, Document, DocumentVersion
)

class WorkflowPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="EWDAE Org")
        self.school = School.objects.create(tenant=self.tenant, name="EWDAE Grammar School", school_types=["secondary"])
        
        # Staff Person profile
        self.staff_person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-202001",
            first_name="Winston",
            last_name="Smith",
            gender="male",
            date_of_birth="1984-04-04"
        )
        
        self.delegate_person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-202002",
            first_name="Julia",
            last_name="Dix",
            gender="female",
            date_of_birth="1988-08-08"
        )
        
        # Definitions & versioning
        self.definition = WorkflowDefinition.objects.create(
            tenant=self.tenant,
            name="Purchase Requisition Workflow",
            trigger_event="purchase.request.created"
        )
        self.version = WorkflowVersion.objects.create(
            workflow=self.definition,
            tenant=self.tenant,
            version_number=1,
            is_published=True
        )
        self.step = WorkflowStep.objects.create(
            version=self.version,
            tenant=self.tenant,
            step_order=1,
            role_required="FinanceManager"
        )
        
        # Instances
        self.instance = WorkflowInstance.objects.create(
            version=self.version,
            tenant=self.tenant,
            target_id=uuid.uuid4(),
            status="in_progress"
        )

    def test_workflow_step_task_transitions(self):
        task = WorkflowTask.objects.create(
            instance=self.instance,
            step=self.step,
            tenant=self.tenant,
            assigned_role="FinanceManager",
            is_completed=False
        )
        self.assertFalse(task.is_completed)
        
        # Approve task
        approval = WorkflowApproval.objects.create(
            task=task,
            approver=self.staff_person,
            tenant=self.tenant,
            decision="approve",
            comments="Looks within budget limit"
        )
        task.is_completed = True
        task.save()
        self.assertTrue(task.is_completed)
        self.assertEqual(approval.decision, "approve")

    def test_approval_delegates_mapping(self):
        delg = ApprovalDelegation.objects.create(
            original_approver=self.staff_person,
            delegated_approver=self.delegate_person,
            tenant=self.tenant,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5)
        )
        self.assertEqual(delg.delegated_approver.person_number, "P-202002")

    def test_document_versions_audits(self):
        doc = Document.objects.create(
            tenant=self.tenant,
            name="Q3 Budget Spreadsheet",
            file_path="spaces/q3_budget.xlsx"
        )
        v1 = DocumentVersion.objects.create(
            document=doc,
            tenant=self.tenant,
            version_number=1
        )
        self.assertEqual(v1.version_number, 1)
