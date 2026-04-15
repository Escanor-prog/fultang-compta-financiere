"""
Serializers de l'app Comptabilité — Passo.
"""
from rest_framework import serializers
from apps.comptabilite.models import (
    CompteComptable, Journal, EcritureComptable, LigneEcriture,
    ExerciceComptable, BudgetPrevisionnel, PrestationDeService,
    AuditLog,
)


# ===================== COMPTE COMPTABLE =====================

class CompteComptableSerializer(serializers.ModelSerializer):
    """Serializer complet pour CompteComptable."""
    niveau = serializers.ReadOnlyField()
    nombre_sous_comptes = serializers.SerializerMethodField()

    class Meta:
        model = CompteComptable
        fields = [
            'id', 'numero_compte', 'libelle', 'classe', 'type_compte',
            'compte_parent', 'description', 'actif', 'date_creation',
            'niveau', 'nombre_sous_comptes',
        ]
        read_only_fields = ['id', 'date_creation']

    def get_nombre_sous_comptes(self, obj):
        return obj.sous_comptes.count()


class CompteComptableArborescenceSerializer(serializers.ModelSerializer):
    """Serializer récursif pour l'arborescence du plan comptable."""
    sous_comptes = serializers.SerializerMethodField()
    niveau = serializers.ReadOnlyField()

    class Meta:
        model = CompteComptable
        fields = [
            'id', 'numero_compte', 'libelle', 'classe', 'type_compte',
            'actif', 'niveau', 'sous_comptes',
        ]

    def get_sous_comptes(self, obj):
        enfants = obj.sous_comptes.filter(actif=True).order_by('numero_compte')
        return CompteComptableArborescenceSerializer(enfants, many=True).data


class CompteComptableListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes déroulantes."""
    class Meta:
        model = CompteComptable
        fields = ['id', 'numero_compte', 'libelle', 'classe', 'type_compte']


# ===================== JOURNAL =====================

class JournalSerializer(serializers.ModelSerializer):
    """Serializer complet pour Journal."""
    compte_contrepartie_detail = CompteComptableListSerializer(
        source='compte_contrepartie', read_only=True
    )
    nombre_ecritures = serializers.SerializerMethodField()

    class Meta:
        model = Journal
        fields = [
            'id', 'code', 'libelle', 'description',
            'compte_contrepartie', 'compte_contrepartie_detail',
            'actif', 'date_creation', 'nombre_ecritures',
        ]
        read_only_fields = ['id', 'date_creation']

    def get_nombre_ecritures(self, obj):
        return obj.ecritures.count()


class JournalListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes."""
    class Meta:
        model = Journal
        fields = ['id', 'code', 'libelle']


# ===================== ÉCRITURE COMPTABLE =====================

class LigneEcritureSerializer(serializers.ModelSerializer):
    """Serializer pour LigneEcriture."""
    compte_detail = CompteComptableListSerializer(source='compte', read_only=True)

    class Meta:
        model = LigneEcriture
        fields = [
            'id', 'compte', 'compte_detail', 'libelle',
            'montant_debit', 'montant_credit',
        ]


class EcritureComptableSerializer(serializers.ModelSerializer):
    """Serializer complet pour EcritureComptable avec lignes imbriquées."""
    lignes = LigneEcritureSerializer(many=True)
    journal_detail = JournalListSerializer(source='journal', read_only=True)
    total_debit = serializers.ReadOnlyField()
    total_credit = serializers.ReadOnlyField()
    est_equilibree = serializers.ReadOnlyField()

    class Meta:
        model = EcritureComptable
        fields = [
            'id', 'numero_ecriture', 'date_ecriture', 'libelle',
            'journal', 'journal_detail', 'exercice', 'statut',
            'piece_justificative', 'quittance_id', 'bon_commande_id',
            'ordre_paiement_id', 'created_by',
            'date_creation', 'date_validation',
            'total_debit', 'total_credit', 'est_equilibree',
            'lignes',
        ]
        read_only_fields = ['id', 'numero_ecriture', 'date_creation', 'date_validation']

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        ecriture = EcritureComptable.objects.create(**validated_data)
        for ligne_data in lignes_data:
            LigneEcriture.objects.create(ecriture=ecriture, **ligne_data)
        return ecriture

    def validate_lignes(self, lignes):
        if len(lignes) < 2:
            raise serializers.ValidationError(
                "Une écriture doit contenir au minimum 2 lignes (débit et crédit)."
            )
        total_debit = sum(l.get('montant_debit') or 0 for l in lignes)
        total_credit = sum(l.get('montant_credit') or 0 for l in lignes)
        if abs(total_debit - total_credit) >= 0.01:
            raise serializers.ValidationError(
                f"L'écriture n'est pas équilibrée : débit={total_debit}, crédit={total_credit}."
            )
        for ligne in lignes:
            if ligne.get('montant_debit') and ligne.get('montant_credit'):
                raise serializers.ValidationError(
                    "Une ligne ne peut pas avoir simultanément un débit ET un crédit."
                )
            if not ligne.get('montant_debit') and not ligne.get('montant_credit'):
                raise serializers.ValidationError(
                    "Chaque ligne doit avoir un montant au débit OU au crédit."
                )
        return lignes


class EcritureComptableListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des écritures."""
    journal_code = serializers.CharField(source='journal.code', read_only=True)
    total_debit = serializers.ReadOnlyField()
    total_credit = serializers.ReadOnlyField()

    class Meta:
        model = EcritureComptable
        fields = [
            'id', 'numero_ecriture', 'date_ecriture', 'libelle',
            'journal_code', 'statut', 'total_debit', 'total_credit',
        ]


# ===================== EXERCICE COMPTABLE =====================

class ExerciceComptableSerializer(serializers.ModelSerializer):
    """Serializer pour ExerciceComptable."""
    est_ouvert = serializers.ReadOnlyField()
    nombre_ecritures = serializers.SerializerMethodField()

    class Meta:
        model = ExerciceComptable
        fields = [
            'id', 'annee', 'date_debut', 'date_fin', 'statut',
            'resultat_net', 'date_cloture', 'cloture_par',
            'observations', 'date_creation',
            'est_ouvert', 'nombre_ecritures',
        ]
        read_only_fields = ['id', 'date_creation', 'date_cloture', 'resultat_net']

    def get_nombre_ecritures(self, obj):
        return obj.ecritures.count()


# ===================== BUDGET PRÉVISIONNEL =====================

class BudgetPrevisionnelSerializer(serializers.ModelSerializer):
    """Serializer pour BudgetPrevisionnel."""
    montant_disponible = serializers.ReadOnlyField()
    taux_consommation = serializers.ReadOnlyField()
    exercice_annee = serializers.IntegerField(source='exercice.annee', read_only=True)
    categorie_libelle = serializers.CharField(source='categorie.libelle', read_only=True)

    class Meta:
        model = BudgetPrevisionnel
        fields = [
            'id', 'exercice', 'exercice_annee', 'categorie', 'categorie_libelle',
            'libelle', 'service_hospitalier', 'service_hospitalier_id',
            'montant_prevu', 'montant_consomme', 'priorite',
            'observations', 'date_creation', 'date_modification',
            'montant_disponible', 'taux_consommation',
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']


# ===================== PRESTATION DE SERVICE =====================

class PrestationDeServiceSerializer(serializers.ModelSerializer):
    """Serializer pour PrestationDeService."""
    compte_comptable_detail = CompteComptableListSerializer(
        source='compte_comptable', read_only=True
    )

    class Meta:
        model = PrestationDeService
        fields = [
            'id', 'code', 'libelle', 'type_prestation',
            'service_hospitalier', 'service_hospitalier_id',
            'tarif', 'duree_min_jours', 'duree_max_jours',
            'compte_comptable', 'compte_comptable_detail',
            'description', 'actif', 'date_creation',
        ]
        read_only_fields = ['id', 'date_creation']


# ===================== AUDIT LOG =====================

class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer pour AuditLog."""
    class Meta:
        model = AuditLog
        fields = [
            'id', 'date_action', 'utilisateur_id', 'utilisateur_nom',
            'action', 'module', 'objet_id', 'objet_reference',
            'description', 'donnees_avant', 'donnees_apres', 'adresse_ip',
        ]
        read_only_fields = ['id', 'date_action']
