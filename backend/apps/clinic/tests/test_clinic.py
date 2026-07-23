from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person
from backend.apps.clinic.models import (
    Clinic, PatientProfile, Appointment, ClinicVisit, Drug, DrugBatch, Prescription, Ward, SickBayAdmission, Vaccination
)

class ClinicPlatformTests(TestCase):
    def setUp(self):
        # Create core configurations
        self.tenant = Tenant.objects.create(name="ECHM Org")
        self.school = School.objects.create(tenant=self.tenant, name="ECHM Sickbay School", school_types=["secondary"])
        
        # Student Person profile
        self.student = Person.objects.create(
            tenant=self.tenant,
            person_number="P-99001",
            first_name="Hermione",
            last_name="Granger",
            gender="female",
            date_of_birth="2011-09-19"
        )
        
        self.patient = PatientProfile.objects.create(
            person=self.student,
            tenant=self.tenant,
            blood_group="O+",
            allergies="Sneezewort",
            chronic_conditions="None"
        )
        
        # Pharmacy Drugs
        self.drug = Drug.objects.create(tenant=self.tenant, name="Pepperup Potion", stock_qty=50)
        self.batch = DrugBatch.objects.create(
            drug=self.drug,
            tenant=self.tenant,
            batch_number="BCH-990",
            expiry_date=date.today() + timedelta(days=365)
        )
        
        # Ward
        self.ward = Ward.objects.create(tenant=self.tenant, name="Main Sick Bay Ward")

    def test_clinic_visit_triage_flow(self):
        visit = ClinicVisit.objects.create(
            patient=self.patient,
            tenant=self.tenant,
            symptoms="High fever after casting spells",
            diagnosis="Common magical cold",
            status="completed"
        )
        self.assertEqual(visit.status, "completed")
        
        # Issue prescription
        presc = Prescription.objects.create(
            visit=visit,
            drug=self.drug,
            tenant=self.tenant,
            dosage="2 drops daily"
        )
        self.assertEqual(presc.drug.name, "Pepperup Potion")

    def test_sickbay_admission_occupancy(self):
        adm = SickBayAdmission.objects.create(
            patient=self.patient,
            ward=self.ward,
            tenant=self.tenant,
            bed_number="Bed-3",
            admitted_at=timezone.now()
        )
        self.assertEqual(adm.bed_number, "Bed-3")
        self.assertNil = adm.discharged_at
        
        # Discharge
        adm.discharged_at = timezone.now()
        adm.save()
        self.assertIsNotNone(adm.discharged_at)

    def test_vaccination_administration(self):
        vac = Vaccination.objects.create(
            patient=self.patient,
            tenant=self.tenant,
            vaccine_name="Dragon Pox Immunization",
            administered_date=date.today()
        )
        self.assertEqual(vac.vaccine_name, "Dragon Pox Immunization")
