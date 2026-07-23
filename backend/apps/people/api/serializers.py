from rest_framework import serializers
from backend.apps.people.models import (
    Person, PersonPreference, PersonRole, EmailAddress,
    PhoneNumber, PhysicalAddress, EmergencyContact,
    StudentProfile, TeacherProfile, StaffProfile, ParentProfile,
    FamilyRelationship, EmploymentHistory
)

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'person_number', 'title', 'first_name', 'middle_name', 'last_name', 'preferred_name', 'gender', 'date_of_birth', 'nationality']


class PersonPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonPreference
        fields = ['id', 'preferred_language', 'theme', 'timezone', 'notification_preference', 'accessibility_settings']


class PersonRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonRole
        fields = ['id', 'role', 'school', 'campus', 'start_date', 'end_date', 'status', 'is_primary']


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAddress
        fields = ['id', 'email', 'is_primary', 'is_verified']


class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['id', 'number', 'is_primary', 'is_verified']


class PhysicalAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalAddress
        fields = ['id', 'address_line1', 'address_line2', 'city', 'state', 'country', 'is_primary']


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'contact_name', 'relationship', 'phone', 'email', 'priority']


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['id', 'student_number', 'admission_number', 'enrollment_status', 'boarding_status']


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyRelationship
        fields = ['id', 'student', 'relative', 'relationship_type', 'legal_guardian', 'pickup_authorized', 'fee_responsibility_percentage', 'medical_consent']
