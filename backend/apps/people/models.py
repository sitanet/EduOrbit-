import uuid
from django.db import models
from django.utils import timezone
from backend.apps.core.models import TenantBaseModel, PlatformBaseModel

# ==============================================================
# BASE PERSON & PREFERENCES
# ==============================================================

class Person(TenantBaseModel):
    """
    Polymorphic core entity representing any human in the system.
    All demographics and static identity fields live here.
    """
    person_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150)
    preferred_name = models.CharField(max_length=150, blank=True)
    
    gender = models.CharField(max_length=20, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=150, blank=True)
    nationality = models.CharField(max_length=100, default='Nigerian')
    state_of_origin = models.CharField(max_length=100, blank=True)
    local_govt_area = models.CharField(max_length=100, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    marital_status = models.CharField(max_length=30, blank=True)
    
    # Optional direct IAM mapping link
    user = models.OneToOneField('identity.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='person_profile')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.person_number})"


class PersonPreference(TenantBaseModel):
    """
    User settings preferences.
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='preferences')
    preferred_language = models.CharField(max_length=20, default='en')
    theme = models.CharField(max_length=20, default='light')
    timezone = models.CharField(max_length=50, default='UTC')
    notification_preference = models.JSONField(default=dict, blank=True)
    accessibility_settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Prefs for {self.person.person_number}"


# ==============================================================
# ROLE ASSIGNMENTS
# ==============================================================

class PersonRole(TenantBaseModel):
    """
    Role assignments mapped per person to schools and campuses.
    Allows a person to hold multiple active roles simultaneously.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
        ('guardian', 'Guardian')
    ]
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='assigned_roles')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    campus = models.ForeignKey('tenants.Campus', on_delete=models.CASCADE, null=True, blank=True)
    
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('person', 'role', 'school')

    def __str__(self):
        return f"{self.person.person_number} - {self.role} @ {self.school.name}"


# ==============================================================
# NORMALIZED CONTACTS
# ==============================================================

class EmailAddress(TenantBaseModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='emails')
    email = models.EmailField()
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.email


class PhoneNumber(TenantBaseModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='phones')
    number = models.CharField(max_length=30)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.number


class PhysicalAddress(TenantBaseModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Nigeria')
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line1}, {self.city}"


class EmergencyContact(TenantBaseModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='emergency_contacts')
    contact_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=50)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    priority = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.contact_name} ({self.relationship})"


# ==============================================================
# ROLE EXTENSION PROFILE RECORDS
# ==============================================================

class StudentProfile(TenantBaseModel):
    """
    Student-specific tracking properties linking back to unique Person.
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='student_profile')
    student_number = models.CharField(max_length=50, unique=True, db_index=True)
    admission_number = models.CharField(max_length=50, blank=True)
    current_school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    enrollment_status = models.CharField(max_length=30, default='enrolled')
    boarding_status = models.CharField(max_length=20, default='day')

    def __str__(self):
        return self.student_number


class TeacherProfile(TenantBaseModel):
    """
    Teacher licensing and registration data.
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_number = models.CharField(max_length=50, unique=True, db_index=True)
    teaching_license_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.employee_number


class StaffProfile(TenantBaseModel):
    """
    General administrative school staff properties.
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='staff_profile')
    employee_number = models.CharField(max_length=50, unique=True, db_index=True)
    role_type = models.CharField(max_length=50)  # ICT, Nurse, Guard, etc.
    supervisor = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.employee_number


class ParentProfile(TenantBaseModel):
    """
    Parent/Guardian profile marker linking back to unique Person.
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='parent_profile')
    parent_number = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.parent_number


# ==============================================================
# MEDICAL PROFILES & HISTORY
# ==============================================================

class MedicalProfile(TenantBaseModel):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='medical_profile')
    blood_group = models.CharField(max_length=10, blank=True)
    genotype = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"Medical for {self.person.person_number}"


class MedicalHistory(TenantBaseModel):
    """
    Dynamic changes/vaccination timelines per person.
    """
    TYPES = [
        ('allergy', 'Allergies'),
        ('vaccine', 'Vaccination Record'),
        ('chronic', 'Chronic Condition'),
        ('visit', 'Clinic Visit Notes')
    ]
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='medical_history')
    record_type = models.CharField(max_length=30, choices=TYPES)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    date_recorded = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.record_type} - {self.name}"


# ==============================================================
# QUALIFICATIONS & CERTIFICATES
# ==============================================================

class Qualification(TenantBaseModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='qualifications')
    qualification_type = models.CharField(max_length=50)  # Degree, Certificate, Membership
    name = models.CharField(max_length=150)
    issuing_institution = models.CharField(max_length=150)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# ==============================================================
# FAMILY RELATIONSHIP ENGINE
# ==============================================================

class FamilyRelationship(TenantBaseModel):
    """
    Junction mapping between Student Person and Parent/Guardian Person.
    """
    RELATIONSHIPS = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('sibling', 'Sibling'),
        ('sponsor', 'Sponsor'),
        ('relative', 'Relative')
    ]
    # Child (the student)
    student = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='relative_links')
    # Guardian / Relative
    relative = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='student_links')
    
    relationship_type = models.CharField(max_length=30, choices=RELATIONSHIPS)
    
    legal_guardian = models.BooleanField(default=False)
    pickup_authorized = models.BooleanField(default=True)
    fee_responsibility_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    medical_consent = models.BooleanField(default=False)
    emergency_contact_priority = models.IntegerField(default=1)

    class Meta:
        unique_together = ('student', 'relative')

    def __str__(self):
        return f"{self.relative.person_number} is {self.relationship_type} of {self.student.person_number}"


# ==============================================================
# EMPLOYMENT HISTORY
# ==============================================================

class EmploymentPosition(TenantBaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('academic.Department', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class EmploymentHistory(TenantBaseModel):
    TYPES = [
        ('appointment', 'Appointment'),
        ('promotion', 'Promotion'),
        ('transfer', 'Transfer'),
        ('resignation', 'Resignation'),
        ('retirement', 'Retirement')
    ]
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='employment_history')
    position = models.ForeignKey(EmploymentPosition, on_delete=models.CASCADE)
    record_type = models.CharField(max_length=30, choices=TYPES)
    effective_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.record_type} - {self.position.name}"


# ==============================================================
# REUSABLE SECURE DOCUMENT ENGINE
# ==============================================================

class DocumentType(PlatformBaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PersonDocument(TenantBaseModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    document_file = models.CharField(max_length=255, help_text="Upload URL or S3 location link")
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.document_type.name} - {self.person.person_number}"
