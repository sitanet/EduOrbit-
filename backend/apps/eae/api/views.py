from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import StudentProfile
from backend.apps.eae.models import Question, Assessment, AssessmentAttempt, AssessmentResult
from backend.apps.eae.services.cbt import CandidateService, AutoMarkingService, ResultService

class QuestionBankListAPIView(APIView):
    def get(self, request):
        questions = Question.objects.all()
        data = [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "question_type": q.question_type,
                "complexity": q.complexity,
                "choices_count": q.choices.count()
            }
            for q in questions
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class ExamListAPIView(APIView):
    def get(self, request):
        exams = Assessment.objects.all()
        data = [
            {
                "id": str(e.id),
                "title": e.title,
                "duration_minutes": e.duration_minutes,
                "is_active": e.is_active
            }
            for e in exams
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class ExamStartAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        exam_id = request.data.get('exam_id')

        try:
            student = StudentProfile.objects.get(id=student_id)
            exam = Assessment.objects.get(id=exam_id)
            res = CandidateService.start_exam(student=student, assessment=exam)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExamSubmitAPIView(APIView):
    def post(self, request):
        attempt_id = request.data.get('attempt_id')

        try:
            attempt = AssessmentAttempt.objects.get(id=attempt_id)
            res = AutoMarkingService.auto_grade_attempt(attempt=attempt)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResultListAPIView(APIView):
    def get(self, request):
        results = AssessmentResult.objects.all()
        data = [
            {
                "id": str(r.id),
                "student_number": r.student.student_number,
                "assessment_title": r.assessment.title,
                "percentage": float(r.percentage),
                "grade": r.grade
            }
            for r in results
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class ResultPublishAPIView(APIView):
    def post(self, request):
        exam_id = request.data.get('exam_id')

        try:
            exam = Assessment.objects.get(id=exam_id)
            res = ResultService.publish_results(assessment=exam)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
