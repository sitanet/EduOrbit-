from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, StudentProfile
from backend.apps.clinic.models import PatientProfile, ClinicVisit
from backend.apps.clinic.services.medical import MedicalRecordService, ClinicVisitService, MedicationService, SickBayService, VaccinationService

class ClinicV240TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Clinic Tenant")
        self.school = School.objects.create(tenant=self.tenant, name="St. Jude International School")
        self.person = Person.objects.create(
            tenant=self.tenant, person_number="PER-MED-001", first_name="Florence", last_name="Nightingale", date_of_birth="1998-05-12", gender="female"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.person, student_number="STU-MED-001", admission_number="ADM-MED-001", current_school=self.school
        )
        self.client = APIClient()

    def test_clinic_medical_services(self):
        # 1. Register Patient Medical Record
        reg_res = MedicalRecordService.register_patient(person=self.person, blood_group="A+", allergies="Penicillin", chronic_conditions="Asthma")
        self.assertEqual(reg_res["status"], "success")

        patient = PatientProfile.objects.get(id=reg_res["patient_id"])

        # 2. Record Clinic Visit
        visit_res = ClinicVisitService.record_visit(patient=patient, symptoms="Mild Fever and Headache", diagnosis="Acute Malaria", status="completed")
        self.assertEqual(visit_res["status"], "success")

        visit = ClinicVisit.objects.get(id=visit_res["visit_id"])

        # 3. Prescribe & Dispense Medication
        med_res = MedicationService.prescribe_drug(visit=visit, drug_name="Paracetamol 500mg", dosage="2 tablets 3x daily")
        self.assertEqual(med_res["status"], "success")

        # 4. Sick Bay Admission & Discharge
        adm_res = SickBayService.admit_patient(patient=patient, ward_name="Female Ward", bed_number="BED-04")
        self.assertEqual(adm_res["status"], "success")

        # 5. Immunization & Vaccination Record
        vac_res = VaccinationService.record_vaccination(patient=patient, vaccine_name="Hepatitis B Booster")
        self.assertEqual(vac_res["status"], "success")

    def test_clinic_api_endpoints(self):
        reg_res = MedicalRecordService.register_patient(person=self.person, blood_group="O+", allergies="None")
        patient_id = reg_res["patient_id"]

        # 1. Patient Records API
        rec_url = '/clinic/api/v1/records/'
        rec_resp = self.client.get(rec_url)
        self.assertEqual(rec_resp.status_code, status.HTTP_200_OK)

        # 2. Clinic Visit Creation API
        create_vst_url = '/clinic/api/v1/visits/create/'
        payload = {
            "patient_id": patient_id,
            "symptoms": "Seasonal Allergy Cough",
            "diagnosis": "Allergic Rhinitis"
        }
        vst_resp = self.client.post(create_vst_url, payload, format='json')
        self.assertEqual(vst_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(vst_resp.data["status"], "success")
