"""ViewSets de l'app Sorties — 19 endpoints."""
from django.utils import timezone
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.sorties.models import (
    CategorieSortie, Fournisseur,
    DemandeAchat, BonCommande, LigneBonCommande,
    Facture, LigneFacture, OrdrePaiement,
    PaiementSalaire, ChargeSociale,
)
from apps.sorties.serializers import (
    CategorieSortieSerializer, FournisseurSerializer,
    DemandeAchatSerializer, BonCommandeSerializer,
    FactureSerializer, OrdrePaiementSerializer,
    PaiementSalaireSerializer, ChargeSocialeSerializer,
)


class CategorieSortieViewSet(viewsets.ModelViewSet):
    queryset = CategorieSortie.objects.all()
    serializer_class = CategorieSortieSerializer
    filter_backends = [SearchFilter]
    search_fields = ['code', 'libelle']


class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['actif']
    search_fields = ['raison_sociale', 'niu']
    ordering = ['raison_sociale']

    @action(detail=True, methods=['get'], url_path='historique')
    def historique(self, request, pk=None):
        fournisseur = self.get_object()
        bons = fournisseur.bons_commande.all()
        return Response({
            'fournisseur': fournisseur.raison_sociale,
            'nombre_commandes': bons.count(),
            'total_commandes': float(bons.aggregate(t=Sum('montant_total'))['t'] or 0),
        })


class DemandeAchatViewSet(viewsets.ModelViewSet):
    queryset = DemandeAchat.objects.all()
    serializer_class = DemandeAchatSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'priorite', 'est_banque_de_sang']
    search_fields = ['numero', 'description']
    ordering = ['-date_creation']

    @action(detail=True, methods=['patch'], url_path='evaluer')
    def evaluer(self, request, pk=None):
        """Évaluation budgétaire par le comptable."""
        da = self.get_object()
        avis = request.data.get('avis_comptable')
        if avis not in ['favorable', 'defavorable']:
            return Response({'error': "avis_comptable doit être 'favorable' ou 'defavorable'."}, status=400)
        da.avis_comptable = avis
        da.commentaire_budgetaire = request.data.get('commentaire_budgetaire', '')
        da.statut = 'evaluee'
        da.save()
        return Response(DemandeAchatSerializer(da).data)

    @action(detail=True, methods=['patch'], url_path='approuver')
    def approuver(self, request, pk=None):
        """Approbation par le directeur."""
        da = self.get_object()
        if da.statut not in ['evaluee', 'soumise'] and not da.est_banque_de_sang:
            return Response({'error': 'La demande doit être évaluée avant approbation.'}, status=400)
        da.statut = 'approuvee'
        da.save()
        return Response(DemandeAchatSerializer(da).data)


class BonCommandeViewSet(viewsets.ModelViewSet):
    queryset = BonCommande.objects.prefetch_related('lignes').select_related('fournisseur')
    serializer_class = BonCommandeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'fournisseur']
    search_fields = ['numero']
    ordering = ['-date_creation']

    @action(detail=True, methods=['patch'], url_path='valider')
    def valider(self, request, pk=None):
        bc = self.get_object()
        if bc.statut != 'brouillon':
            return Response({'error': 'Seul un bon en brouillon peut être validé.'}, status=400)
        bc.statut = 'valide_comptable'
        bc.save()
        return Response(BonCommandeSerializer(bc).data)


class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.prefetch_related('lignes')
    serializer_class = FactureSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['est_payee']
    ordering = ['-date_reception']

    @action(detail=False, methods=['get'], url_path='impayees')
    def impayees(self, request):
        qs = self.get_queryset().filter(est_payee=False)
        return Response({
            'nombre': qs.count(),
            'total': float(qs.aggregate(t=Sum('montant_ttc'))['t'] or 0),
            'factures': FactureSerializer(qs, many=True).data,
        })


