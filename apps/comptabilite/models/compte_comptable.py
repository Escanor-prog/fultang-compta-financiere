"""
Modèle CompteComptable — Plan Comptable OHADA.
App: comptabilite | Responsable: Passo
"""
from django.db import models


class CompteComptable(models.Model):
    """
    Plan Comptable OHADA.
    Permet de catégoriser les recettes et dépenses selon les normes OHADA.
    """

    TYPE_COMPTE_CHOICES = [
        ('produit', 'Produit'),        # Classe 7
        ('charge', 'Charge'),          # Classe 6
        ('actif', 'Actif'),            # Classes 2, 3, 4, 5
        ('passif', 'Passif'),          # Classes 1, 4
        ('tresorerie', 'Trésorerie'),  # Classe 5
    ]

    CLASSE_CHOICES = [
        ('1', 'Classe 1 - Capitaux'),
        ('2', 'Classe 2 - Immobilisations'),
        ('3', 'Classe 3 - Stocks'),
        ('4', 'Classe 4 - Tiers'),
        ('5', 'Classe 5 - Trésorerie'),
        ('6', 'Classe 6 - Charges'),
        ('7', 'Classe 7 - Produits'),
    ]

    numero_compte = models.CharField(
        max_length=10, unique=True,
        verbose_name="Numéro de compte",
        help_text="Numéro du compte selon le plan OHADA (ex: 706100)"
    )
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    classe = models.CharField(max_length=1, choices=CLASSE_CHOICES, verbose_name="Classe")
    type_compte = models.CharField(max_length=20, choices=TYPE_COMPTE_CHOICES, verbose_name="Type de compte")
    compte_parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        related_name='sous_comptes',
        null=True, blank=True,
        verbose_name="Compte parent"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Compte Comptable"
        verbose_name_plural = "Comptes Comptables"
        ordering = ['numero_compte']

    def __str__(self):
        return f"{self.numero_compte} - {self.libelle}"

    @property
    def niveau(self):
        """Retourne le niveau hiérarchique du compte."""
        return len(self.numero_compte)
