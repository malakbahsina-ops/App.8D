from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Seed specific responsables'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        respos = [
            {'username': 'respo_qualite', 'dept': 'QUALITY', 'email': 'qualite@example.com'},
            {'username': 'respo_prod', 'dept': 'PRODUCTION', 'email': 'prod@example.com'},
            {'username': 'respo_maint', 'dept': 'MAINTENANCE', 'email': 'maint@example.com'},
            {'username': 'respo_log', 'dept': 'LOGISTICS', 'email': 'log@example.com'},
            {'username': 'respo_ci', 'dept': 'CONTINUOUS_IMPROVEMENT', 'email': 'ci@example.com'},
        ]

        self.stdout.write("Seeding Responsables...")
        
        for r in respos:
            user, created = User.objects.get_or_create(
                username=r['username'],
                defaults={
                    'email': r['email'],
                    'role': 'RESPONSABLE',
                    'department': r['dept']
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created: {r['username']} ({r['dept']})"))
            else:
                user.role = 'RESPONSABLE'
                user.department = r['dept']
                if not user.check_password('password123'):
                    user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Updated: {r['username']} ({r['dept']})"))

        # Ensure Manager exists for notifications
        manager, created = User.objects.get_or_create(
            username='manager_demo',
            defaults={'role': 'MANAGER', 'email': 'manager@example.com'}
        )
        if created:
            manager.set_password('password123')
            manager.save()
            self.stdout.write(self.style.SUCCESS("Created Manager"))
        else:
            self.stdout.write(self.style.SUCCESS("Manager exists"))
