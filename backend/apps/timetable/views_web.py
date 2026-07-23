from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from backend.apps.tenants.models import School
from backend.apps.timetable.models import Resource, Schedule, ConflictReport

class TimetableMatrixWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        
        # Resolve active school context from session
        active_school_id = request.session.get('active_school_id')
        active_school = School.objects.filter(id=active_school_id, tenant=tenant).first() if active_school_id else None
        if not active_school:
            active_school = schools.first()
            
        schedules = Schedule.objects.filter(school=active_school, tenant=tenant).select_related('lesson__subject', 'lesson__teacher', 'resource', 'time_slot')
        conflicts = ConflictReport.objects.filter(school=active_school, tenant=tenant)
        
        # Fetch setup components
        from backend.apps.timetable.models import Resource, TimeSlot, Lesson, BellSchedule
        from backend.apps.academic.models import Subject, AcademicClass
        from backend.apps.people.models import Person
        
        bell, _ = BellSchedule.objects.get_or_create(
            school=active_school,
            tenant=tenant,
            defaults={'name': 'Standard Bell Schedule'}
        )
        
        resources = Resource.objects.filter(school=active_school, tenant=tenant)
        time_slots = TimeSlot.objects.filter(bell_schedule=bell, tenant=tenant)
        lessons = Lesson.objects.filter(school=active_school, tenant=tenant)
        
        subjects = Subject.objects.filter(school=active_school, tenant=tenant)
        classes = AcademicClass.objects.filter(tenant=tenant)
        teachers = Person.objects.filter(tenant=tenant, assigned_roles__role='staff').distinct()
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'schedules': schedules,
            'conflicts': conflicts,
            'resources': resources,
            'time_slots': time_slots,
            'lessons': lessons,
            'subjects': subjects,
            'classes': classes,
            'teachers': teachers,
            'bell_schedule': bell
        }
        return render(request, 'timetable/builder.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        action = request.POST.get('action')
        tenant = getattr(request, 'tenant', None)
        
        # Resolve active school context from session
        active_school_id = request.session.get('active_school_id')
        active_school = School.objects.filter(id=active_school_id, tenant=tenant).first() if active_school_id else School.objects.filter(tenant=tenant).first()
        
        if action == 'create_resource':
            name = request.POST.get('name')
            res_type = request.POST.get('resource_type', 'classroom')
            capacity = request.POST.get('capacity', 40)
            if name and active_school:
                Resource.objects.create(
                    tenant=tenant,
                    school=active_school,
                    name=name,
                    resource_type=res_type,
                    capacity=int(capacity)
                )
        elif action == 'create_timeslot':
            day = request.POST.get('day_of_week')
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            
            from backend.apps.timetable.models import BellSchedule, TimeSlot
            bell, _ = BellSchedule.objects.get_or_create(
                school=active_school,
                tenant=tenant,
                defaults={'name': 'Standard Bell Schedule'}
            )
            if day and start and end:
                TimeSlot.objects.create(
                    tenant=tenant,
                    bell_schedule=bell,
                    day_of_week=day,
                    start_time=start,
                    end_time=end
                )
        elif action == 'create_lesson':
            subject_id = request.POST.get('subject_id')
            teacher_id = request.POST.get('teacher_id')
            class_id = request.POST.get('class_id')
            duration = request.POST.get('duration_minutes', 40)
            
            from backend.apps.academic.models import Subject, AcademicClass
            from backend.apps.people.models import Person
            from backend.apps.timetable.models import Lesson
            
            subject = Subject.objects.filter(id=subject_id, tenant=tenant).first()
            teacher = Person.objects.filter(id=teacher_id, tenant=tenant).first()
            a_class = AcademicClass.objects.filter(id=class_id, tenant=tenant).first()
            
            if subject and teacher and a_class and active_school:
                Lesson.objects.get_or_create(
                    tenant=tenant,
                    school=active_school,
                    subject=subject,
                    teacher=teacher,
                    academic_class=a_class,
                    defaults={'duration_minutes': int(duration)}
                )
                
        return redirect('/timetable/builder/')


class ResourceBookingWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        resources = Resource.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'timetable/bookings.html', {'resources': resources})
