"""
Modèle Fournisseur.
App: sorties | Responsable: Moffo
"""
from django.db import models


class Fournisseur(models.Model):
    raison_sociale = models.CharField(max_length=200, verbose_name="Raison sociale")
    niu = models.CharField(max_length=50, blank=True, verbose_name="NIU")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    rib = models.CharField(max_length=100, blank=True, verbose_name="RIB")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    compte_comptable = models.ForeignKey(
        'comptabilite.CompteComptable',
        on_delete=models.PROTECT,
        related_name='fournisseurs',
        verbose_name="Compte fournisseur (401xxx)"
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['raison_sociale']

    def __str__(self):
        return self.raison_sociale
