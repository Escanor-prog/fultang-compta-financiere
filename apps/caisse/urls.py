"""URLs de l'app caisse — Charles-Henry."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'caisse'
router = DefaultRouter()

# Charles-Henry : enregistre tes ViewSets ici
# router.register(r'quittances', QuittanceViewSet, basename='quittance')

urlpatterns = [
    path('', include(router.urls)),
]
