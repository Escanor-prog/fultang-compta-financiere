"""
URLs principales du Service Comptabilité Financière.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def health_check(request):
    """Endpoint de santé de l'API."""
    return Response({
        'service': 'Comptabilité Financière',
        'status': 'ok',
        'version': '1.0.0'
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    # Apps
    path('api/', include('apps.comptabilite.urls')),
    path('api/', include('apps.caisse.urls')),
    path('api/', include('apps.sorties.urls')),
    # Documentation Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
