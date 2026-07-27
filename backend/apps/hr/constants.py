"""
Constants & Choice Enums for HRPM Module.
"""

EMPLOYEE_LIFECYCLE_STATUS = [
    ('draft', 'Draft'),
    ('pending_verification', 'Pending Verification'),
    ('pending_approval', 'Pending Approval'),
    ('approved', 'Approved'),
    ('onboarding', 'Onboarding'),
    ('active', 'Active'),
    ('probation', 'Probation'),
    ('confirmed', 'Confirmed'),
    ('suspended', 'Suspended'),
    ('terminated', 'Terminated'),
    ('retired', 'Retired'),
    ('archived', 'Archived'),
]

EMPLOYEE_STATUS = [
    ('active', 'Active'),
    ('probation', 'Probation'),
    ('suspended', 'Suspended'),
    ('exited', 'Exited'),
    ('archived', 'Archived'),
]

EMPLOYMENT_TYPE = [
    ('full_time', 'Full Time'),
    ('part_time', 'Part Time'),
    ('permanent', 'Permanent'),
    ('contract', 'Contract'),
    ('temporary', 'Temporary'),
    ('consultant', 'Consultant'),
    ('volunteer', 'Volunteer'),
    ('intern', 'Intern'),
    ('nysc', 'NYSC Corp Member'),
    ('adjunct', 'Adjunct Teacher'),
    ('visiting', 'Visiting Lecturer'),
]

CONFIRMATION_STATUS = [
    ('probation', 'Probation'),
    ('confirmed', 'Confirmed'),
    ('extended', 'Extended Probation'),
    ('exited', 'Exited'),
]

REQUISITION_STATUS = [
    ('draft', 'Draft'),
    ('pending_approval', 'Pending Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]

VACANCY_STATUS = [
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('on_hold', 'On Hold'),
    ('closed', 'Closed'),
]

APPLICATION_STAGE = [
    ('applied', 'Applied'),
    ('screening', 'Screening'),
    ('interviewing', 'Interviewing'),
    ('offered', 'Offered'),
    ('accepted', 'Accepted'),
    ('hired', 'Hired'),
    ('rejected', 'Rejected'),
    ('future_pool', 'Future Hiring Pool'),
]

INTERVIEW_TYPE = [
    ('in_person', 'In Person'),
    ('virtual', 'Virtual Video Call'),
    ('phone', 'Phone Screening'),
]

ONBOARDING_CATEGORY = [
    ('contract', 'Contract & Agreements'),
    ('identity', 'Identity & Tax Verification'),
    ('background', 'Background & Reference Checks'),
    ('medical', 'Medical Clearance'),
    ('policy', 'Compliance & Safety Policies'),
    ('accounts', 'IT Accounts & Badges'),
]

LEAVE_STATUS = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('supervisor_approved', 'Supervisor Approved'),
    ('hr_approved', 'HR Approved'),
    ('completed', 'Completed'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]

PAYROLL_STATUS = [
    ('draft', 'Draft'),
    ('calculated', 'Calculated'),
    ('pending_approval', 'Pending Approval'),
    ('approved', 'Approved'),
    ('locked', 'Locked'),
    ('paid', 'Paid'),
    ('reversed', 'Reversed'),
]

DOCUMENT_TYPES = [
    ('cv', 'Curriculum Vitae (CV)'),
    ('appointment_letter', 'Appointment Letter'),
    ('contract', 'Employment Contract'),
    ('confirmation_letter', 'Confirmation Letter'),
    ('promotion_letter', 'Promotion Letter'),
    ('warning_letter', 'Warning Letter'),
    ('certificates', 'Academic & Professional Certificates'),
    ('id_card', 'ID Card'),
    ('passport_photo', 'Passport Photograph'),
    ('medical_certificate', 'Medical Clearance Certificate'),
    ('police_clearance', 'Police Background Clearance'),
]

TRAINING_STATUS = [
    ('scheduled', 'Scheduled'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]
