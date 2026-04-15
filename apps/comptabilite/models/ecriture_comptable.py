"""
Modèles EcritureComptable et LigneEcriture — Écritures en partie double.
App: comptabilite | Responsable: Passo
"""
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime


class EcritureComptable(models.Model):
    """
    Écriture comptable en partie double.
    Chaque écriture contient au minimum 2 lignes (débit et crédit).
    Auto-numérotation : EC-YYYY-NNNNN.
    """

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('annulee', 'Annulée'),
    ]

    numero_ecriture = models.CharField(
        max_length=20, unique=True, editable=False,
        verbose_name="Numéro d'écriture",
        help_text="Auto-généré : EC-YYYY-NNNNN"
    )
    date_ecriture = models.DateField(verbose_name="Date de l'écriture")
    libelle = models.CharField(max_length=300, verbose_name="Libellé de l'écriture")
    journal = models.ForeignKey(
        'comptabilite.Journal',
        on_delete=models.PROTECT,
        related_name='ecritures',
        verbose_name="Journal"
    )
    exercice = models.ForeignKey(
        'comptabilite.ExerciceComptable',
        on_delete=models.PROTECT,
        related_name='ecritures',
        verbose_name="Exercice comptable",
        null=True, blank=True
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon',
        verbose_name="Statut"
    )
    piece_justificative = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Pièce justificative",
        help_text="Numéro de quittance, facture, bon de commande, etc."
    )
    # Lien optionnel vers la quittance ou le bon de commande source
    quittance_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID Quittance source",
        help_text="# EXT — ID de la quittance dans l'app caisse"
    )
    bon_commande_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID Bon de commande source",
        help_text="# EXT — ID du bon de commande dans l'app sorties"
    )
    ordre_paiement_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID Ordre de paiement source",
        help_text="# EXT — ID de l'ordre de paiement dans l'app sorties"
    )
    created_by = models.IntegerField(
        null=True, blank=True,
        verbose_name="Créé par",
        help_text="# EXT — ID de l'utilisateur ayant créé l'écriture"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_validation = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date de validation"
    )

    class Meta:
        verbose_name = "Écriture Comptable"
        verbose_name_plural = "Écritures Comptables"
        ordering = ['-date_ecriture', '-numero_ecriture']

    def __str__(self):
        return f"{self.numero_ecriture} — {self.libelle} ({self.statut})"

    def save(self, *args, **kwargs):
        if not self.numero_ecriture:
            self.numero_ecriture = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        """Génère le numéro d'écriture : EC-YYYY-NNNNN."""
        annee = datetime.now().year
        prefix = f"EC-{annee}-"
        dernier = EcritureComptable.objects.filter(
            numero_ecriture__startswith=prefix
        ).order_by('-numero_ecriture').first()
        if dernier:
            try:
                seq = int(dernier.numero_ecriture.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:05d}"

    @property
    def total_debit(self):
        """Total des débits de l'écriture."""
        return sum(l.montant_debit or 0 for l in self.lignes.all())

    @property
    def total_credit(self):
        """Total des crédits de l'écriture."""
        return sum(l.montant_credit or 0 for l in self.lignes.all())

    @property
    def est_equilibree(self):
        """Vérifie que total débits == total crédits (tolérance 0.01)."""
        return abs(self.total_debit - self.total_credit) < 0.01


class LigneEcriture(models.Model):
    """
    Ligne d'une écriture comptable.
    Une ligne ne peut avoir qu'un montant au débit OU au crédit, pas les deux.
    """

    ecriture = models.ForeignKey(
        EcritureComptable,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Écriture"
    )
    compte = models.ForeignKey(
        'comptabilite.CompteComptable',
        on_delete=models.PROTECT,
        related_name='lignes_ecriture',
        verbose_name="Compte comptable"
    )
    libelle = models.CharField(
        max_length=300, blank=True, null=True,
        verbose_name="Libellé de la ligne"
    )
    montant_debit = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True, default=None,
        verbose_name="Montant débit"
    )
    montant_credit = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True, default=None,
        verbose_name="Montant crédit"
    )

    class Meta:
        verbose_name = "Ligne d'Écriture"
        verbose_name_plural = "Lignes d'Écriture"
        ordering = ['id']

    def __str__(self):
        direction = "D" if self.montant_debit else "C"
        montant = self.montant_debit or self.montant_credit or 0
        return f"{self.compte} | {direction} {montant}"

    def clean(self):
        """Valide qu'une ligne n'a pas simultanément un débit ET un crédit."""
        if self.montant_debit and self.montant_credit:
            raise ValidationError(
                "Une ligne ne peut pas avoir simultanément un montant au débit ET au crédit."
            )
        if not self.montant_debit and not self.montant_credit:
            raise ValidationError(
                "Une ligne doit avoir un montant au débit OU au crédit."
            )
