import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from problems.models import Problem
from django.contrib.auth import get_user_model

User = get_user_model()

def setup_data():
    # Ensure we have a user
    user = User.objects.first()
    if not user:
        print("No users found. Creating admin.")
        user = User.objects.create_superuser('admin', 'admin@example.com', 'password')

    # Check for D2 problems
    d2_problems = Problem.objects.filter(current_step='D2', d2_validated_by__isnull=True)
    
    if d2_problems.exists():
        print(f"Found {d2_problems.count()} problems in D2 waiting for validation.")
        for p in d2_problems:
            print(f"- {p.title} (ID: {p.id})")
    else:
        print("No problems in D2. Creating/Updating one...")
        
        # Try to find an existing problem to update
        p = Problem.objects.first()
        if not p:
            print("Creating new problem...")
            p = Problem.objects.create(
                title="Problème de Test Supervisor",
                description="Ceci est un problème de test pour vérifier le formulaire superviseur.",
                created_by=user,
                current_step='D2',
                status='OPEN'
            )
        else:
            print(f"Updating problem {p.title} to D2...")
            p.current_step = 'D2'
            p.d2_validated_by = None # Ensure it needs validation
            p.save()
            
        print(f"Problem '{p.title}' is now in D2.")

if __name__ == '__main__':
    setup_data()
