"""
Modèle CategorieSortie — Catégorisation des dépenses.
App: sorties | Responsable: Moffo

NOTE: Ce modèle est créé par Passo lors du setup car
l'app caisse (Charles-Henry) en dépend via DepenseMenue.
Moffo complètera ce modèle si nécessaire.
"""
from django.db import models


class CategorieSortie(models.Model):
    """
    Catégorie de sortie/dépense, liée au plan comptable OHADA.
    Ex: Médicaments (601), Fournitures de bureau (602), Charges de personnel (64), etc.
    """

    TYPE_CATEGORIE_CHOICES = [
        ('achat', 'Achat'),
        ('service', 'Service'),
        ('salaire', 'Salaire'),
        ('charge_sociale', 'Charge Sociale'),
        ('investissement', 'Investissement'),
        ('fonctionnement', 'Fonctionnement'),
        ('autre', 'Autre'),
    ]

    code = models.CharField(
        max_length=20, unique=True,
        verbose_name="Code catégorie",
        help_text="Code unique (ex: CAT-MED, CAT-FOUR)"
    )
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    type_categorie = models.CharField(
        max_length=20, choices=TYPE_CATEGORIE_CHOICES,
        verbose_name="Type de catégorie"
    )
    compte_comptable = models.ForeignKey(
        'comptabilite.CompteComptable',
        on_delete=models.PROTECT,
        related_name='categories_sortie',
        verbose_name="Compte comptable OHADA",
        help_text="Compte de charge OHADA associé (classe 6)"
    )

    class Meta:
        verbose_name = "Catégorie de Sortie"
        verbose_name_plural = "Catégories de Sortie"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.libelle}"
