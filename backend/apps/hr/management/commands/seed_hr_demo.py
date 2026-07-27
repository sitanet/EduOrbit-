import uuid
from decimal import Decimal
from datetime import date, datetime, time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.apps.identity.models import User, Role, TenantMembership
from backend.apps.tenants.models import Tenant, School
from backend.apps.people.models import Person, PersonRole, StaffProfile
from backend.apps.hr.models.employee import EmployeeProfile, OrgAssignmentHistory, HRAuditLog
from backend.apps.hr.models.settings import HRSettings
from backend.apps.hr.models.leave import LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, PublicHoliday
from backend.apps.hr.models.payroll import (
    PayrollPeriod, SalaryStructure, PayrollRun, PayrollPayslip, 
    PayrollGLAccount, PayrollAccountingConfiguration
)
from backend.apps.hr.models.attendance import (
    AttendanceShift, EmployeeShiftAssignment, AttendanceRecord, AttendanceAdjustment
)
from backend.apps.hr.models.recruitment import JobRequisition, JobVacancy, JobApplication

class Command(BaseCommand):
    help = "Seeds complete HR demo environment with 5 role-based accounts and full sample data."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Enterprise HR Demo Data...")

        # 1. Tenant & School
        tenant, _ = Tenant.objects.get_or_create(
            name="Grace Academy International",
            defaults={"legal_name": "Grace Academy Group"}
        )
        school, _ = School.objects.get_or_create(
            tenant=tenant,
            name="Grace Main Campus"
        )

        # 2. Roles
        roles_spec = [
            ("hr_admin", "HR Admin / Director"),
            ("payroll_admin", "Payroll Administrator"),
            ("supervisor", "Department Supervisor"),
            ("staff", "Staff / Teacher"),
            ("finance", "Finance Officer"),
        ]
        roles_dict = {}
        for code, name in roles_spec:
            r, _ = Role.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={"name": name, "description": f"{name} system role"}
            )
            roles_dict[code] = r

        # 3. Create 5 Accounts
        users_spec = [
            {
                "username": "hr.admin",
                "email": "hr.admin@eduorbit.com",
                "first_name": "Grace",
                "last_name": "Adeyemi",
                "job_title": "HR Director",
                "salary_grade": "grade_2",
                "role_code": "hr_admin",
                "emp_num": "EMP-001",
                "dept": "Human Resources"
            },
            {
                "username": "payroll.admin",
                "email": "payroll.admin@eduorbit.com",
                "first_name": "Tunde",
                "last_name": "Bakare",
                "job_title": "Payroll Specialist",
                "salary_grade": "grade_2",
                "role_code": "payroll_admin",
                "emp_num": "EMP-002",
                "dept": "Finance"
            },
            {
                "username": "dept.manager",
                "email": "dept.manager@eduorbit.com",
                "first_name": "Chioma",
                "last_name": "Okafor",
                "job_title": "Head of Sciences",
                "salary_grade": "grade_2",
                "role_code": "supervisor",
                "emp_num": "EMP-003",
                "dept": "Sciences"
            },
            {
                "username": "staff.member",
                "email": "staff.member@eduorbit.com",
                "first_name": "David",
                "last_name": "Eze",
                "job_title": "Biology Teacher",
                "salary_grade": "grade_1",
                "role_code": "staff",
                "emp_num": "EMP-004",
                "dept": "Sciences"
            },
            {
                "username": "finance.officer",
                "email": "finance.officer@eduorbit.com",
                "first_name": "Fatima",
                "last_name": "Bello",
                "job_title": "Financial Analyst",
                "salary_grade": "grade_1",
                "role_code": "finance",
                "emp_num": "EMP-005",
                "dept": "Finance"
            },
        ]

        employees = {}
        for spec in users_spec:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "is_active": True,
                    "email_verified": True
                }
            )
            if created or not user.check_password("Demo@2026"):
                user.set_password("Demo@2026")
                user.save()

            TenantMembership.objects.get_or_create(
                user=user,
                tenant=tenant,
                defaults={"role": roles_dict[spec["role_code"]], "primary_membership": True, "status": "active"}
            )

            person, _ = Person.objects.get_or_create(
                tenant=tenant,
                user=user,
                defaults={
                    "person_number": f"PER-{spec['emp_num']}",
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "gender": "female" if spec["first_name"] in ["Grace", "Chioma", "Fatima"] else "male",
                    "date_of_birth": date(1988, 5, 15)
                }
            )

            PersonRole.objects.get_or_create(
                tenant=tenant,
                person=person,
                role="staff",
                school=school
            )

            emp, _ = EmployeeProfile.objects.get_or_create(
                tenant=tenant,
                person=person,
                defaults={
                    "employee_number": spec["emp_num"],
                    "job_title": spec["job_title"],
                    "salary_grade": spec["salary_grade"],
                    "status": "active",
                    "confirmation_status": "confirmed",
                    "bank_name": "Zenith Bank",
                    "account_number": "1012345678",
                    "account_name": f"{spec['first_name']} {spec['last_name']}"
                }
            )
            employees[spec["username"]] = emp

            StaffProfile.objects.get_or_create(
                tenant=tenant,
                person=person,
                employee_number=spec["emp_num"],
                defaults={"role_type": "Teaching" if "Teacher" in spec["job_title"] else "Administrative"}
            )

        # Reporting lines: David Eze reports to Chioma Okafor, Chioma reports to Grace Adeyemi
        manager_chioma = employees["dept.manager"]
        manager_grace = employees["hr.admin"]

        for username, emp in employees.items():
            mgr = None
            if username == "staff.member":
                mgr = manager_chioma
            elif username in ["dept.manager", "payroll.admin", "finance.officer"]:
                mgr = manager_grace

            OrgAssignmentHistory.objects.get_or_create(
                tenant=tenant,
                employee=emp,
                is_active=True,
                defaults={
                    "campus_name": school.name,
                    "department_name": [s for s in users_spec if s["username"] == username][0]["dept"],
                    "job_position": emp.job_title,
                    "manager": mgr,
                    "cost_centre": "CC-01"
                }
            )

        # 4. Salary Structures
        SalaryStructure.objects.get_or_create(
            tenant=tenant,
            grade="grade_1",
            defaults={
                "base_salary": Decimal("150000.00"),
                "housing_allowance": Decimal("30000.00"),
                "transport_allowance": Decimal("20000.00"),
                "other_allowances": Decimal("10000.00"),
                "tax_deduction": Decimal("15000.00"),
                "pension_deduction": Decimal("12000.00"),
                "net_salary": Decimal("183000.00")
            }
        )
        SalaryStructure.objects.get_or_create(
            tenant=tenant,
            grade="grade_2",
            defaults={
                "base_salary": Decimal("250000.00"),
                "housing_allowance": Decimal("50000.00"),
                "transport_allowance": Decimal("35000.00"),
                "other_allowances": Decimal("15000.00"),
                "tax_deduction": Decimal("30000.00"),
                "pension_deduction": Decimal("20000.00"),
                "net_salary": Decimal("300000.00")
            }
        )

        # 5. Payroll GL Accounts & Config
        gl_sal, _ = PayrollGLAccount.objects.get_or_create(tenant=tenant, code="5001", defaults={"name": "Salaries & Wages Expense"})
        gl_paye, _ = PayrollGLAccount.objects.get_or_create(tenant=tenant, code="2101", defaults={"name": "PAYE Tax Liability"})
        gl_pen, _ = PayrollGLAccount.objects.get_or_create(tenant=tenant, code="2102", defaults={"name": "Pension Contribution Liability"})
        gl_net, _ = PayrollGLAccount.objects.get_or_create(tenant=tenant, code="2103", defaults={"name": "Net Salaries Payable"})
        gl_nhf, _ = PayrollGLAccount.objects.get_or_create(tenant=tenant, code="2104", defaults={"name": "NHF Liability"})

        PayrollAccountingConfiguration.objects.get_or_create(
            tenant=tenant,
            defaults={
                "salary_expense_account": gl_sal,
                "paye_liability_account": gl_paye,
                "pension_liability_account": gl_pen,
                "net_salary_liability_account": gl_net,
                "nhf_liability_account": gl_nhf
            }
        )

        # 6. Payroll Period & Run
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, 28)
        
        period, _ = PayrollPeriod.objects.get_or_create(
            tenant=tenant,
            name=f"{today.strftime('%B %Y')} Payroll",
            defaults={"start_date": start_date, "end_date": end_date, "status": "calculated"}
        )

        run, _ = PayrollRun.objects.get_or_create(
            tenant=tenant,
            period=period,
            defaults={
                "total_gross": Decimal("1100000.00"),
                "total_tax": Decimal("120000.00"),
                "total_pension": Decimal("88000.00"),
                "total_net": Decimal("864500.00"),
                "status": "calculated"
            }
        )

        for emp in employees.values():
            PayrollPayslip.objects.get_or_create(
                tenant=tenant,
                payroll_run=run,
                employee=emp,
                defaults={
                    "gross_pay": Decimal("210000.00"),
                    "tax_amount": Decimal("22000.00"),
                    "pension_amount": Decimal("16000.00"),
                    "net_pay": Decimal("168250.00"),
                    "base_salary": Decimal("150000.00"),
                    "housing_allowance": Decimal("30000.00"),
                    "transport_allowance": Decimal("20000.00"),
                    "other_allowances": Decimal("10000.00"),
                    "salary_grade": emp.salary_grade,
                    "working_days": 20,
                    "paid_days": 20,
                    "absent_days": 0,
                    "leave_days": 0
                }
            )

        # 7. Leave Types & Balances
        leave_annual, _ = LeaveType.objects.get_or_create(
            tenant=tenant, code="ANNUAL", defaults={"name": "Annual Leave", "default_days_per_year": 20, "is_paid": True}
        )
        leave_sick, _ = LeaveType.objects.get_or_create(
            tenant=tenant, code="SICK", defaults={"name": "Sick Leave", "default_days_per_year": 10, "is_paid": True}
        )

        for emp in employees.values():
            LeaveBalance.objects.get_or_create(
                tenant=tenant, employee=emp, leave_type=leave_annual,
                defaults={"leave_type_name": "Annual Leave", "allowed_days": 20, "used_days": 2, "remaining_days": 18}
            )
            LeaveBalance.objects.get_or_create(
                tenant=tenant, employee=emp, leave_type=leave_sick,
                defaults={"leave_type_name": "Sick Leave", "allowed_days": 10, "used_days": 0, "remaining_days": 10}
            )

        # Pending Leave Request from David Eze
        LeaveRequest.objects.get_or_create(
            tenant=tenant,
            employee=employees["staff.member"],
            leave_type=leave_annual,
            defaults={
                "leave_type_name": "Annual Leave",
                "start_date": today + timedelta(days=5),
                "end_date": today + timedelta(days=7),
                "days_requested": 3,
                "reason": "Family vacation and rest.",
                "status": "submitted"
            }
        )

        # 8. Attendance Shift & Records
        shift, _ = AttendanceShift.objects.get_or_create(
            tenant=tenant,
            code="MORNING",
            defaults={
                "name": "Morning Shift (8 AM - 4 PM)",
                "start_time": time(8, 0),
                "end_time": time(16, 0),
                "grace_minutes": 15,
                "minimum_hours": Decimal("7.00"),
                "overtime_after": Decimal("8.00")
            }
        )

        for emp in employees.values():
            EmployeeShiftAssignment.objects.get_or_create(
                tenant=tenant, employee=emp, shift=shift,
                defaults={"effective_from": date(2026, 1, 1)}
            )

        # Create past 5 days attendance records
        for i in range(5):
            rec_date = today - timedelta(days=i+1)
            if rec_date.weekday() < 5: # Weekdays
                for emp in employees.values():
                    rec, _ = AttendanceRecord.objects.get_or_create(
                        tenant=tenant,
                        employee=emp,
                        attendance_date=rec_date,
                        defaults={
                            "shift": shift,
                            "check_in": time(7, 55),
                            "check_out": time(16, 5),
                            "total_hours": Decimal("8.10"),
                            "overtime_hours": Decimal("0.10"),
                            "attendance_status": "Present"
                        }
                    )
                    # Create 1 adjustment for David Eze
                    if emp == employees["staff.member"] and i == 1:
                        AttendanceAdjustment.objects.get_or_create(
                            tenant=tenant,
                            attendance_record=rec,
                            defaults={
                                "reason": "System failed to register check-out time due to network timeout.",
                                "requested_by": emp,
                                "adjusted_check_in": time(8, 0),
                                "adjusted_check_out": time(16, 0),
                                "approval_status": "Pending"
                            }
                        )

        # 9. Public Holidays
        PublicHoliday.objects.get_or_create(
            tenant=tenant,
            name="Independence Day",
            date=date(2026, 10, 1),
            defaults={"holiday_name": "Independence Day", "recurring": True, "active": True}
        )

        # 10. HR Settings
        HRSettings.objects.get_or_create(
            tenant=tenant,
            defaults={
                "payroll_frequency": "monthly",
                "pension_employee_percentage": Decimal("8.00"),
                "pension_employer_percentage": Decimal("10.00"),
                "paye_tax_formula": "statutory_graduated",
                "enable_recruitment": True,
                "enable_payroll": True,
                "enable_performance": True
            }
        )

        self.stdout.write(self.style.SUCCESS("HR Demo Data seeded successfully!"))
        self.stdout.write(self.style.NOTICE("""
Demo Accounts Created (Password: Demo@2026):
1. HR Admin        : hr.admin@eduorbit.com (Username: hr.admin)
2. Payroll Admin   : payroll.admin@eduorbit.com (Username: payroll.admin)
3. Dept Supervisor : dept.manager@eduorbit.com (Username: dept.manager)
4. Staff Member    : staff.member@eduorbit.com (Username: staff.member)
5. Finance Officer : finance.officer@eduorbit.com (Username: finance.officer)
"""))
