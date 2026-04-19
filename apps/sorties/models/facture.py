"""
Modèles Facture, LigneFacture, OrdrePaiement.
App: sorties | Responsable: Moffo
"""
from django.db import models
from django.db import transaction
from datetime import datetime


class Facture(models.Model):
    bon_commande = models.ForeignKey(
        'sorties.BonCommande', on_delete=models.PROTECT,
        related_name='factures', null=True, blank=True
    )
    numero_facture = models.CharField(max_length=100, verbose_name="Numéro facture fournisseur")
    montant_ht = models.DecimalField(max_digits=15, decimal_places=2)
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2)
    est_payee = models.BooleanField(default=False)
    date_echeance = models.DateField(null=True, blank=True)
    date_reception = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Facture Fournisseur"
        verbose_name_plural = "Factures Fournisseurs"
        ordering = ['-date_reception']

    def __str__(self):
        return f"Facture {self.numero_facture} — {self.montant_ttc} FCFA"


class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    designation = models.CharField(max_length=300)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Ligne Facture"
        verbose_name_plural = "Lignes Facture"

    def __str__(self):
        return f"{self.designation} x{self.quantite}"


class OrdrePaiement(models.Model):
    TYPE_SORTIE_CHOICES = [
        ('fournisseur', 'Fournisseur'),
        ('salaire', 'Salaire'),
        ('remboursement', 'Remboursement'),
        ('charge', 'Charge'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('caisse', 'Caisse'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide_comptable', 'Validé comptable'),
        ('approuve_directeur', 'Approuvé directeur'),
        ('execute', 'Exécuté'),
    ]

    numero = models.CharField(max_length=20, unique=True, editable=False)
    facture = models.ForeignKey(
        Facture, on_delete=models.PROTECT,
        related_name='ordres_paiement', null=True, blank=True
    )
    type_sortie = models.CharField(max_length=20, choices=TYPE_SORTIE_CHOICES)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    mode_paiement = models.CharField(max_length=10, choices=MODE_PAIEMENT_CHOICES)
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='brouillon')
    est_comptabilise = models.BooleanField(default=False)
    beneficiaire = models.CharField(max_length=200, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_execution = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ordre de Paiement"
        verbose_name_plural = "Ordres de Paiement"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.numero} — {self.montant} FCFA ({self.statut})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        annee = datetime.now().year
        prefix = f"OP-{annee}-"
        with transaction.atomic():
            dernier = OrdrePaiement.objects.select_for_update().filter(
                numero__startswith=prefix
            ).order_by('-numero').first()
            seq = int(dernier.numero.split('-')[-1]) + 1 if dernier else 1
        return f"{prefix}{seq:05d}"
