from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Runs clear_demo then seed_all.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting reseed process...")
        
        call_command('clear_demo')
        call_command('seed_all')
        
        self.stdout.write(self.style.SUCCESS('Successfully reseeded the database.'))
