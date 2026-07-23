from django.test import TestCase
from django.utils import timezone
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import (
    Person, PersonRole, EmailAddress, PhoneNumber,
    StudentProfile, ParentProfile, FamilyRelationship,
    MedicalProfile, MedicalHistory
)

class PeopleManagementCoreTests(TestCase):
    def setUp(self):
        # Create tenant and schools
        self.tenant = Tenant.objects.create(name="Anchor Org")
        self.school = School.objects.create(tenant=self.tenant, name="Anchor High School", school_types=["secondary"])
        
        # Create Person base record
        self.person = Person.objects.create(
            tenant=self.tenant,
            person_number="P-10001",
            first_name="John",
            last_name="Doe",
            gender="male",
            date_of_birth="2010-05-15"
        )
        
    def test_polymorphic_roles_assignment(self):
        # Assign multiple roles to the same Person (without profile duplication)
        student_role = PersonRole.objects.create(
            tenant=self.tenant,
            person=self.person,
            role="student",
            school=self.school,
            status="active",
            is_primary=True
        )
        
        # Verify PersonRole mapping
        self.assertEqual(self.person.assigned_roles.count(), 1)
        self.assertEqual(self.person.assigned_roles.first().role, "student")
        
    def test_normalized_contact_details(self):
        # Add primary phone
        phone = PhoneNumber.objects.create(
            tenant=self.tenant,
            person=self.person,
            number="+2348011223344",
            is_primary=True,
            is_verified=True
        )
        # Add primary email
        email = EmailAddress.objects.create(
            tenant=self.tenant,
            person=self.person,
            email="johndoe@anchor.com",
            is_primary=True,
            is_verified=False
        )
        
        self.assertEqual(self.person.phones.count(), 1)
        self.assertTrue(self.person.phones.first().is_primary)
        self.assertEqual(self.person.emails.count(), 1)
        self.assertFalse(self.person.emails.first().is_verified)

    def test_medical_profile_and_history(self):
        # Create basic medical profile
        med_profile = MedicalProfile.objects.create(
            tenant=self.tenant,
            person=self.person,
            blood_group="O+",
            genotype="AA"
        )
        
        # Record clinical visit/vaccination history entry
        visit = MedicalHistory.objects.create(
            tenant=self.tenant,
            person=self.person,
            record_type="vaccine",
            name="BCG Vaccine Booster",
            description="Administered booster dose"
        )
        
        self.assertEqual(self.person.medical_profile.blood_group, "O+")
        self.assertEqual(self.person.medical_history.count(), 1)
        self.assertEqual(self.person.medical_history.first().record_type, "vaccine")
