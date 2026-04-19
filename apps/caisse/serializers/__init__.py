"""Serializers de l'app Caisse."""
from rest_framework import serializers
from apps.caisse.models import (
    Quittance, Cheque, PaiementMobile, PaiementCarte, VirementBancaire,
    CaisseJournaliere, DepenseMenue, InventaireCaisse,
)


class ChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cheque
        fields = ['id', 'numero', 'banque', 'titulaire', 'est_encaisse', 'date_encaissement']


class PaiementMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaiementMobile
        fields = ['id', 'operateur', 'numero_payant', 'reference_transaction']


class PaiementCarteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaiementCarte
        fields = ['id', 'quatre_derniers_chiffres', 'reference_transaction', 'id_terminal']


class VirementBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirementBancaire
        fields = ['id', 'banque_emettrice', 'reference', 'date_virement']


class QuittanceSerializer(serializers.ModelSerializer):
    cheque = ChequeSerializer(read_only=True)
    paiement_mobile = PaiementMobileSerializer(read_only=True)
    paiement_carte = PaiementCarteSerializer(read_only=True)
    virement = VirementBancaireSerializer(read_only=True)

    class Meta:
        model = Quittance
        fields = [
            'id', 'numero', 'montant', 'motif', 'type_recette', 'mode_paiement',
            'est_validee', 'est_urgence', 'est_comptabilisee',
            'est_assure', 'taux_couverture', 'montant_assurance', 'montant_patient',
            'assurance_id', 'compte_tiers', 'journal', 'exercice',
            'caissier_id', 'patient_id', 'session_id',
            'date_creation', 'date_modification',
            'cheque', 'paiement_mobile', 'paiement_carte', 'virement',
        ]
        read_only_fields = ['id', 'numero', 'date_creation', 'date_modification',
                            'montant_assurance', 'montant_patient']


class QuittanceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quittance
        fields = ['id', 'numero', 'montant', 'type_recette', 'mode_paiement',
                  'est_validee', 'est_comptabilisee', 'date_creation']


class ChequeDetailSerializer(serializers.ModelSerializer):
    quittance_numero = serializers.CharField(source='quittance.numero', read_only=True)
    montant = serializers.DecimalField(source='quittance.montant', max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Cheque
        fields = ['id', 'quittance', 'quittance_numero', 'montant',
                  'numero', 'banque', 'titulaire', 'est_encaisse', 'date_encaissement']


class CaisseJournaliereSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaisseJournaliere
        fields = [
            'id', 'date', 'solde_ouverture', 'solde_physique',
            'solde_theorique', 'ecart', 'statut', 'caissier_id',
            'date_creation', 'date_fermeture',
        ]
        read_only_fields = ['id', 'solde_theorique', 'ecart', 'date_creation']


class DepenseMenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepenseMenue
        fields = ['id', 'caisse', 'montant', 'motif', 'categorie_sortie',
                  'caissier_id', 'date_creation']
        read_only_fields = ['id', 'date_creation']


class InventaireCaisseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventaireCaisse
        fields = [
            'id', 'mois', 'annee', 'recettes_enregistrees', 'recettes_attendues',
            'ecart', 'ecart_justifie', 'observations', 'caissier_id',
            'comptable_id', 'statut', 'date_creation',
        ]
        read_only_fields = ['id', 'ecart', 'date_creation']
