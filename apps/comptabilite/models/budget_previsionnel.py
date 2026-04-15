"""
Modèle BudgetPrevisionnel — Budget par catégorie et service.
App: comptabilite | Responsable: Passo
"""
from django.db import models


class BudgetPrevisionnel(models.Model):
    """
    Budget prévisionnel par catégorie, par service hospitalier et par exercice.
    Permet de suivre le taux de consommation en temps réel.
    """

    PRIORITE_CHOICES = [
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]

    exercice = models.ForeignKey(
        'comptabilite.ExerciceComptable',
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name="Exercice"
    )
    categorie = models.ForeignKey(
        'sorties.CategorieSortie',
        on_delete=models.PROTECT,
        related_name='budgets',
        verbose_name="Catégorie de dépense"
    )
    libelle = models.CharField(max_length=200, verbose_name="Libellé du budget")
    service_hospitalier = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Service hospitalier",
        help_text="Nom du service (ex: Laboratoire, Radiologie, Chirurgie)"
    )
    service_hospitalier_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID Service hospitalier",
        help_text="# EXT — ID du service dans le microservice Personnel"
    )
    montant_prevu = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Montant prévu",
        help_text="Budget alloué en FCFA"
    )
    montant_consomme = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Montant consommé",
        help_text="Montant réellement dépensé"
    )
    priorite = models.CharField(
        max_length=10, choices=PRIORITE_CHOICES, default='normale',
        verbose_name="Priorité"
    )
    observations = models.TextField(blank=True, null=True, verbose_name="Observations")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Budget Prévisionnel"
        verbose_name_plural = "Budgets Prévisionnels"
        ordering = ['-exercice__annee', 'categorie']
        unique_together = ['exercice', 'categorie', 'service_hospitalier']

    def __str__(self):
        service = f" — {self.service_hospitalier}" if self.service_hospitalier else ""
        return f"{self.libelle}{service} (Ex. {self.exercice.annee})"

    @property
    def montant_disponible(self):
        """Budget restant."""
        return self.montant_prevu - self.montant_consomme

    @property
    def taux_consommation(self):
        """Pourcentage de consommation du budget."""
        if self.montant_prevu == 0:
            return 0
        return round((self.montant_consomme / self.montant_prevu) * 100, 2)
