from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from backend.apps.people.models import Person, StudentProfile
from backend.apps.academic.models import AcademicYear, AcademicClass
from backend.apps.tenants.models import School
from backend.apps.students.services.enrollment import EnrollmentService
from backend.apps.students.services.student_number import StudentNumberGeneratorService
from backend.apps.students.services.lifecycle import StudentLifecycleService

class StudentListAPIView(APIView):
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        students = StudentProfile.objects.filter(tenant=tenant).select_related('person')
        data = [
            {
                "id": str(s.id),
                "student_number": s.student_number,
                "admission_number": s.admission_number,
                "first_name": s.person.first_name,
                "last_name": s.person.last_name,
                "enrollment_status": s.enrollment_status,
                "boarding_status": s.boarding_status
            }
            for s in students
        ]
        return Response({"status": "success", "count": len(data), "data": data})

class StudentEnrollmentAPIView(APIView):
    @transaction.atomic
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        school_id = request.data.get('school_id')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        gender = request.data.get('gender', 'male')
        dob = request.data.get('date_of_birth', '2012-01-01')
        
        if not first_name or not last_name:
            return Response({"status": "error", "message": "first_name and last_name are required."}, status=status.HTTP_400_BAD_REQUEST)

        stu_number = StudentNumberGeneratorService.generate_next_student_number(tenant=tenant)
        person_number = f"PER-STU-{stu_number.split('-')[-1]}"

        person = Person.objects.create(
            tenant=tenant,
            person_number=person_number,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=dob
        )

        student_profile = StudentProfile.objects.create(
            tenant=tenant,
            person=person,
            student_number=stu_number,
            admission_number=f"ADM-{stu_number.split('-')[-1]}",
            current_school_id=school_id,
            enrollment_status="pending"
        )

        return Response({
            "status": "success",
            "message": "Student enrolled successfully.",
            "data": {
                "student_id": str(student_profile.id),
                "student_number": student_profile.student_number,
                "admission_number": student_profile.admission_number,
                "name": f"{first_name} {last_name}",
                "enrollment_status": student_profile.enrollment_status
            }
        }, status=status.HTTP_201_CREATED)

class PromoteStudentAPIView(APIView):
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        student_id = request.data.get('student_id')
        prev_class_id = request.data.get('previous_class_id')
        new_class_id = request.data.get('new_class_id')
        reason = request.data.get('reason', 'Class Promotion')

        try:
            student = StudentProfile.objects.get(id=student_id, tenant=tenant)
            prev_class = AcademicClass.objects.get(id=prev_class_id, tenant=tenant)
            new_class = AcademicClass.objects.get(id=new_class_id, tenant=tenant)

            res = EnrollmentService.promote_student(student, prev_class, new_class, reason=reason)
            return Response({"status": "success", "data": res})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class WithdrawStudentAPIView(APIView):
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        student_id = request.data.get('student_id')
        reason = request.data.get('reason', 'Parent Request')

        try:
            student = StudentProfile.objects.get(id=student_id, tenant=tenant)
            res = EnrollmentService.withdraw_student(student, reason=reason)
            return Response({"status": "success", "data": res})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentRecordAPIView(APIView):
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        student_id = request.query_params.get('student_id')
        try:
            student = StudentProfile.objects.get(id=student_id, tenant=tenant)
            return Response({
                "status": "success",
                "data": {
                    "student_number": student.student_number,
                    "admission_number": student.admission_number,
                    "name": f"{student.person.first_name} {student.person.last_name}",
                    "gender": student.person.gender,
                    "enrollment_status": student.enrollment_status,
                    "boarding_status": student.boarding_status
                }
            })
        except StudentProfile.DoesNotExist:
            return Response({"status": "error", "message": "Student record not found."}, status=status.HTTP_404_NOT_FOUND)
