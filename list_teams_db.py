import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team

def list_teams():
    teams = Team.objects.all().prefetch_related('members')
    print(f"Total teams found: {teams.count()}")
    print("-" * 50)
    for team in teams:
        print(f"Team: {team.name}")
        print(f"ID: {team.id}")
        if team.leader:
            print(f"Leader: {team.leader.username}")
        else:
            print("Leader: None")
        
        members = team.members.all()
        member_names = [m.username for m in members]
        print(f"Members ({len(members)}): {', '.join(member_names)}")
        print("-" * 50)

if __name__ == "__main__":
    list_teams()
