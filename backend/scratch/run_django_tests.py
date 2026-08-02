import os
import sys
import django

# Setup Django environment
sys.path.insert(0, r"c:\Users\user\Desktop\Development\SMS")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
django.setup()

from django.test.runner import DiscoverRunner

def run():
    runner = DiscoverRunner(verbosity=2, keepdb=True)
    failures = runner.run_tests(["backend.apps.academic.tests.test_academic_completion"])
    if failures:
        sys.exit(1)

if __name__ == "__main__":
    run()
