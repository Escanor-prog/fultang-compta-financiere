"""
Modèle ExerciceComptable — Exercice annuel.
App: comptabilite | Responsable: Passo
"""
from django.db import models


class ExerciceComptable(models.Model):
    """
    Exercice comptable (année civile : 1er janvier — 31 décembre).
    Un seul exercice peut être ouvert à la fois.
    """

    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('cloture', 'Clôturé'),
    ]

    annee = models.IntegerField(
        unique=True,
        verbose_name="Année",
        help_text="Année de l'exercice (ex: 2026)"
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    statut = models.CharField(
        max_length=10, choices=STATUT_CHOICES, default='ouvert',
        verbose_name="Statut"
    )
    resultat_net = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name="Résultat net",
        help_text="Calculé à la clôture : total produits (7) - total charges (6)"
    )
    date_cloture = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date de clôture"
    )
    cloture_par = models.IntegerField(
        null=True, blank=True,
        verbose_name="Clôturé par",
        help_text="# EXT — ID de l'utilisateur ayant clôturé"
    )
    observations = models.TextField(
        blank=True, null=True,
        verbose_name="Observations"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Exercice Comptable"
        verbose_name_plural = "Exercices Comptables"
        ordering = ['-annee']

    def __str__(self):
        return f"Exercice {self.annee} ({self.statut})"

    @property
    def est_ouvert(self):
        return self.statut == 'ouvert'
