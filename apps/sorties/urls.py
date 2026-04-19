"""URLs de l'app sorties."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sorties.views import (
    CategorieSortieViewSet, FournisseurViewSet,
    DemandeAchatViewSet, BonCommandeViewSet,
    FactureViewSet, OrdrePaiementViewSet,
    PaiementSalaireViewSet, ChargeSocialeViewSet,
)

app_name = 'sorties'
router = DefaultRouter()
router.register(r'categories-sortie', CategorieSortieViewSet, basename='categorie-sortie')
router.register(r'fournisseurs', FournisseurViewSet, basename='fournisseur')
router.register(r'demandes-achat', DemandeAchatViewSet, basename='demande-achat')
router.register(r'bons-commande', BonCommandeViewSet, basename='bon-commande')
router.register(r'factures-fournisseur', FactureViewSet, basename='facture')
router.register(r'ordres-paiement', OrdrePaiementViewSet, basename='ordre-paiement')
router.register(r'salaires', PaiementSalaireViewSet, basename='salaire')
router.register(r'charges-sociales', ChargeSocialeViewSet, basename='charge-sociale')

urlpatterns = [
    path('', include(router.urls)),
]
