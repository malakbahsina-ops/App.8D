from django.db import models
from core.models import TimeStampedModel

class BestPractice(TimeStampedModel):
    problem = models.ForeignKey('problems.Problem', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    tags = models.CharField(max_length=200, help_text="Comma separated tags")

    def __str__(self):
        return self.title
