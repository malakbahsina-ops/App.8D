from django.core.management.base import BaseCommand
from teams.models import Team
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Reorganize teams based on Atelier/Ligne structure'

    def handle(self, *args, **options):
        self.stdout.write("Reorganizing teams...")

        # Structure definition
        structure = [
            {'name': 'Atelier 1', 'description': 'Équipe dédiée à l\'Atelier 1'},
            {'name': 'Atelier 2', 'description': 'Équipe dédiée à l\'Atelier 2'},
            {'name': 'Atelier 3', 'description': 'Équipe dédiée à l\'Atelier 3'},
            {'name': 'Qualité', 'description': 'Équipe Qualité transverse'},
            {'name': 'Maintenance', 'description': 'Équipe Maintenance transverse'},
            {'name': 'Logistique', 'description': 'Équipe Logistique'},
        ]

        # Existing functional teams to keep or rename if needed
        # We will try to update existing teams or create new ones
        
        # 1. Clear existing teams if we want a fresh start? 
        # Or try to map them? Let's try to map or create.
        
        # For simplicity, let's ensure these specific teams exist
        for item in structure:
            team, created = Team.objects.get_or_create(
                name=item['name'],
                defaults={'description': item['description']}
            )
            if created:
                self.stdout.write(f"Created team: {team.name}")
            else:
                self.stdout.write(f"Team already exists: {team.name}")

        # 2. Assign some users if they exist
        # Let's find some users to assign randomly or specifically if we know them
        all_users = User.objects.all()
        
        # Example assignments logic (distribute users)
        teams = Team.objects.filter(name__in=[s['name'] for s in structure])
        
        for i, user in enumerate(all_users):
            # Skip admin or specific roles if needed, but for now assign everyone to a team
            if user.is_superuser:
                continue
                
            # Assign to a team in round-robin fashion
            team = teams[i % len(teams)]
            team.members.add(user)
            self.stdout.write(f"Assigned {user.username} to {team.name}")
            
            # If user has a leadership role (e.g. RESPONSIBLE), maybe make them leader
            if user.role == 'RESPONSIBLE' and not team.leader:
                team.leader = user
                team.save()
                self.stdout.write(f"Set {user.username} as leader of {team.name}")

        self.stdout.write(self.style.SUCCESS('Successfully reorganized teams'))
