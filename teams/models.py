from django.db import models
from django.conf import settings
from core.models import TimeStampedModel

class Team(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='led_teams', on_delete=models.SET_NULL, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='teams')

    def __str__(self):
        return self.name
