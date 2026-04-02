"""URLs de l'app sorties — Moffo."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'sorties'
router = DefaultRouter()

# Moffo : enregistre tes ViewSets ici
# router.register(r'fournisseurs', FournisseurViewSet, basename='fournisseur')

urlpatterns = [
    path('', include(router.urls)),
]
