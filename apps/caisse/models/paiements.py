"""
Modèles de paiement détaillés : Cheque, PaiementMobile, PaiementCarte, VirementBancaire.
App: caisse | Responsable: Charles-Henry
"""
from django.db import models


class Cheque(models.Model):
    quittance = models.OneToOneField(
        'caisse.Quittance', on_delete=models.CASCADE,
        related_name='cheque', verbose_name="Quittance"
    )
    numero = models.CharField(max_length=50, verbose_name="Numéro de chèque")
    banque = models.CharField(max_length=100, verbose_name="Banque")
    titulaire = models.CharField(max_length=200, verbose_name="Titulaire")
    est_encaisse = models.BooleanField(default=False, verbose_name="Encaissé")
    date_encaissement = models.DateField(null=True, blank=True, verbose_name="Date d'encaissement")

    class Meta:
        verbose_name = "Chèque"
        verbose_name_plural = "Chèques"

    def __str__(self):
        return f"Chèque {self.numero} — {self.banque}"


class PaiementMobile(models.Model):
    OPERATEUR_CHOICES = [
        ('orange', 'Orange Money'),
        ('mtn', 'MTN Mobile Money'),
    ]
    quittance = models.OneToOneField(
        'caisse.Quittance', on_delete=models.CASCADE,
        related_name='paiement_mobile', verbose_name="Quittance"
    )
    operateur = models.CharField(max_length=10, choices=OPERATEUR_CHOICES, verbose_name="Opérateur")
    numero_payant = models.CharField(max_length=20, verbose_name="Numéro du payant")
    reference_transaction = models.CharField(max_length=100, verbose_name="Référence transaction")

    class Meta:
        verbose_name = "Paiement Mobile"
        verbose_name_plural = "Paiements Mobile"

    def __str__(self):
        return f"{self.operateur} — {self.reference_transaction}"


class PaiementCarte(models.Model):
    quittance = models.OneToOneField(
        'caisse.Quittance', on_delete=models.CASCADE,
        related_name='paiement_carte', verbose_name="Quittance"
    )
    quatre_derniers_chiffres = models.CharField(max_length=4, verbose_name="4 derniers chiffres")
    reference_transaction = models.CharField(max_length=100, verbose_name="Référence transaction")
    id_terminal = models.CharField(max_length=50, verbose_name="ID Terminal")

    class Meta:
        verbose_name = "Paiement Carte"
        verbose_name_plural = "Paiements Carte"

    def __str__(self):
        return f"Carte ****{self.quatre_derniers_chiffres} — {self.reference_transaction}"


class VirementBancaire(models.Model):
    quittance = models.OneToOneField(
        'caisse.Quittance', on_delete=models.CASCADE,
        related_name='virement', verbose_name="Quittance"
    )
    banque_emettrice = models.CharField(max_length=100, verbose_name="Banque émettrice")
    reference = models.CharField(max_length=100, verbose_name="Référence virement")
    date_virement = models.DateField(verbose_name="Date du virement")

    class Meta:
        verbose_name = "Virement Bancaire"
        verbose_name_plural = "Virements Bancaires"

    def __str__(self):
        return f"Virement {self.reference} — {self.banque_emettrice}"
