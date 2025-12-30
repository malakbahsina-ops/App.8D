from django.db import models
from django.conf import settings
from core.models import TimeStampedModel

class Problem(TimeStampedModel):
    LEVEL_FACTORY = 'FACTORY'
    LEVEL_WORKSHOP = 'WORKSHOP'
    LEVEL_LINE = 'LINE'
    LEVEL_CHOICES = (
        (LEVEL_FACTORY, 'Usine'),
        (LEVEL_WORKSHOP, 'Atelier'),
        (LEVEL_LINE, 'Ligne'),
    )
    
    STEP_CHOICES = [
        (f'D{i}', f'D{i}') for i in range(9)
    ]
    STATUS_CHOICES = (('OPEN', 'Ouvert'), ('CLOSED', 'Clôturé'))

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Symptôme initial")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    current_step = models.CharField(max_length=2, choices=STEP_CHOICES, default='D0')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_problems', on_delete=models.CASCADE)
    
    # D1 Team / Initial Data (Team Leader Form)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='led_problems', on_delete=models.SET_NULL, null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='problems_involved', blank=True)
    workstation = models.CharField(max_length=50, blank=True, verbose_name="Poste de travail")
    operator_id = models.CharField(max_length=50, blank=True, verbose_name="ID Opérateur")
    detection_method = models.CharField(max_length=255, blank=True, verbose_name="Méthode de détection")
    impacted_quantity = models.IntegerField(null=True, blank=True, verbose_name="Quantité impactée")
    importance = models.TextField(blank=True, verbose_name="Importance/Criticité")

    # Specific Location Details (Added for Operator)
    plant = models.CharField(max_length=50, blank=True, verbose_name="Usine")
    workshop_name = models.CharField(max_length=100, blank=True, verbose_name="Atelier")
    line_name = models.CharField(max_length=100, blank=True, verbose_name="Ligne")

    # D3 Decision (Supervisor Form)
    containment_actions = models.TextField(blank=True, verbose_name="Actions de sécurisation (D3)")
    process_continue = models.BooleanField(null=True, verbose_name="Laisser le processus continuer ?")
    observations = models.TextField(blank=True, verbose_name="Preuves / Observations")
    risk_personnel = models.BooleanField(null=True, verbose_name="Risque personnel ?")
    risk_equipment = models.BooleanField(null=True, verbose_name="Risque équipement ?")
    
    # Changed to CharField without choices to allow multiple selections (stored as comma-separated)
    non_conformity_type = models.CharField(max_length=255, blank=True, verbose_name="Type de non-conformité")
    
    # Validations
    immediate_actions_validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='validated_immediate_actions', null=True, blank=True, on_delete=models.SET_NULL)
    rca_validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='validated_rca', null=True, blank=True, on_delete=models.SET_NULL)
    final_report_validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='validated_final_reports', null=True, blank=True, on_delete=models.SET_NULL)

    # D2 QQOQCCP
    d2_who = models.TextField(blank=True, verbose_name="Qui")
    d2_what = models.TextField(blank=True, verbose_name="Quoi")
    d2_where = models.TextField(blank=True, verbose_name="Où")
    d2_when = models.TextField(blank=True, verbose_name="Quand")
    d2_how = models.TextField(blank=True, verbose_name="Comment")
    d2_how_many = models.TextField(blank=True, verbose_name="Combien")
    d2_why = models.TextField(blank=True, verbose_name="Pourquoi")
    d2_validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='validated_d2', null=True, blank=True, on_delete=models.SET_NULL)
    
    # D8
    closed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.current_step})"

class ProblemAttachment(TimeStampedModel):
    problem = models.ForeignKey(Problem, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='problems/attachments/')
    description = models.CharField(max_length=255, blank=True)

class RootCause(TimeStampedModel):
    CATEGORY_CHOICES = (
        ('METHOD', 'Méthode'),
        ('MACHINE', 'Machine'),
        ('MAN', 'Main d\'œuvre'),
        ('MATERIAL', 'Matière'),
        ('ENVIRONMENT', 'Milieu'),
        ('MEASURE', 'Mesure'),
    )
    ANALYSIS_METHOD_CHOICES = (
        ('5P', '5 Pourquoi'),
        ('ISHIKAWA', 'Ishikawa'),
        ('OTHER', 'Autre'),
    )
    problem = models.ForeignKey(Problem, related_name='root_causes', on_delete=models.CASCADE)
    description = models.TextField(verbose_name="Cause racine")
    details = models.TextField(blank=True, verbose_name="Explication détaillée")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    analysis_method = models.CharField(max_length=20, choices=ANALYSIS_METHOD_CHOICES, default='5P', verbose_name="Méthode d'analyse")
    other_method = models.CharField(max_length=255, blank=True, verbose_name="Autre méthode")
    is_root = models.BooleanField(default=False)
    why_number = models.IntegerField(default=1, help_text="Niveau dans le 5 Pourquoi")

class Action(TimeStampedModel):
    TYPE_CHOICES = (
        ('CONTAINMENT', 'Confinement (D3)'),
        ('CORRECTIVE', 'Corrective (D5)'),
        ('PREVENTIVE', 'Préventive (D7)'),
    )
    STATUS_CHOICES = (
        ('TODO', 'A faire'),
        ('IN_PROGRESS', 'En cours'),
        ('DONE', 'Fait'),
        ('VERIFIED', 'Vérifié'),
    )
    problem = models.ForeignKey(Problem, related_name='actions', on_delete=models.CASCADE)
    root_cause = models.ForeignKey(RootCause, related_name='actions', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    action_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assigned_actions', on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.description[:30]}"
