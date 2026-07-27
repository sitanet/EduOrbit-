import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.config.settings.local'

import django
django.setup()

from django.test.runner import DiscoverRunner

def run():
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(['backend.apps.hr.tests.test_hr'])
    if failures:
        sys.exit(1)
    print("\n=======================================================")
    print(" ALL SLICE 1 TESTS PASSED PERFECTLY WITH 0 FAILURES!")
    print("=======================================================\n")

if __name__ == '__main__':
    run()
