from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teams.models import Team

class Command(BaseCommand):
    help = 'Seed Full Organization Structure ensuring ALL users are in teams'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        self.stdout.write("Seeding Full Organization...")

        # 1. Retrieve or Create Key Users (Common Test Users)
        # We assume these might exist, if not we create them
        common_users = {
            'leader': 'TEAM_LEADER',
            'operateur': 'OPERATOR',
            'superviseur': 'SUPERVISOR',
            'manager': 'MANAGER',
            'respo_qualite': 'RESPONSABLE'
        }
        
        users_db = {}
        for username, role in common_users.items():
            u, created = User.objects.get_or_create(username=username, defaults={'role': role})
            if created:
                u.set_password('password123')
                u.save()
                self.stdout.write(f"Created common user: {username}")
            users_db[username] = u

        # 2. Define Teams Structure covering ALL roles
        # Team A: The "Standard" Test Team
        team_a_name = "Equipe Alpha (Test)"
        team_a, _ = Team.objects.get_or_create(name=team_a_name)
        
        # Assign 'leader' as leader of Team A
        team_a.leader = users_db['leader']
        team_a.save()
        
        # Add members to Team A
        team_a_members = [
            users_db['leader'],      # Leader is a member
            users_db['operateur'],   # Operator is a member
            users_db['superviseur'], # Supervisor is involved
            users_db['respo_qualite'] # Quality Respo is involved
        ]
        for m in team_a_members:
            team_a.members.add(m)
        self.stdout.write(f"Configured {team_a_name} with leader {users_db['leader'].username} and members.")

        # Team B: Management / Validation Team (Multi-team example)
        team_b_name = "Comité de Direction"
        team_b, _ = Team.objects.get_or_create(name=team_b_name)
        
        # Manager leads this team
        team_b.leader = users_db['manager']
        team_b.save()
        
        # Members: Manager, Supervisor (Multi-team!), Respo Qualite (Multi-team!)
        team_b_members = [
            users_db['manager'],
            users_db['superviseur'], # Also in Team A
            users_db['respo_qualite'] # Also in Team A
        ]
        for m in team_b_members:
            team_b.members.add(m)
        self.stdout.write(f"Configured {team_b_name} with leader {users_db['manager'].username} and cross-functional members.")

        # 3. Ensure ANY other orphan Team Leader in the DB has a team
        all_leaders = User.objects.filter(role='TEAM_LEADER')
        for ld in all_leaders:
            # Check if they lead a team
            if not ld.led_teams.exists():
                # Create a team for them
                t_name = f"Equipe de {ld.username}"
                t, created = Team.objects.get_or_create(name=t_name, defaults={'leader': ld})
                if created:
                    t.members.add(ld) # Add leader to their own team
                    self.stdout.write(f"Created orphan team {t_name} for leader {ld.username}")
                else:
                    # Update existing team leader if needed or just ensure membership
                    if t.leader != ld:
                        t.leader = ld
                        t.save()
                    t.members.add(ld)

        # 4. Ensure ANY other orphan Operator is in a team
        all_ops = User.objects.filter(role='OPERATOR')
        # Assign orphans to Team Alpha by default if they have no team
        for op in all_ops:
            if not op.teams.exists():
                team_a.members.add(op)
                self.stdout.write(f"Assigned orphan operator {op.username} to {team_a_name}")

        self.stdout.write(self.style.SUCCESS('Full Organization Seeded. All key users are in teams.'))
