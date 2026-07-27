from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.academic.models import (
    AcademicSettings, AcademicYear, EducationLevel, AcademicClass,
    Subject, GradingScale, SchoolCalendarEvent, PromotionPolicy
)
from backend.apps.academic.api.serializers import (
    AcademicSettingsSerializer, AcademicYearSerializer, EducationLevelSerializer,
    AcademicClassSerializer, SubjectSerializer, GradingScaleSerializer,
    CalendarEventSerializer, PromotionPolicySerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class AcademicSettingsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        settings = get_object_or_404(AcademicSettings, school_id=school_id, tenant=request.tenant)
        serializer = AcademicSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        school_id = request.data.get('school_id')
        settings = get_object_or_404(AcademicSettings, school_id=school_id, tenant=request.tenant)
        serializer = AcademicSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcademicYearAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        years = AcademicYear.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = AcademicYearSerializer(years, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        school_id = request.data.get('school_id')
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.save(school_id=school_id, tenant=request.tenant)
            event_bus.publish(DomainEvent("subject.created", tenant_id=str(request.tenant.id), data={"subject": subject.name}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================
# TIMETABLE & SCHEDULING ENGINE API VIEWS
# ==============================================================

class TimetableCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        school_id = request.data.get('school_id')
        academic_year_id = request.data.get('academic_year_id')
        name = request.data.get('name', 'Master Timetable')

        try:
            school = School.objects.get(id=school_id, tenant=tenant)
            year = AcademicYear.objects.get(id=academic_year_id, tenant=tenant)
            res = TimetableGenerationService.create_timetable(school, year, None, name=name)
            return Response({"status": "success", "data": res}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TimetableScheduleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        timetable_id = request.data.get('timetable_id')
        day_of_week = request.data.get('day_of_week')
        bell_schedule_id = request.data.get('bell_schedule_id')
        academic_class_id = request.data.get('academic_class_id')
        subject_id = request.data.get('subject_id')

        try:
            timetable = Timetable.objects.get(id=timetable_id, tenant=tenant)
            bell_schedule = BellSchedule.objects.get(id=bell_schedule_id, tenant=tenant)
            academic_class = AcademicClass.objects.get(id=academic_class_id, tenant=tenant)
            subject = Subject.objects.get(id=subject_id, tenant=tenant)

            res = TimetableGenerationService.schedule_entry(
                timetable=timetable,
                day_of_week=day_of_week,
                bell_schedule=bell_schedule,
                academic_class=academic_class,
                subject=subject
            )
            return Response({"status": "success" if res["status"] == "success" else "error", "data": res}, status=status.HTTP_200_OK if res["status"] == "success" else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TimetablePublishAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        timetable_id = request.data.get('timetable_id')

        try:
            timetable = Timetable.objects.get(id=timetable_id, tenant=tenant)
            res = TimetableGenerationService.publish_timetable(timetable)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EducationLevelAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        levels = EducationLevel.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = EducationLevelSerializer(levels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubjectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school_id = request.query_params.get('school_id')
        subjects = Subject.objects.filter(school_id=school_id, tenant=request.tenant)
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==============================================================
# ATTENDANCE MANAGEMENT ENGINE API VIEWS
# ==============================================================

from backend.apps.attendance.models import AttendanceSession, AttendanceType
from backend.apps.people.models import Person
from backend.apps.academic.services.attendance import AttendanceService

class AttendanceCheckInAPIView(APIView):
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        session_id = request.data.get('session_id')
        person_id = request.data.get('person_id')
        status_code = request.data.get('status_code', 'present')
        source_code = request.data.get('source_code', 'manual')
        reason_code = request.data.get('reason_code')

        try:
            session = AttendanceSession.objects.get(id=session_id)
            person = Person.objects.get(id=person_id)
            res = AttendanceService.mark_attendance(
                session=session,
                person=person,
                status_code=status_code,
                source_code=source_code,
                reason_code=reason_code
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AttendanceSummaryAPIView(APIView):
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        person_id = request.query_params.get('person_id')

        try:
            person = Person.objects.get(id=person_id, tenant=tenant)
            summary = AttendanceService.get_attendance_summary(person)
            return Response({"status": "success", "data": summary}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({"status": "error", "message": "Person profile not found."}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================
# ASSESSMENT, GRADING, & EXAMINATION ENGINE API VIEWS
# ==============================================================

from backend.apps.people.models import StudentProfile
from backend.apps.tenants.models import School
from backend.apps.academic.services.grading import GradeCalculationService

class AssessmentCalculateAPIView(APIView):
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        student_id = request.data.get('student_id')
        school_id = request.data.get('school_id')
        subject_scores = request.data.get('subject_scores', [])

        try:
            student = StudentProfile.objects.get(id=student_id)
            school = School.objects.get(id=school_id)
            res = GradeCalculationService.compute_student_result(
                student=student,
                school=school,
                subject_scores=subject_scores
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentResultReportAPIView(APIView):
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        student_id = request.query_params.get('student_id')

        try:
            student = StudentProfile.objects.get(id=student_id)
            return Response({
                "status": "success",
                "data": {
                    "student_number": student.student_number,
                    "admission_number": student.admission_number,
                    "name": f"{student.person.first_name} {student.person.last_name}",
                    "status": "published"
                }
            }, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response({"status": "error", "message": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================
# PROMOTION, GRADUATION, & TRANSCRIPT API VIEWS
# ==============================================================

from backend.apps.academic.models import AcademicClass
from backend.apps.academic.services.progression import PromotionService, GraduationService, TranscriptService

class PromotionRunAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        previous_class_id = request.data.get('previous_class_id')
        new_class_id = request.data.get('new_class_id')
        overall_score = request.data.get('overall_score', 60.0)

        try:
            student = StudentProfile.objects.get(id=student_id)
            prev_class = AcademicClass.objects.get(id=previous_class_id)
            new_class = AcademicClass.objects.get(id=new_class_id)

            res = PromotionService.run_class_promotion(
                student=student,
                previous_class=prev_class,
                new_class=new_class,
                overall_score=overall_score
            )
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GraduationRunAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        try:
            student = StudentProfile.objects.get(id=student_id)
            res = GraduationService.evaluate_and_graduate(student=student)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TranscriptDetailAPIView(APIView):
    def get(self, request, student_uuid):
        try:
            student = StudentProfile.objects.get(id=student_uuid)
            res = TranscriptService.generate_transcript(student=student)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response({"status": "error", "message": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)



