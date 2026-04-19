"""Serializers de l'app Sorties."""
from rest_framework import serializers
from apps.sorties.models import (
    CategorieSortie, Fournisseur,
    DemandeAchat, BonCommande, LigneBonCommande,
    Facture, LigneFacture, OrdrePaiement,
    PaiementSalaire, ChargeSociale,
)


class CategorieSortieSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieSortie
        fields = ['id', 'code', 'libelle', 'description', 'type_categorie', 'compte_comptable']


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ['id', 'raison_sociale', 'niu', 'telephone', 'email', 'rib',
                  'adresse', 'compte_comptable', 'actif', 'date_creation']
        read_only_fields = ['id', 'date_creation']


class LigneBonCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneBonCommande
        fields = ['id', 'designation', 'quantite', 'prix_unitaire', 'montant']
        read_only_fields = ['id', 'montant']


class BonCommandeSerializer(serializers.ModelSerializer):
    lignes = LigneBonCommandeSerializer(many=True, required=False)

    class Meta:
        model = BonCommande
        fields = ['id', 'numero', 'demande_achat', 'fournisseur', 'montant_total',
                  'statut', 'date_creation', 'lignes']
        read_only_fields = ['id', 'numero', 'date_creation']

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        bc = BonCommande.objects.create(**validated_data)
        total = 0
        for l in lignes_data:
            ligne = LigneBonCommande.objects.create(bon_commande=bc, **l)
            total += ligne.montant
        bc.montant_total = total
        bc.save()
        return bc


class DemandeAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeAchat
        fields = [
            'id', 'numero', 'service_demandeur_id', 'demandeur_id',
            'montant_estime', 'priorite', 'est_banque_de_sang',
            'avis_comptable', 'commentaire_budgetaire', 'statut',
            'description', 'date_creation',
        ]
        read_only_fields = ['id', 'numero', 'date_creation']


class LigneFactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneFacture
        fields = ['id', 'designation', 'quantite', 'prix_unitaire', 'taux_tva']


class FactureSerializer(serializers.ModelSerializer):
    lignes = LigneFactureSerializer(many=True, required=False)

    class Meta:
        model = Facture
        fields = ['id', 'bon_commande', 'numero_facture', 'montant_ht', 'montant_ttc',
                  'est_payee', 'date_echeance', 'date_reception', 'lignes']
        read_only_fields = ['id', 'date_reception']

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        facture = Facture.objects.create(**validated_data)
        for l in lignes_data:
            LigneFacture.objects.create(facture=facture, **l)
        return facture


class OrdrePaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdrePaiement
        fields = [
            'id', 'numero', 'facture', 'type_sortie', 'montant',
            'mode_paiement', 'statut', 'est_comptabilise',
            'beneficiaire', 'date_creation', 'date_execution',
        ]
        read_only_fields = ['id', 'numero', 'date_creation', 'date_execution']


class ChargeSocialeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeSociale
        fields = ['id', 'paiement_salaire', 'type_charge', 'montant', 'date_creation']
        read_only_fields = ['id', 'date_creation']


class PaiementSalaireSerializer(serializers.ModelSerializer):
    charges_sociales = ChargeSocialeSerializer(many=True, read_only=True)

    class Meta:
        model = PaiementSalaire
        fields = [
            'id', 'mois', 'annee', 'personnel_id', 'nom_personnel', 'matricule', 'poste',
            'salaire_brut', 'retenue_cnps', 'retenue_impots', 'deduction_ecart_caisse',
            'salaire_net', 'est_paye', 'date_paiement', 'date_creation', 'charges_sociales',
        ]
        read_only_fields = ['id', 'salaire_net', 'date_creation']
