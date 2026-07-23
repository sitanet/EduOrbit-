from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Runs seed_platform, seed_school, and seed_demo sequentially.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting complete platform seeding...")
        
        call_command('seed_platform')
        call_command('seed_school')
        call_command('seed_demo')
        
        self.stdout.write(self.style.SUCCESS('Successfully ran all seeders.'))
