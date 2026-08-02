from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.hostel.models import Hostel, HostelRoom, BedAllocation
from backend.apps.dashboard.services import DashboardFactory, ROLE_WARDEN, ROLE_SCHOOL_ADMIN


class HostelDashboardWebView(View):
    """Hostel dashboard — warden, hostel_officer, school_admin, superuser only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_WARDEN) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()

        from backend.apps.hostel.models import Hostel, HostelRoom, HostelBed, BedAllocation, HostelBlock

        hostels = Hostel.objects.filter(tenant=tenant).prefetch_related('blocks__rooms')
        blocks = HostelBlock.objects.filter(tenant=tenant).select_related('hostel')
        total_rooms = HostelRoom.objects.filter(tenant=tenant).count()
        total_beds = HostelBed.objects.filter(tenant=tenant).count()
        occupied_beds = HostelBed.objects.filter(tenant=tenant, status='occupied').count()
        available_beds = HostelBed.objects.filter(tenant=tenant, status='available').count()

        occupancy_pct = int((occupied_beds / total_beds) * 100) if total_beds > 0 else 0

        allocations = BedAllocation.objects.filter(
            tenant=tenant, status='active'
        ).select_related('bed__room__block__hostel', 'student').order_by('-start_date')[:10]

        available_beds_list = HostelBed.objects.filter(tenant=tenant, status='available').select_related('room__block__hostel')[:30]

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'schools': schools,
            'active_school': active_school,
            'hostels': hostels,
            'blocks': blocks,
            'total_rooms': total_rooms,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'available_beds': available_beds,
            'occupancy_pct': occupancy_pct,
            'allocations': allocations,
            'available_beds_list': available_beds_list,
        })
        return render(request, 'hostel/dashboard.html', ctx)

    def post(self, request):
        """Handle bed allocation for a student."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'allocate_bed':
            bed_id = request.POST.get('bed_id')
            student_name = request.POST.get('student_name', '').strip()
            student_id = request.POST.get('student_id')

            from backend.apps.hostel.models import HostelBed, BedAllocation
            from backend.apps.people.models import Person

            student = None
            if student_id:
                student = Person.objects.filter(id=student_id, tenant=tenant).first()

            if not student and student_name:
                parts = student_name.split(maxsplit=1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''

                student = Person.objects.filter(
                    tenant=tenant,
                    first_name__icontains=first_name
                ).first()

                if not student:
                    student = Person.objects.create(
                        tenant=tenant,
                        first_name=first_name,
                        last_name=last_name or 'Boarder'
                    )

            if bed_id and student:
                bed = HostelBed.objects.filter(id=bed_id, tenant=tenant).first()
                if bed:
                    BedAllocation.objects.filter(bed=bed, status='active').update(status='completed')
                    BedAllocation.objects.create(
                        tenant=tenant,
                        bed=bed,
                        student=student,
                        status='active'
                    )
                    bed.status = 'occupied'
                    bed.save()

        return redirect(request.path)


class RoomsDirectoryWebView(View):
    """Rooms directory — warden/hostel_officer/school_admin roles only."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')

        allowed = (
            DashboardFactory.has_dashboard_access(request.user, ROLE_WARDEN) or
            DashboardFactory.has_dashboard_access(request.user, ROLE_SCHOOL_ADMIN)
        )
        if not allowed:
            return redirect(DashboardFactory.get_dashboard_url(request.user))

        tenant = getattr(request, 'tenant', None)
        from backend.apps.hostel.models import Hostel, HostelBlock, HostelBed

        rooms = HostelRoom.objects.filter(
            tenant=tenant
        ).select_related('block__hostel').prefetch_related('beds')

        hostels = Hostel.objects.filter(tenant=tenant)
        blocks = HostelBlock.objects.filter(tenant=tenant).select_related('hostel')

        total_beds = HostelBed.objects.filter(tenant=tenant).count()
        occupied_beds = HostelBed.objects.filter(tenant=tenant, status='occupied').count()
        available_beds = HostelBed.objects.filter(tenant=tenant, status='available').count()

        ctx = DashboardFactory.get_context(request.user)
        ctx.update({
            'rooms': rooms,
            'hostels': hostels,
            'blocks': blocks,
            'total_rooms': rooms.count(),
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'available_beds': available_beds,
        })
        return render(request, 'hostel/rooms.html', ctx)

    def post(self, request):
        """Handle adding a new room with beds."""
        if not request.user.is_authenticated:
            return redirect('login_web')

        tenant = getattr(request, 'tenant', None)
        action = request.POST.get('action')

        if action == 'add_room':
            room_number = request.POST.get('room_number', '').strip()
            block_id = request.POST.get('block_id')
            hostel_id = request.POST.get('hostel_id')
            floor = request.POST.get('floor', '').strip()
            capacity = request.POST.get('capacity', 4)

            try:
                cap = int(capacity)
            except (ValueError, TypeError):
                cap = 4

            from backend.apps.hostel.models import Hostel, HostelBlock, HostelBed, HostelRoom
            from backend.apps.tenants.models import School

            block = None
            if block_id:
                block = HostelBlock.objects.filter(id=block_id, tenant=tenant).first()
            elif hostel_id:
                hostel = Hostel.objects.filter(id=hostel_id, tenant=tenant).first()
                if hostel:
                    block, _ = HostelBlock.objects.get_or_create(
                        tenant=tenant,
                        hostel=hostel,
                        name='Main Block'
                    )

            if not block:
                # Get or create default hostel and block if none exist
                school = School.objects.filter(tenant=tenant).first()
                if school:
                    hostel, _ = Hostel.objects.get_or_create(
                        tenant=tenant,
                        school=school,
                        defaults={'name': 'Main Hostel', 'gender': 'mixed'}
                    )
                    block, _ = HostelBlock.objects.get_or_create(
                        tenant=tenant,
                        hostel=hostel,
                        defaults={'name': 'Block A'}
                    )

            if room_number and block:
                room = HostelRoom.objects.create(
                    tenant=tenant,
                    block=block,
                    room_number=room_number,
                    floor=floor or '1st Floor',
                    capacity=cap
                )
                # Auto-generate bed entries for capacity
                for i in range(1, cap + 1):
                    HostelBed.objects.create(
                        tenant=tenant,
                        room=room,
                        bed_number=f"Bed {i}",
                        status='available'
                    )

        return redirect('rooms_directory_web')

