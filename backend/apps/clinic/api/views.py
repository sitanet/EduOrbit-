from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import Person
from backend.apps.clinic.models import PatientProfile, ClinicVisit
from backend.apps.clinic.services.medical import MedicalRecordService, ClinicVisitService, MedicationService

class PatientRecordListAPIView(APIView):
    def get(self, request):
        patients = PatientProfile.objects.all()
        data = [
            {
                "id": str(p.id),
                "person_number": p.person.person_number,
                "name": f"{p.person.first_name} {p.person.last_name}",
                "blood_group": p.blood_group,
                "allergies": p.allergies
            }
            for p in patients
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class ClinicVisitCreateAPIView(APIView):
    def post(self, request):
        patient_id = request.data.get('patient_id')
        symptoms = request.data.get('symptoms')
        diagnosis = request.data.get('diagnosis', 'Under Review')

        try:
            patient = PatientProfile.objects.get(id=patient_id)
            res = ClinicVisitService.record_visit(patient=patient, symptoms=symptoms, diagnosis=diagnosis)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClinicVisitListAPIView(APIView):
    def get(self, request):
        visits = ClinicVisit.objects.all()
        data = [
            {
                "id": str(v.id),
                "patient_name": f"{v.patient.person.first_name} {v.patient.person.last_name}",
                "symptoms": v.symptoms,
                "diagnosis": v.diagnosis,
                "visit_date": str(v.visit_date)
            }
            for v in visits
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class MedicationAdministerAPIView(APIView):
    def post(self, request):
        visit_id = request.data.get('visit_id')
        drug_name = request.data.get('drug_name')
        dosage = request.data.get('dosage', '1 tablet 3x daily')

        try:
            visit = ClinicVisit.objects.get(id=visit_id)
            res = MedicationService.prescribe_drug(visit=visit, drug_name=drug_name, dosage=dosage)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
