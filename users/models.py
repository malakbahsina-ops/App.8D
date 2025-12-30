from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('OPERATOR', 'Opérateur'),
        ('TEAM_LEADER', 'Chef d\'équipe'),
        ('SUPERVISOR', 'Superviseur'),
        ('RESPONSABLE', 'Responsable'),
        ('MANAGER', 'Manager'),
    )
    DEPARTMENT_CHOICES = (
        ('QUALITY', 'Qualité'),
        ('PRODUCTION', 'Production'),
        ('MAINTENANCE', 'Maintenance'),
        ('LOGISTICS', 'Logistique'),
        ('ENGINEERING', 'Ingénierie'),
        ('CONTINUOUS_IMPROVEMENT', 'Amélioration Continue'),
        ('HR', 'Ressources Humaines'),
        ('OTHER', 'Autre'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OPERATOR')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='OTHER', verbose_name="Département/Service")
    
    def __str__(self):
        dept = self.get_department_display() if self.department else ""
        return f"{self.username} ({self.get_role_display()}) - {dept}"
