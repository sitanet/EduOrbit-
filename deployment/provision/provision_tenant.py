#!/usr/bin/env python
import os
import sys
import argparse
import django

# Setup Django environment
sys.path.append('/var/www/eduorbit')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduorbit.settings')
django.setup()

from django.contrib.auth import get_user_model

def provision(tenant_name, domain_name):
    print(f"Provisioning tenant: {tenant_name} at {domain_name}")
    
    User = get_user_model()
    admin_email = f"admin@{domain_name}"
    if not User.objects.filter(email=admin_email).exists():
        User.objects.create_superuser(
            email=admin_email,
            password='InitialPassword123!',
            username=f"{tenant_name}_admin"
        )
        print(f"Admin user created: {admin_email}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant', required=True)
    parser.add_argument('--domain', required=True)
    args = parser.parse_args()
    
    provision(args.tenant, args.domain)
