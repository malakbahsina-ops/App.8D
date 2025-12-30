import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team

def cleanup_teams():
    allowed_names = [
        'Atelier 1', 'Atelier 2', 'Atelier 3',
        'Qualité', 'Maintenance', 'Logistique'
    ]
    
    # Find teams that are NOT in the allowed list
    teams_to_delete = Team.objects.exclude(name__in=allowed_names)
    
    print(f"Found {teams_to_delete.count()} teams to delete.")
    
    for team in teams_to_delete:
        print(f"Deleting team: {team.name} (ID: {team.id})")
        team.delete()
        
    print("Cleanup complete.")
    
    # Verify remaining teams
    remaining_teams = Team.objects.all()
    print(f"Remaining teams: {remaining_teams.count()}")
    for team in remaining_teams:
        print(f"- {team.name}")

if __name__ == "__main__":
    cleanup_teams()