class OrdrePaiementViewSet(viewsets.ModelViewSet):
    queryset = OrdrePaiement.objects.all()
    serializer_class = OrdrePaiementSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'type_sortie', 'mode_paiement']
    search_fields = ['numero', 'beneficiaire']
    ordering = ['-date_creation']

    @action(detail=True, methods=['patch'], url_path='valider')
    def valider(self, request, pk=None):
        op = self.get_object()
        if op.statut != 'brouillon':
            return Response({'error': 'Seul un ordre en brouillon peut être validé.'}, status=400)
        op.statut = 'valide_comptable'
        op.save()
        return Response(OrdrePaiementSerializer(op).data)

    @action(detail=True, methods=['patch'], url_path='approuver')
    def approuver(self, request, pk=None):
        op = self.get_object()
        if op.statut != 'valide_comptable':
            return Response({'error': "L'ordre doit être validé par le comptable d'abord."}, status=400)
        op.statut = 'approuve_directeur'
        op.save()
        return Response(OrdrePaiementSerializer(op).data)

    @action(detail=True, methods=['patch'], url_path='executer')
    def executer(self, request, pk=None):
        op = self.get_object()
        if op.statut != 'approuve_directeur':
            return Response({'error': "L'ordre doit être approuvé par le directeur d'abord."}, status=400)
        op.statut = 'execute'
        op.date_execution = timezone.now()
        op.save()
        # Marquer la facture comme payée si liée
        if op.facture:
            op.facture.est_payee = True
            op.facture.save()
        return Response(OrdrePaiementSerializer(op).data)


class PaiementSalaireViewSet(viewsets.ModelViewSet):
    queryset = PaiementSalaire.objects.prefetch_related('charges_sociales')
    serializer_class = PaiementSalaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['mois', 'annee', 'est_paye']
    search_fields = ['nom_personnel', 'matricule']
    ordering = ['-annee', '-mois']

    @action(detail=False, methods=['post'], url_path='generer')
    def generer(self, request):
        """Génère les bulletins de paie pour un mois/année donné."""
        mois = request.data.get('mois', timezone.now().month)
        annee = request.data.get('annee', timezone.now().year)
        personnels = request.data.get('personnels', [])
        created = []
        for p in personnels:
            sal, _ = PaiementSalaire.objects.get_or_create(
                mois=mois, annee=annee, personnel_id=p.get('personnel_id'),
                defaults={
                    'nom_personnel': p.get('nom_personnel', ''),
                    'matricule': p.get('matricule', ''),
                    'poste': p.get('poste', ''),
                    'salaire_brut': p.get('salaire_brut', 0),
                    'retenue_cnps': p.get('retenue_cnps', 0),
                    'retenue_impots': p.get('retenue_impots', 0),
                }
            )
            created.append(sal)
        return Response({
            'mois': mois, 'annee': annee,
            'bulletins_crees': len(created),
            'salaires': PaiementSalaireSerializer(created, many=True).data,
        }, status=201)

    @action(detail=True, methods=['patch'], url_path='payer')
    def payer(self, request, pk=None):
        sal = self.get_object()
        if sal.est_paye:
            return Response({'error': 'Ce salaire est déjà payé.'}, status=400)
        sal.est_paye = True
        sal.date_paiement = timezone.now()
        sal.save()
        return Response(PaiementSalaireSerializer(sal).data)

    @action(detail=False, methods=['get'], url_path='masse-salariale')
    def masse_salariale(self, request):
        qs = self.get_queryset()
        annee = request.query_params.get('annee', timezone.now().year)
        qs = qs.filter(annee=annee)
        return Response({
            'annee': annee,
            'total_brut': float(qs.aggregate(t=Sum('salaire_brut'))['t'] or 0),
            'total_net': float(qs.aggregate(t=Sum('salaire_net'))['t'] or 0),
            'nombre_bulletins': qs.count(),
        })


class ChargeSocialeViewSet(viewsets.ModelViewSet):
    queryset = ChargeSociale.objects.all()
    serializer_class = ChargeSocialeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type_charge', 'paiement_salaire']
