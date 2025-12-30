from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teams.models import Team

class Command(BaseCommand):
    help = 'Seed Teams and Members'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Define Teams structure
        teams_data = [
            {
                'name': 'Equipe Qualité',
                'dept': 'QUALITY',
                'respo_username': 'respo_qualite'
            },
            {
                'name': 'Equipe Production',
                'dept': 'PRODUCTION',
                'respo_username': 'respo_prod'
            },
            {
                'name': 'Equipe Maintenance',
                'dept': 'MAINTENANCE',
                'respo_username': 'respo_maint'
            },
            {
                'name': 'Equipe Logistique',
                'dept': 'LOGISTICS',
                'respo_username': 'respo_log'
            },
            {
                'name': 'Equipe Amélioration Continue',
                'dept': 'CONTINUOUS_IMPROVEMENT',
                'respo_username': 'respo_ci'
            }
        ]

        # Create generic supervisor if not exists for testing
        supervisor_generic, _ = User.objects.get_or_create(username='supervisor', defaults={'role': 'SUPERVISOR', 'email': 'sup@test.com'})
        supervisor_generic.set_password('password123')
        supervisor_generic.save()

        for t_data in teams_data:
            team, created = Team.objects.get_or_create(name=t_data['name'])
            if created:
                self.stdout.write(f"Created team: {team.name}")
            else:
                self.stdout.write(f"Team exists: {team.name}")

            # Add Responsable
            try:
                respo = User.objects.get(username=t_data['respo_username'])
                team.members.add(respo)
                self.stdout.write(f"Added {respo.username} to {team.name}")
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User {t_data['respo_username']} not found"))

            # Add generic supervisor to Quality team for testing
            if t_data['dept'] == 'QUALITY':
                team.members.add(supervisor_generic)
                self.stdout.write(f"Added supervisor to {team.name}")
        
        self.stdout.write(self.style.SUCCESS('Teams seeded successfully'))
