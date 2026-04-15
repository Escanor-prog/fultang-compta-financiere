"""URLs de l'app comptabilite — Passo."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.comptabilite.views import (
    CompteComptableViewSet,
    JournalViewSet,
    EcritureComptableViewSet,
    ExerciceComptableViewSet,
    BudgetPrevisionnelViewSet,
    PrestationDeServiceViewSet,
    EtatsFinanciersViewSet,
    AuditLogViewSet,
    TableauDeBordViewSet,
)

app_name = 'comptabilite'
router = DefaultRouter()

# 9 ViewSets — 34 endpoints au total
router.register(r'comptes-comptables', CompteComptableViewSet, basename='compte-comptable')
router.register(r'journaux', JournalViewSet, basename='journal')
router.register(r'ecritures', EcritureComptableViewSet, basename='ecriture')
router.register(r'exercices', ExerciceComptableViewSet, basename='exercice')
router.register(r'budgets', BudgetPrevisionnelViewSet, basename='budget')
router.register(r'prestations-de-service', PrestationDeServiceViewSet, basename='prestation')
router.register(r'etats-financiers', EtatsFinanciersViewSet, basename='etats-financiers')
router.register(r'audit-log', AuditLogViewSet, basename='audit-log')
router.register(r'tableau-de-bord', TableauDeBordViewSet, basename='tableau-de-bord')

urlpatterns = [
    path('', include(router.urls)),
]
