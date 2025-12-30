from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Team
from .serializers import TeamSerializer
from notifications.models import Notification

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None # Disable pagination to return simple list array

    @action(detail=True, methods=['post'])
    def congratulate(self, request, pk=None):
        team = self.get_object()
        # Congratulate all members
        for member in team.members.all():
            Notification.objects.create(
                recipient=member,
                message=f"Félicitations de la part du Manager pour l'excellent travail de l'équipe {team.name} !",
                problem=None # General notification
            )
        return Response({'status': 'Congratulations sent'})
