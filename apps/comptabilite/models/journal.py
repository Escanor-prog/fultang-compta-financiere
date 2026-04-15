"""
Modèle Journal — Journaux Comptables.
App: comptabilite | Responsable: Passo
"""
from django.db import models


class Journal(models.Model):
    """
    Journal comptable OHADA.
    7 journaux : JA (Achats), JV (Ventes), JC (Caisse), JB (Banque),
    JMM (Mobile Money), JOD (Opérations Diverses), JRN (Report à Nouveau).
    """

    CODE_CHOICES = [
        ('JA', 'Journal des Achats'),
        ('JV', 'Journal des Ventes'),
        ('JC', 'Journal de Caisse'),
        ('JB', 'Journal de Banque'),
        ('JMM', 'Journal Mobile Money'),
        ('JOD', 'Journal des Opérations Diverses'),
        ('JRN', 'Journal de Report à Nouveau'),
    ]

    code = models.CharField(
        max_length=5, unique=True, choices=CODE_CHOICES,
        verbose_name="Code journal",
        help_text="Code unique du journal (ex: JC, JB)"
    )
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    compte_contrepartie = models.ForeignKey(
        'comptabilite.CompteComptable',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='journaux_contrepartie',
        verbose_name="Compte de contrepartie par défaut",
        help_text="Compte de trésorerie par défaut (571 pour JC, 521 pour JB, etc.)"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Journal Comptable"
        verbose_name_plural = "Journaux Comptables"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.libelle}"
