from rest_framework import serializers
from .models import BestPractice

class BestPracticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestPractice
        fields = '__all__'
