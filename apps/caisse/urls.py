"""URLs de l'app caisse."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.caisse.views import (
    QuittanceViewSet, ChequeViewSet,
    CaisseJournaliereViewSet, InventaireCaisseViewSet, DepenseMenueViewSet,
)

app_name = 'caisse'
router = DefaultRouter()
router.register(r'quittances', QuittanceViewSet, basename='quittance')
router.register(r'cheques', ChequeViewSet, basename='cheque')
router.register(r'caisse-journaliere', CaisseJournaliereViewSet, basename='caisse-journaliere')
router.register(r'inventaires-caisse', InventaireCaisseViewSet, basename='inventaire-caisse')
router.register(r'depenses-menues', DepenseMenueViewSet, basename='depense-menue')

urlpatterns = [
    path('', include(router.urls)),
]
