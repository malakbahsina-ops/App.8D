from django.db import models
from django.conf import settings
from core.models import TimeStampedModel

class Notification(TimeStampedModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    problem = models.ForeignKey('problems.Problem', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"To {self.recipient}: {self.message}"
