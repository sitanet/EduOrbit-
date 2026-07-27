from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.apps.people.models import StudentProfile
from backend.apps.lms.models import LearningModule, LearningActivity, Course, CourseLesson, Quiz
from backend.apps.lms.services.learning import AssignmentSubmissionService, QuizService

class CourseListAPIView(APIView):
    def get(self, request):
        courses = Course.objects.all()
        data = [
            {
                "id": str(c.id),
                "title": c.title,
                "description": c.description,
                "subject_name": c.subject.name,
                "lessons_count": c.lessons.count()
            }
            for c in courses
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class LessonListAPIView(APIView):
    def get(self, request):
        lessons = CourseLesson.objects.all()
        data = [
            {
                "id": str(l.id),
                "title": l.title,
                "course_title": l.course.title,
                "video_url": l.video_url,
                "order": l.order
            }
            for l in lessons
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class QuizListAPIView(APIView):
    def get(self, request):
        quizzes = Quiz.objects.all()
        data = [
            {
                "id": str(q.id),
                "title": q.title,
                "course_title": q.course.title,
                "total_marks": q.total_marks,
                "pass_marks": q.pass_marks
            }
            for q in quizzes
        ]
        return Response({"status": "success", "count": len(data), "data": data})


class QuizSubmitAPIView(APIView):
    def post(self, request):
        quiz_id = request.data.get('quiz_id')
        student_id = request.data.get('student_id')
        score_achieved = request.data.get('score_achieved', 0.0)

        try:
            quiz = Quiz.objects.get(id=quiz_id)
            student = StudentProfile.objects.get(id=student_id)
            res = QuizService.submit_quiz(quiz=quiz, student=student, score_achieved=score_achieved)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AssignmentSubmitAPIView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        activity_id = request.data.get('activity_id')
        content_body = request.data.get('content_body', '')

        try:
            student = StudentProfile.objects.get(id=student_id)
            activity = LearningActivity.objects.get(id=activity_id)
            res = AssignmentSubmissionService.submit_assignment(student=student, activity=activity, content_body=content_body)
            return Response({"status": "success", "data": res}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
