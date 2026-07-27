from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from backend.apps.tenants.models import Tenant, School
from backend.apps.academic.models import Subject, Curriculum
from backend.apps.people.models import Person, StudentProfile
from backend.apps.lms.models import Course, CourseLesson, Quiz, QuizAttempt
from backend.apps.lms.services.learning import CourseService, LessonService, QuizService

class LMSV180TestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test LMS Tenant v180")
        self.school = School.objects.create(tenant=self.tenant, name="Academy of Technology")
        self.curriculum = Curriculum.objects.create(name="STEM Curriculum", code="STEM-V180")
        self.subject = Subject.objects.create(tenant=self.tenant, school=self.school, curriculum=self.curriculum, name="Computer Science", code="CS101")
        self.course = Course.objects.create(
            tenant=self.tenant, school=self.school, subject=self.subject, title="Python Programming Masterclass", description="Complete Python course", is_published=True
        )
        self.lesson = CourseLesson.objects.create(
            tenant=self.tenant, course=self.course, title="Variables & Control Flow", content_body="Intro to Python variables", order=1
        )
        self.quiz = Quiz.objects.create(
            tenant=self.tenant, course=self.course, title="Python Syntax Quiz", total_marks=100, pass_marks=60
        )
        
        self.student_person = Person.objects.create(
            tenant=self.tenant, person_number="PER-STU-8899", first_name="Ada", last_name="Lovelace", date_of_birth="1815-12-10", gender="female"
        )
        self.student = StudentProfile.objects.create(
            tenant=self.tenant, person=self.student_person, student_number="STU-CS-001", admission_number="ADM-CS-001", current_school=self.school
        )
        self.client = APIClient()

    def test_course_lesson_and_quiz_services(self):
        # 1. Course Creation
        crs_res = CourseService.create_course(school=self.school, subject=self.subject, title="Data Structures in Python")
        self.assertEqual(crs_res["status"], "success")

        # 2. Lesson Creation
        lsn_res = LessonService.create_lesson(course=self.course, title="Functions & Modules", content_body="Advanced functions", video_url="https://video.eduorbit.com/lesson2")
        self.assertEqual(lsn_res["status"], "success")

        # 3. Quiz Submission
        qz_res = QuizService.submit_quiz(quiz=self.quiz, student=self.student, score_achieved=85.00)
        self.assertEqual(qz_res["status"], "success")
        self.assertTrue(qz_res["is_passed"])

    def test_lms_v180_api_endpoints(self):
        # 1. Courses API
        c_url = '/lms/api/v1/courses/'
        c_resp = self.client.get(c_url)
        self.assertEqual(c_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(c_resp.data["count"] > 0)

        # 2. Lessons API
        l_url = '/lms/api/v1/lessons/'
        l_resp = self.client.get(l_url)
        self.assertEqual(l_resp.status_code, status.HTTP_200_OK)

        # 3. Quizzes API
        q_url = '/lms/api/v1/quizzes/'
        q_resp = self.client.get(q_url)
        self.assertEqual(q_resp.status_code, status.HTTP_200_OK)

        # 4. Quiz Submit API
        sub_url = '/lms/api/v1/quizzes/submit/'
        payload = {
            "quiz_id": str(self.quiz.id),
            "student_id": str(self.student.id),
            "score_achieved": 90.00
        }
        sub_resp = self.client.post(sub_url, payload, format='json')
        self.assertEqual(sub_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(sub_resp.data["status"], "success")
