"""
Modèles DemandeAchat, BonCommande, LigneBonCommande.
App: sorties | Responsable: Moffo
"""
from django.db import models
from django.db import transaction
from datetime import datetime


class DemandeAchat(models.Model):
    PRIORITE_CHOICES = [
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    AVIS_CHOICES = [
        ('en_attente', 'En attente'),
        ('favorable', 'Favorable'),
        ('defavorable', 'Défavorable'),
    ]
    STATUT_CHOICES = [
        ('soumise', 'Soumise'),
        ('evaluee', 'Évaluée'),
        ('approuvee', 'Approuvée'),
        ('rejetee', 'Rejetée'),
    ]

    numero = models.CharField(max_length=20, unique=True, editable=False)
    service_demandeur_id = models.IntegerField(null=True, blank=True, help_text="# EXT")
    demandeur_id = models.IntegerField(null=True, blank=True, help_text="# EXT")
    montant_estime = models.DecimalField(max_digits=15, decimal_places=2)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    est_banque_de_sang = models.BooleanField(default=False, verbose_name="Banque de sang (prioritaire)")
    avis_comptable = models.CharField(max_length=15, choices=AVIS_CHOICES, default='en_attente', null=True, blank=True)
    commentaire_budgetaire = models.TextField(blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='soumise')
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Demande d'Achat"
        verbose_name_plural = "Demandes d'Achat"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.numero} — {self.montant_estime} FCFA ({self.statut})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        annee = datetime.now().year
        prefix = f"DA-{annee}-"
        with transaction.atomic():
            dernier = DemandeAchat.objects.select_for_update().filter(
                numero__startswith=prefix
            ).order_by('-numero').first()
            seq = int(dernier.numero.split('-')[-1]) + 1 if dernier else 1
        return f"{prefix}{seq:05d}"


class BonCommande(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide_comptable', 'Validé comptable'),
        ('approuve_directeur', 'Approuvé directeur'),
        ('envoye', 'Envoyé'),
    ]

    numero = models.CharField(max_length=20, unique=True, editable=False)
    demande_achat = models.ForeignKey(
        DemandeAchat, on_delete=models.PROTECT,
        related_name='bons_commande', null=True, blank=True
    )
    fournisseur = models.ForeignKey(
        'sorties.Fournisseur', on_delete=models.PROTECT,
        related_name='bons_commande'
    )
    montant_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='brouillon')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bon de Commande"
        verbose_name_plural = "Bons de Commande"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.numero} — {self.fournisseur} ({self.statut})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        annee = datetime.now().year
        prefix = f"BC-{annee}-"
        with transaction.atomic():
            dernier = BonCommande.objects.select_for_update().filter(
                numero__startswith=prefix
            ).order_by('-numero').first()
            seq = int(dernier.numero.split('-')[-1]) + 1 if dernier else 1
        return f"{prefix}{seq:05d}"


class LigneBonCommande(models.Model):
    bon_commande = models.ForeignKey(
        BonCommande, on_delete=models.CASCADE, related_name='lignes'
    )
    designation = models.CharField(max_length=300)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2)
    montant = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)

    class Meta:
        verbose_name = "Ligne Bon de Commande"
        verbose_name_plural = "Lignes Bon de Commande"

    def save(self, *args, **kwargs):
        self.montant = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.designation} x{self.quantite}"
