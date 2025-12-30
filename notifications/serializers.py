from rest_framework import serializers
from .models import Notification
from problems.models import Problem

class ProblemSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'title', 'status', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    problem = ProblemSummarySerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
