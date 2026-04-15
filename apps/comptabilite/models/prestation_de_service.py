"""
Modèle PrestationDeService — Tarifs des prestations hospitalières.
App: comptabilite | Responsable: Passo
"""
from django.db import models


class PrestationDeService(models.Model):
    """
    Tarification des prestations par service hospitalier.
    Supporte les paliers tarifaires (ex: hospitalisation 35 000 FCFA pour 1-5 jours).
    """

    TYPE_PRESTATION_CHOICES = [
        ('consultation', 'Consultation'),
        ('hospitalisation', 'Hospitalisation'),
        ('laboratoire', 'Laboratoire'),
        ('imagerie', 'Imagerie'),
        ('pharmacie', 'Pharmacie'),
        ('soins', 'Soins'),
        ('chirurgie', 'Chirurgie'),
        ('autre', 'Autre'),
    ]

    code = models.CharField(
        max_length=20, unique=True,
        verbose_name="Code prestation",
        help_text="Code unique (ex: PREST-CONS-001)"
    )
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    type_prestation = models.CharField(
        max_length=20, choices=TYPE_PRESTATION_CHOICES,
        verbose_name="Type de prestation"
    )
    service_hospitalier = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Service hospitalier"
    )
    service_hospitalier_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID Service hospitalier",
        help_text="# EXT — ID du service dans le microservice Personnel"
    )
    tarif = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Tarif (FCFA)",
        help_text="Tarif de base en FCFA"
    )
    # Paliers tarifaires pour l'hospitalisation
    duree_min_jours = models.IntegerField(
        null=True, blank=True,
        verbose_name="Durée minimale (jours)",
        help_text="Pour les paliers tarifaires (hospitalisation)"
    )
    duree_max_jours = models.IntegerField(
        null=True, blank=True,
        verbose_name="Durée maximale (jours)",
        help_text="Pour les paliers tarifaires (hospitalisation)"
    )
    compte_comptable = models.ForeignKey(
        'comptabilite.CompteComptable',
        on_delete=models.PROTECT,
        related_name='prestations',
        verbose_name="Compte de produit associé",
        help_text="Compte de classe 7 pour cette prestation"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Prestation de Service"
        verbose_name_plural = "Prestations de Service"
        ordering = ['type_prestation', 'code']

    def __str__(self):
        return f"{self.code} — {self.libelle} ({self.tarif} FCFA)"
