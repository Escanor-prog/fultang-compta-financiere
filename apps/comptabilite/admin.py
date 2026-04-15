"""Admin de l'app Comptabilité — Passo."""
from django.contrib import admin
from apps.comptabilite.models import (
    CompteComptable, Journal, EcritureComptable, LigneEcriture,
    ExerciceComptable, BudgetPrevisionnel, PrestationDeService,
)


@admin.register(CompteComptable)
class CompteComptableAdmin(admin.ModelAdmin):
    list_display = ['numero_compte', 'libelle', 'classe', 'type_compte', 'actif']
    list_filter = ['classe', 'type_compte', 'actif']
    search_fields = ['numero_compte', 'libelle']
    ordering = ['numero_compte']


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'compte_contrepartie', 'actif']
    list_filter = ['actif']


class LigneEcritureInline(admin.TabularInline):
    model = LigneEcriture
    extra = 2
    fields = ['compte', 'libelle', 'montant_debit', 'montant_credit']


@admin.register(EcritureComptable)
class EcritureComptableAdmin(admin.ModelAdmin):
    list_display = ['numero_ecriture', 'date_ecriture', 'libelle', 'journal', 'statut']
    list_filter = ['statut', 'journal', 'date_ecriture']
    search_fields = ['numero_ecriture', 'libelle']
    inlines = [LigneEcritureInline]
    readonly_fields = ['numero_ecriture']


@admin.register(ExerciceComptable)
class ExerciceComptableAdmin(admin.ModelAdmin):
    list_display = ['annee', 'date_debut', 'date_fin', 'statut', 'resultat_net']
    list_filter = ['statut']


@admin.register(BudgetPrevisionnel)
class BudgetPrevisionnelAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'exercice', 'categorie', 'montant_prevu', 'montant_consomme', 'priorite']
    list_filter = ['exercice', 'priorite']


@admin.register(PrestationDeService)
class PrestationDeServiceAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'type_prestation', 'tarif', 'actif']
    list_filter = ['type_prestation', 'actif']
    search_fields = ['code', 'libelle']
