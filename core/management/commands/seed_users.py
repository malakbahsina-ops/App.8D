from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create demo users for each role'

    def handle(self, *args, **options):
        users_data = [
            {'username': 'operateur', 'role': 'OPERATOR', 'password': 'password123'},
            {'username': 'leader', 'role': 'TEAM_LEADER', 'password': 'password123'},
            {'username': 'superviseur', 'role': 'SUPERVISOR', 'password': 'password123'},
            {'username': 'responsable', 'role': 'RESPONSABLE', 'password': 'password123'},
            {'username': 'manager', 'role': 'MANAGER', 'password': 'password123'},
        ]

        self.stdout.write('Creating demo users...')

        for data in users_data:
            if not User.objects.filter(username=data['username']).exists():
                User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    role=data['role'],
                    email=f"{data['username']}@example.com"
                )
                self.stdout.write(self.style.SUCCESS(f"Created: {data['username']} ({data['role']})"))
            else:
                self.stdout.write(self.style.WARNING(f"Exists: {data['username']}"))

        # Ensure 'responsable' exists
        if not User.objects.filter(username='responsable').exists():
            User.objects.create_user(
                username='responsable',
                password='password123',
                role='RESPONSABLE',
                email='responsable@example.com'
            )
            self.stdout.write(self.style.SUCCESS("Created: responsable (RESPONSABLE)"))
        else:
            u = User.objects.get(username='responsable')
            u.role = 'RESPONSABLE'
            u.save()
            self.stdout.write(self.style.WARNING("Exists: responsable (role set to RESPONSABLE)"))

        # Migrate old 'qualite' user role to RESPONSABLE if exists (keep username to avoid conflict)
        if User.objects.filter(username='qualite').exists():
            uq = User.objects.get(username='qualite')
            uq.role = 'RESPONSABLE'
            uq.save()
            self.stdout.write(self.style.SUCCESS("Updated user 'qualite' role to RESPONSABLE"))
