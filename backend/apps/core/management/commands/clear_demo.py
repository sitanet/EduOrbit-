from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Wipes the database cleanly. Use with caution!'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Wiping the database cleanly..."))
        
        # NOTE: In a real Django environment, this can be destructive and complex due to FK constraints.
        # A common approach is using 'flush' or wiping specific models.
        
        from django.core.management import call_command
        call_command('flush', '--no-input')
        self.stdout.write(self.style.SUCCESS('Database cleared successfully.'))
