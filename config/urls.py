from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/v1/auth/', include('djoser.urls')), # Removed djoser dependency
    # Let's use simplejwt routes directly as requested
    path('api/v1/token/', include('users.urls')), # Login/Refresh
    
    # App endpoints
    path('api/v1/users/', include('users.api_urls')),
    path('api/v1/problems/', include('problems.urls')),
    path('api/v1/teams/', include('teams.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/knowledge-base/', include('knowledge_base.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
