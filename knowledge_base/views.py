from rest_framework import viewsets, permissions
from .models import BestPractice
from .serializers import BestPracticeSerializer

class BestPracticeViewSet(viewsets.ModelViewSet):
    queryset = BestPractice.objects.all()
    serializer_class = BestPracticeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
