from rest_framework import viewsets, permissions
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(recipient=self.request.user).order_by('-created_at')

    def perform_destroy(self, instance):
        # Logic to notify Operator if Team Leader "views" (deletes) the notification
        if instance.problem and instance.recipient.role == 'TEAM_LEADER':
            # Check if this was a "New Problem" notification
            if "Nouveau problème" in instance.message:
                operator = instance.problem.created_by
                if operator:
                    Notification.objects.create(
                        recipient=operator,
                        message=f"Le Team Leader a consulté votre signalement : {instance.problem.title}",
                        problem=instance.problem
                    )
        
        instance.delete()
