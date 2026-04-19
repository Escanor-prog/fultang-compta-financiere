"""
Modèles PaiementSalaire, ChargeSociale.
App: sorties | Responsable: Moffo
"""
from django.db import models


class PaiementSalaire(models.Model):
    mois = models.IntegerField(verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    # Données dénormalisées (EXT)
    personnel_id = models.IntegerField(null=True, blank=True, help_text="# EXT")
    nom_personnel = models.CharField(max_length=200, verbose_name="Nom complet")
    matricule = models.CharField(max_length=50, verbose_name="Matricule")
    poste = models.CharField(max_length=100, verbose_name="Poste")
    # Montants
    salaire_brut = models.DecimalField(max_digits=15, decimal_places=2)
    retenue_cnps = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retenue_impots = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deduction_ecart_caisse = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Déduction écart caisse")
    salaire_net = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    est_paye = models.BooleanField(default=False)
    date_paiement = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paiement Salaire"
        verbose_name_plural = "Paiements Salaires"
        unique_together = ['mois', 'annee', 'personnel_id']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"{self.nom_personnel} — {self.mois:02d}/{self.annee} — {self.salaire_net} FCFA"

    def save(self, *args, **kwargs):
        self.salaire_net = (
            self.salaire_brut
            - self.retenue_cnps
            - self.retenue_impots
            - self.deduction_ecart_caisse
        )
        super().save(*args, **kwargs)


class ChargeSociale(models.Model):
    TYPE_CHOICES = [
        ('cnps', 'CNPS'),
        ('assurance', 'Assurance'),
        ('impots', 'Impôts'),
    ]
    paiement_salaire = models.ForeignKey(
        PaiementSalaire, on_delete=models.CASCADE, related_name='charges_sociales'
    )
    type_charge = models.CharField(max_length=15, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Charge Sociale"
        verbose_name_plural = "Charges Sociales"

    def __str__(self):
        return f"{self.type_charge} — {self.montant} FCFA"
