import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# PATIENT REGISTRY & CLINICS
# ==============================================================

class Clinic(TenantBaseModel):
    """
    Physical clinic buildings, sickbays, or consultation wings.
    """
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class PatientProfile(TenantBaseModel):
    """
    Extends PMC base Person table with HIPAA-compliant medical indexes (allergies, blood).
    """
    person = models.OneToOneField('people.Person', on_delete=models.CASCADE, related_name='patient_profile')
    blood_group = models.CharField(max_length=10, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)

    def __str__(self):
        return f"Patient: {self.person.first_name} {self.person.last_name}"


# ==============================================================
# CLINICAL WORKFLOWS
# ==============================================================

class Appointment(TenantBaseModel):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='scheduled')

    def __str__(self):
        return f"Appt: {self.patient.person.first_name} at {self.appointment_date}"


class ClinicVisit(TenantBaseModel):
    """
    Consultation log tracking symptoms and doctor triage diagnosis.
    """
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('referred', 'Referred'),
        ('admitted', 'Admitted to Sick Bay')
    ]
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateTimeField(default=timezone.now)
    symptoms = models.TextField()
    diagnosis = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='completed')

    def __str__(self):
        return f"Visit: {self.patient.person.first_name} on {self.visit_date}"


# ==============================================================
# PHARMACY & DISPENSARY
# ==============================================================

class Drug(TenantBaseModel):
    name = models.CharField(max_length=150)
    stock_qty = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class DrugBatch(TenantBaseModel):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.drug.name} (Batch: {self.batch_number})"


class Prescription(TenantBaseModel):
    visit = models.ForeignKey(ClinicVisit, on_delete=models.CASCADE, related_name='prescriptions')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)

    def __str__(self):
        return f"Prescr: {self.drug.name} ({self.dosage})"


class DrugDispenseLog(TenantBaseModel):
    """Audit log for dispensed medications."""
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='dispense_logs')
    patient = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='drug_dispenses')
    dispensed_to = models.CharField(max_length=200, blank=True)
    quantity = models.IntegerField(default=1)
    dispensed_at = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Dispensed {self.quantity} x {self.drug.name} to {self.dispensed_to or 'General'} at {self.dispensed_at}"


# ==============================================================
# SICK BAY ADMISSIONS & VACCINATIONS
# ==============================================================

class Ward(TenantBaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SickBayAdmission(TenantBaseModel):
    """
    In-patient boarding logs.
    """
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='admissions')
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='admissions')
    bed_number = models.CharField(max_length=50)
    admitted_at = models.DateTimeField(default=timezone.now)
    discharged_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Adm: {self.patient.person.first_name} Bed: {self.bed_number}"


class Vaccination(TenantBaseModel):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=100)
    administered_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Vacc: {self.vaccine_name} for {self.patient.person.first_name}"
