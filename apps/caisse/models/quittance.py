"""
Modèle Quittance — Reçu de paiement patient.
App: caisse | Responsable: Charles-Henry
"""
from django.db import models
from django.db import transaction


class Quittance(models.Model):
    TYPE_RECETTE_CHOICES = [
        ('consultation', 'Consultation'),
        ('hospitalisation', 'Hospitalisation'),
        ('laboratoire', 'Laboratoire'),
        ('pharmacie', 'Pharmacie'),
        ('imagerie', 'Imagerie'),
        ('chirurgie', 'Chirurgie'),
        ('autre', 'Autre'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('carte', 'Carte Bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('virement', 'Virement Bancaire'),
        ('assurance', 'Assurance'),
    ]

    numero = models.CharField(
        max_length=20, unique=True, editable=False,
        verbose_name="Numéro de quittance",
        help_text="Auto-généré : QT-YYYY-NNNNN"
    )
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Montant total")
    motif = models.CharField(max_length=300, verbose_name="Motif")
    type_recette = models.CharField(max_length=20, choices=TYPE_RECETTE_CHOICES, verbose_name="Type de recette")
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, verbose_name="Mode de paiement")

    # Statuts
    est_validee = models.BooleanField(default=True, verbose_name="Validée par le caissier")
    est_urgence = models.BooleanField(default=False, verbose_name="Urgence (paiement différé)")
    est_comptabilisee = models.BooleanField(default=False, verbose_name="Comptabilisée")

    # Assurance
    est_assure = models.BooleanField(default=False, verbose_name="Patient assuré")
    taux_couverture = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Taux couverture (%)")
    montant_assurance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Part assurance")
    montant_patient = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Part patient")
    assurance_id = models.IntegerField(null=True, blank=True, verbose_name="ID Assurance", help_text="# EXT")

    # Compte tiers (assureur ou 411 clients divers)
    compte_tiers = models.ForeignKey(
        'comptabilite.CompteComptable',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='quittances_tiers',
        verbose_name="Compte tiers"
    )

    # Journal déterminé par mode de paiement
    journal = models.ForeignKey(
        'comptabilite.Journal',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='quittances',
        verbose_name="Journal comptable"
    )
    exercice = models.ForeignKey(
        'comptabilite.ExerciceComptable',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='quittances',
        verbose_name="Exercice comptable"
    )

    # Champs externes (EXT)
    caissier_id = models.IntegerField(null=True, blank=True, verbose_name="ID Caissier", help_text="# EXT")
    patient_id = models.IntegerField(null=True, blank=True, verbose_name="ID Patient", help_text="# EXT")
    session_id = models.IntegerField(null=True, blank=True, verbose_name="ID Session", help_text="# EXT")

    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Quittance"
        verbose_name_plural = "Quittances"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.numero} — {self.montant} FCFA ({self.mode_paiement})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        # Calcul automatique parts assurance/patient
        if self.est_assure and self.taux_couverture:
            self.montant_assurance = round(self.montant * self.taux_couverture / 100, 2)
            self.montant_patient = self.montant - self.montant_assurance
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from datetime import datetime
        annee = datetime.now().year
        prefix = f"QT-{annee}-"
        with transaction.atomic():
            dernier = Quittance.objects.select_for_update().filter(
                numero__startswith=prefix
            ).order_by('-numero').first()
            seq = 1
            if dernier:
                try:
                    seq = int(dernier.numero.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
        return f"{prefix}{seq:05d}"
