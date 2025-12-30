from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teams.models import Team

class Command(BaseCommand):
    help = 'Seed Advanced Teams and Members (Multi-team membership)'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        self.stdout.write("Starting advanced team seeding...")

        # 1. Create specific users if they don't exist
        users_to_create = [
            {'username': 'leader_prod_a', 'role': 'TEAM_LEADER', 'dept': 'PRODUCTION'},
            {'username': 'op_prod_1', 'role': 'OPERATOR', 'dept': 'PRODUCTION'},
            {'username': 'op_prod_2', 'role': 'OPERATOR', 'dept': 'PRODUCTION'},
            {'username': 'expert_qualite', 'role': 'RESPONSABLE', 'dept': 'QUALITY'}, # Expert transversal
            {'username': 'expert_methodes', 'role': 'RESPONSABLE', 'dept': 'ENGINEERING'}, # Expert transversal
            {'username': 'maintenancier_1', 'role': 'OPERATOR', 'dept': 'MAINTENANCE'},
        ]

        created_users = {}
        for u_data in users_to_create:
            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults={
                    'role': u_data['role'],
                    'department': u_data['dept'],
                    'email': f"{u_data['username']}@test.com"
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"Created user: {user.username}")
            created_users[u_data['username']] = user

        # 2. Define Teams and their members
        # Structure: Team Name, Leader Username, List of Member Usernames
        teams_config = [
            {
                'name': 'Equipe Production A (Jour)',
                'leader': 'leader_prod_a',
                'members': ['op_prod_1', 'op_prod_2', 'expert_qualite', 'maintenancier_1']
            },
            {
                'name': 'Equipe Projet 8D Transverse',
                'leader': 'expert_methodes',
                'members': ['expert_qualite', 'op_prod_1', 'maintenancier_1'] # Note: op_prod_1 and expert_qualite are in multiple teams
            }
        ]

        for t_conf in teams_config:
            leader = created_users.get(t_conf['leader'])
            if not leader:
                try:
                    leader = User.objects.get(username=t_conf['leader'])
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Leader {t_conf['leader']} not found. Skipping team {t_conf['name']}"))
                    continue

            team, created = Team.objects.get_or_create(
                name=t_conf['name'],
                defaults={'leader': leader}
            )
            
            # Ensure leader is set correctly even if team existed
            team.leader = leader
            team.save()

            if created:
                self.stdout.write(f"Created team: {team.name}")
            else:
                self.stdout.write(f"Updated team: {team.name}")

            # Add members
            for member_username in t_conf['members']:
                member = created_users.get(member_username)
                if not member:
                     try:
                        member = User.objects.get(username=member_username)
                     except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Member {member_username} not found. Skipping."))
                        continue
                
                team.members.add(member)
                self.stdout.write(f"  -> Added {member.username} to {team.name}")

            # Also add leader to members if not implicitly done (though logic usually separates them, good to have in members for query simplicity)
            team.members.add(leader)
            self.stdout.write(f"  -> Added leader {leader.username} to {team.name}")

        self.stdout.write(self.style.SUCCESS('Advanced teams seeded successfully!'))
