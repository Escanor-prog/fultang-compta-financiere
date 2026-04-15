"""
Modèle AuditLog — Piste d'audit comptable.
App: comptabilite | Responsable: Passo
"""
from django.db import models


class AuditLog(models.Model):
    """
    Piste d'audit comptable — traçabilité de toutes les opérations.
    Exigé par SYSCOHADA pour la fiabilité des données comptables.
    """

    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('validation', 'Validation'),
        ('annulation', 'Annulation'),
        ('cloture', 'Clôture'),
        ('suppression', 'Suppression'),
    ]

    MODULE_CHOICES = [
        ('compte_comptable', 'Compte Comptable'),
        ('journal', 'Journal'),
        ('ecriture', 'Écriture Comptable'),
        ('exercice', 'Exercice Comptable'),
        ('budget', 'Budget Prévisionnel'),
        ('prestation', 'Prestation de Service'),
        ('quittance', 'Quittance'),
        ('bon_commande', 'Bon de Commande'),
        ('ordre_paiement', 'Ordre de Paiement'),
        ('caisse', 'Caisse Journalière'),
        ('inventaire', 'Inventaire Caisse'),
    ]

    date_action = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date et heure"
    )
    utilisateur_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID Utilisateur",
        help_text="# EXT — ID de l'utilisateur ayant effectué l'action"
    )
    utilisateur_nom = models.CharField(
        max_length=150, blank=True, null=True,
        verbose_name="Nom utilisateur",
        help_text="Nom complet dénormalisé pour la piste d'audit"
    )
    action = models.CharField(
        max_length=20, choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    module = models.CharField(
        max_length=30, choices=MODULE_CHOICES,
        verbose_name="Module"
    )
    objet_id = models.IntegerField(
        null=True, blank=True,
        verbose_name="ID de l'objet concerné"
    )
    objet_reference = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Référence",
        help_text="Numéro d'écriture, de quittance, etc."
    )
    description = models.TextField(
        verbose_name="Description de l'action"
    )
    donnees_avant = models.JSONField(
        null=True, blank=True,
        verbose_name="Données avant modification"
    )
    donnees_apres = models.JSONField(
        null=True, blank=True,
        verbose_name="Données après modification"
    )
    adresse_ip = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="Adresse IP"
    )

    class Meta:
        verbose_name = "Journal d'Audit"
        verbose_name_plural = "Journaux d'Audit"
        ordering = ['-date_action']
        indexes = [
            models.Index(fields=['-date_action']),
            models.Index(fields=['module', 'objet_id']),
            models.Index(fields=['utilisateur_id']),
        ]

    def __str__(self):
        return f"[{self.date_action:%Y-%m-%d %H:%M}] {self.action} — {self.module} — {self.objet_reference or self.objet_id}"

    @classmethod
    def log(cls, action, module, description, objet_id=None, objet_reference=None,
            utilisateur_id=None, utilisateur_nom=None, donnees_avant=None,
            donnees_apres=None, adresse_ip=None):
        """Méthode utilitaire pour créer facilement un log d'audit."""
        return cls.objects.create(
            action=action,
            module=module,
            description=description,
            objet_id=objet_id,
            objet_reference=objet_reference,
            utilisateur_id=utilisateur_id,
            utilisateur_nom=utilisateur_nom,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            adresse_ip=adresse_ip,
        )
