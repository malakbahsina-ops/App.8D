from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProblemViewSet, ActionViewSet, RootCauseViewSet, ProblemAttachmentViewSet

router = DefaultRouter()
router.register(r'list', ProblemViewSet)
router.register(r'actions', ActionViewSet)
router.register(r'root-causes', RootCauseViewSet)
router.register(r'attachments', ProblemAttachmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
