def get_default_portal_preferences(role: str) -> dict:
    """
    Returns standard shortcuts and layout preferences for specific user roles.
    """
    defaults = {
        'parent': {
            'shortcuts': [
                {'name': 'Pay School Fees', 'url': '/portal/wallet/'},
                {'name': 'Report Cards', 'url': '/portal/results/'},
                {'name': 'Attendance Records', 'url': '/portal/attendance/'}
            ],
            'theme': 'light'
        },
        'student': {
            'shortcuts': [
                {'name': 'Join Virtual Class', 'url': '/portal/lms/'},
                {'name': 'Take CBT Test', 'url': '/portal/cbt/'},
                {'name': 'My Homeworks', 'url': '/portal/homework/'}
            ],
            'theme': 'dark'
        },
        'teacher': {
            'shortcuts': [
                {'name': 'Class Register', 'url': '/portal/register/'},
                {'name': 'Record Lesson Plan', 'url': '/portal/lesson-plans/'}
            ],
            'theme': 'light'
        }
    }
    return defaults.get(role.lower(), {'shortcuts': [], 'theme': 'light'})
