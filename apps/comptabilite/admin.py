"""Admin de l'app comptabilite — Passo."""
from django.contrib import admin
from .models import CompteComptable


@admin.register(CompteComptable)
class CompteComptableAdmin(admin.ModelAdmin):
    list_display = ('numero_compte', 'libelle', 'classe', 'type_compte', 'actif')
    list_filter = ('classe', 'type_compte', 'actif')
    search_fields = ('numero_compte', 'libelle')
    ordering = ('numero_compte',)
