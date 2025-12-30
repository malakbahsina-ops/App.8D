from rest_framework.routers import DefaultRouter
from .views import BestPracticeViewSet

router = DefaultRouter()
router.register(r'', BestPracticeViewSet)

urlpatterns = router.urls
