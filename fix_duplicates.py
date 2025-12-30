import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

print("Cleaning up duplicates and verifying departments...")

# 1. Fix Duplicates in QUALITY
qual_users = User.objects.filter(role='RESPONSABLE', department='QUALITY')
if qual_users.count() > 1:
    print(f"Found {qual_users.count()} users for QUALITY. Consolidating...")
    # Prefer 'respo_qualite' if exists, otherwise the most recently created or first one
    preferred = qual_users.filter(username='respo_qualite').first()
    if not preferred:
        preferred = qual_users.first()
    
    print(f"Keeping '{preferred.username}' as the main Responsable Qualité.")
    
    for u in qual_users:
        if u != preferred:
            print(f"  - Demoting '{u.username}' to OTHER department.")
            u.department = 'OTHER'
            # u.role = 'OPERATOR' # Optional: could also demote role
            u.save()
else:
    print("Responsable Qualité count is OK.")

# 2. Ensure Continuous Improvement exists
ci_users = User.objects.filter(role='RESPONSABLE', department='CONTINUOUS_IMPROVEMENT')
if not ci_users.exists():
    print("Creating Responsable Amélioration Continue...")
    User.objects.create_user(
        username='respo_amelioration',
        email='respo_amelioration@example.com',
        password='password123',
        role='RESPONSABLE',
        department='CONTINUOUS_IMPROVEMENT'
    )
else:
    print(f"Responsable Amélioration Continue already exists: {[u.username for u in ci_users]}")

print("\nFinal list of active Responsables:")
for u in User.objects.filter(role='RESPONSABLE').exclude(department='OTHER').order_by('department'):
    print(f"- {u.department}: {u.username}")
