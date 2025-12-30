import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team
from django.contrib.auth import get_user_model

User = get_user_model()

def recreate_maintenance():
    team, created = Team.objects.get_or_create(
        name='Maintenance',
        defaults={'description': 'Équipe Maintenance transverse'}
    )
    if created:
        print("Created 'Maintenance' team.")
    else:
        print("'Maintenance' team already exists.")
        
    # Assign members
    members_to_add = ['manager', 'respo_prod', 'leader_prod_a']
    users = User.objects.filter(username__in=members_to_add)
    for user in users:
        team.members.add(user)
        print(f"Added {user.username} to Maintenance.")

if __name__ == "__main__":
    recreate_maintenance()
