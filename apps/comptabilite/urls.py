"""URLs de l'app comptabilite — Passo."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'comptabilite'
router = DefaultRouter()

# Passo : enregistre tes ViewSets ici
# router.register(r'comptes-comptables', CompteComptableViewSet, basename='compte-comptable')

urlpatterns = [
    path('', include(router.urls)),
]
