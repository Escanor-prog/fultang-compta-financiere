"""
Modèles CaisseJournaliere, DepenseMenue, InventaireCaisse.
App: caisse | Responsable: Charles-Henry
"""
from django.db import models
from django.core.exceptions import ValidationError


class CaisseJournaliere(models.Model):
    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('fermee', 'Fermée'),
    ]

    date = models.DateField(unique=True, verbose_name="Date")
    solde_ouverture = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Solde d'ouverture")
    solde_physique = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Solde physique (comptage réel)")
    solde_theorique = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Solde théorique (calculé)")
    ecart = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Écart")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ouverte', verbose_name="Statut")
    caissier_id = models.IntegerField(null=True, blank=True, verbose_name="ID Caissier", help_text="# EXT")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Caisse Journalière"
        verbose_name_plural = "Caisses Journalières"
        ordering = ['-date']

    def __str__(self):
        return f"Caisse {self.date} — {self.statut}"

    def calculer_solde_theorique(self):
        """Recalcule le solde théorique : ouverture + recettes - dépenses menues."""
        from django.db.models import Sum
        recettes = self.quittances_du_jour().aggregate(t=Sum('montant'))['t'] or 0
        depenses = self.depenses.aggregate(t=Sum('montant'))['t'] or 0
        return self.solde_ouverture + recettes - depenses

    def quittances_du_jour(self):
        from apps.caisse.models.quittance import Quittance
        return Quittance.objects.filter(
            date_creation__date=self.date,
            est_validee=True,
            mode_paiement='especes'
        )


class DepenseMenue(models.Model):
    caisse = models.ForeignKey(
        CaisseJournaliere, on_delete=models.CASCADE,
        related_name='depenses', verbose_name="Caisse journalière"
    )
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Montant")
    motif = models.CharField(max_length=300, verbose_name="Motif")
    categorie_sortie = models.ForeignKey(
        'sorties.CategorieSortie',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='depenses_menues',
        verbose_name="Catégorie de sortie"
    )
    caissier_id = models.IntegerField(null=True, blank=True, verbose_name="ID Caissier", help_text="# EXT")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dépense Menue"
        verbose_name_plural = "Dépenses Menues"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.motif} — {self.montant} FCFA"


class InventaireCaisse(models.Model):
    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('clos', 'Clos'),
    ]

    mois = models.IntegerField(verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    recettes_enregistrees = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Recettes enregistrées")
    recettes_attendues = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Recettes attendues")
    ecart = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Écart")
    ecart_justifie = models.BooleanField(default=False, verbose_name="Écart justifié")
    observations = models.TextField(blank=True, verbose_name="Observations")
    caissier_id = models.IntegerField(null=True, blank=True, verbose_name="ID Caissier", help_text="# EXT")
    comptable_id = models.IntegerField(null=True, blank=True, verbose_name="ID Comptable", help_text="# EXT")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ouvert', verbose_name="Statut")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inventaire de Caisse"
        verbose_name_plural = "Inventaires de Caisse"
        unique_together = ['mois', 'annee']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"Inventaire {self.mois:02d}/{self.annee} — {self.statut}"

    def save(self, *args, **kwargs):
        self.ecart = self.recettes_enregistrees - self.recettes_attendues
        super().save(*args, **kwargs)
