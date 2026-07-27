from django.db import transaction
from django.utils import timezone
from backend.apps.clinic.models import PatientProfile, ClinicVisit, Drug, Prescription, Ward, SickBayAdmission, Vaccination
from backend.apps.core.services.notifications import UnifiedNotificationService

class MedicalRecordService:
    """
    Patient Medical Registry & EHR Engine.
    """
    @classmethod
    @transaction.atomic
    def register_patient(cls, person, blood_group="O+", allergies="None", chronic_conditions="None"):
        tenant = person.tenant
        patient, _ = PatientProfile.objects.get_or_create(
            tenant=tenant,
            person=person,
            defaults={
                'blood_group': blood_group,
                'allergies': allergies,
                'chronic_conditions': chronic_conditions
            }
        )
        return {
            "status": "success",
            "patient_id": str(patient.id),
            "patient_name": f"{person.first_name} {person.last_name}",
            "blood_group": patient.blood_group
        }


class ClinicVisitService:
    """
    Sick Bay Consultation & Triage Consultation Engine.
    """
    @classmethod
    @transaction.atomic
    def record_visit(cls, patient, symptoms, diagnosis="Under Observation", status="completed"):
        tenant = patient.tenant

        visit = ClinicVisit.objects.create(
            tenant=tenant,
            patient=patient,
            symptoms=symptoms,
            diagnosis=diagnosis,
            status=status,
            visit_date=timezone.now()
        )

        # Notify parent/guardian about the clinic visit
        UnifiedNotificationService.send_notification(
            recipient=f"Guardian of {patient.person.first_name}",
            title="Clinic Visit Alert",
            message=f"{patient.person.first_name} {patient.person.last_name} visited the school clinic. Diagnosis: {diagnosis}",
            channels=['in_app', 'email', 'sms']
        )

        return {
            "status": "success",
            "visit_id": str(visit.id),
            "patient_name": f"{patient.person.first_name} {patient.person.last_name}",
            "diagnosis": visit.diagnosis,
            "visit_date": str(visit.visit_date)
        }


class MedicationService:
    """
    Pharmacy & Medication Dispensary Engine.
    """
    @classmethod
    @transaction.atomic
    def prescribe_drug(cls, visit, drug_name, dosage="1 tablet 3x daily"):
        tenant = visit.tenant

        drug, _ = Drug.objects.get_or_create(
            tenant=tenant,
            name=drug_name,
            defaults={'stock_qty': 100}
        )

        prescription = Prescription.objects.create(
            tenant=tenant,
            visit=visit,
            drug=drug,
            dosage=dosage
        )

        if drug.stock_qty > 0:
            drug.stock_qty -= 1
            drug.save()

        return {
            "status": "success",
            "prescription_id": str(prescription.id),
            "drug_name": drug.name,
            "dosage": prescription.dosage,
            "remaining_stock": drug.stock_qty
        }


class SickBayService:
    """
    Sick Bay Admission & In-Patient Management Engine.
    """
    @classmethod
    @transaction.atomic
    def admit_patient(cls, patient, ward_name="General Sickbay Ward", bed_number="BED-01"):
        tenant = patient.tenant

        ward, _ = Ward.objects.get_or_create(
            tenant=tenant,
            name=ward_name
        )

        admission = SickBayAdmission.objects.create(
            tenant=tenant,
            patient=patient,
            ward=ward,
            bed_number=bed_number,
            admitted_at=timezone.now()
        )

        UnifiedNotificationService.send_notification(
            recipient=f"Guardian of {patient.person.first_name}",
            title="Sick Bay Admission Alert",
            message=f"{patient.person.first_name} has been admitted to {ward_name} ({bed_number}).",
            channels=['in_app', 'email', 'sms']
        )

        return {
            "status": "success",
            "admission_id": str(admission.id),
            "ward": ward.name,
            "bed_number": admission.bed_number,
            "admitted_at": str(admission.admitted_at)
        }


class VaccinationService:
    """
    Immunization & Health Compliance Engine.
    """
    @classmethod
    @transaction.atomic
    def record_vaccination(cls, patient, vaccine_name, administered_date=None):
        tenant = patient.tenant
        date_given = administered_date or timezone.now().date()

        vaccination = Vaccination.objects.create(
            tenant=tenant,
            patient=patient,
            vaccine_name=vaccine_name,
            administered_date=date_given
        )

        return {
            "status": "success",
            "vaccination_id": str(vaccination.id),
            "vaccine_name": vaccination.vaccine_name,
            "administered_date": str(vaccination.administered_date)
        }
