"""Admin de l'app sorties — Moffo."""
from django.contrib import admin
from .models import CategorieSortie


@admin.register(CategorieSortie)
class CategorieSortieAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'type_categorie', 'compte_comptable')
    list_filter = ('type_categorie',)
    search_fields = ('code', 'libelle')
    ordering = ('code',)
