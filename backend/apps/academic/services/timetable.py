from django.db import transaction
from backend.apps.timetable.models import Schedule, ScheduleType, TimeSlot, Resource, BellSchedule, Lesson

class ConflictDetectionService:
    """
    Service for detecting scheduling conflicts (Teacher double-booking, Resource collisions).
    """
    @classmethod
    def check_conflicts(cls, school, time_slot, teacher_person=None, resource=None):
        conflicts = []

        if teacher_person:
            if Schedule.objects.filter(
                school=school, time_slot=time_slot, lesson__teacher=teacher_person
            ).exists():
                conflicts.append(f"Teacher Collision: {teacher_person.first_name} {teacher_person.last_name} is already teaching at this time slot.")

        if resource:
            if Schedule.objects.filter(
                school=school, time_slot=time_slot, resource=resource
            ).exists():
                conflicts.append(f"Resource Collision: {resource.name} is already occupied at this time slot.")

        return conflicts

class TimetableGenerationService:
    """
    Service for generating, editing, and publishing master academic timetables.
    """
    @classmethod
    @transaction.atomic
    def create_schedule_slot(cls, school, schedule_type, lesson, resource, time_slot, title="Academic Lesson"):
        # Check conflicts
        conflicts = ConflictDetectionService.check_conflicts(
            school=school,
            time_slot=time_slot,
            teacher_person=lesson.teacher if lesson else None,
            resource=resource
        )
        if conflicts:
            return {"status": "error", "has_conflicts": True, "conflicts": conflicts}

        schedule = Schedule.objects.create(
            tenant=school.tenant,
            school=school,
            schedule_type=schedule_type,
            lesson=lesson,
            resource=resource,
            time_slot=time_slot,
            title=title
        )

        return {
            "status": "success",
            "schedule_id": str(schedule.id),
            "title": schedule.title,
            "resource": resource.name if resource else None
        }

