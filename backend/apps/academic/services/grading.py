from decimal import Decimal
from django.db import transaction
from backend.apps.academic.models import GradingScale

class GradeCalculationService:
    """
    Grading & Result Computation Engine.
    Handles score-to-letter grade mapping, weighted GPA calculation, and class ranking statistics.
    """
    DEFAULT_GRADING_SCHEME = [
        (70.0, 100.0, "A", 4.0, "Excellent"),
        (60.0, 69.99, "B", 3.0, "Very Good"),
        (50.0, 59.99, "C", 2.0, "Good"),
        (45.0, 49.99, "D", 1.0, "Pass"),
        (40.0, 44.99, "E", 0.5, "Fair Pass"),
        (0.0,  39.99, "F", 0.0, "Fail")
    ]

    @classmethod
    def calculate_grade(cls, school, score):
        # Convert score to float
        score_flt = float(score)
        
        # Check custom tenant grading scale first
        scales = GradingScale.objects.filter(school=school).order_by('-min_score')
        for s in scales:
            if float(s.min_score) <= score_flt <= float(s.max_score):
                return {
                    "grade_letter": s.grade_letter,
                    "gpa_value": float(s.gpa_value),
                    "remarks": s.remarks or "Satisfactory"
                }

        # Fallback to standard 4.0 grading scale
        for min_s, max_s, letter, gpa, remark in cls.DEFAULT_GRADING_SCHEME:
            if min_s <= score_flt <= max_s:
                return {
                    "grade_letter": letter,
                    "gpa_value": gpa,
                    "remarks": remark
                }

        return {"grade_letter": "F", "gpa_value": 0.0, "remarks": "Fail"}

    @classmethod
    @transaction.atomic
    def compute_student_result(cls, student, school, subject_scores):
        """
        Computes overall total, average, GPA, and subject grade breakdown for a student.
        subject_scores format: [{'subject_name': 'Maths', 'ca_score': 30, 'exam_score': 60, 'credit_units': 3}]
        """
        results = []
        total_weighted_points = 0.0
        total_credit_units = 0

        for item in subject_scores:
            ca = float(item.get('ca_score', 0))
            exam = float(item.get('exam_score', 0))
            total_score = ca + exam
            credits = int(item.get('credit_units', 1))

            grade_info = cls.calculate_grade(school=school, score=total_score)

            results.append({
                "subject": item.get('subject_name'),
                "ca_score": ca,
                "exam_score": exam,
                "total_score": total_score,
                "grade_letter": grade_info["grade_letter"],
                "gpa_value": grade_info["gpa_value"],
                "remarks": grade_info["remarks"]
            })

            total_weighted_points += (grade_info["gpa_value"] * credits)
            total_credit_units += credits

        overall_avg = sum(r["total_score"] for r in results) / len(results) if results else 0.0
        gpa = round(total_weighted_points / total_credit_units, 2) if total_credit_units > 0 else 0.0

        return {
            "student_number": student.student_number,
            "overall_average": round(overall_avg, 2),
            "gpa": gpa,
            "subject_count": len(results),
            "subject_breakdown": results
        }
