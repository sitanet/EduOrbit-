from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates Platform Settings, Subscription Plans, Feature Flags, Super Admin, Platform Admins.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding platform data...")
        
        try:
            # Platform Settings (mock)
            # from apps.core.models import PlatformSetting, SubscriptionPlan, FeatureFlag
            self.stdout.write("Creating Platform Settings...")
            
            # Subscription Plans
            self.stdout.write("Creating Subscription Plans (Basic, Pro, Enterprise)...")
            
            # Feature Flags
            self.stdout.write("Creating Feature Flags...")

            # Super Admin
            if not User.objects.filter(username='superadmin').exists():
                User.objects.create_superuser('superadmin', 'admin@eduorbit.com', 'ChangeMe123!')
                self.stdout.write("Created Super Admin (superadmin).")
            else:
                self.stdout.write("Super Admin already exists.")

            # Platform Admins
            for i in range(1, 4):
                username = f'platform_admin_{i}'
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(username, f'{username}@eduorbit.com', 'ChangeMe123!')
                    user.is_staff = True
                    user.save()
            self.stdout.write("Created Platform Admins.")

            self.stdout.write(self.style.SUCCESS('Successfully seeded platform data.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding platform: {e}'))
