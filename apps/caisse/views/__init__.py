"""ViewSets de l'app Caisse — 28 endpoints."""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Q
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.caisse.models import (
    Quittance, Cheque, PaiementMobile, PaiementCarte, VirementBancaire,
    CaisseJournaliere, DepenseMenue, InventaireCaisse,
)
from apps.caisse.serializers import (
    QuittanceSerializer, QuittanceListSerializer,
    ChequeDetailSerializer,
    CaisseJournaliereSerializer, DepenseMenueSerializer, InventaireCaisseSerializer,
)


# ─────────────────────────────────────────────────────────────────────
#  QUITTANCES  (13 endpoints)
# ─────────────────────────────────────────────────────────────────────

class QuittanceViewSet(viewsets.ModelViewSet):
    queryset = Quittance.objects.select_related('journal', 'exercice', 'compte_tiers')
    serializer_class = QuittanceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type_recette', 'mode_paiement', 'est_validee', 'est_comptabilisee', 'est_urgence']
    search_fields = ['numero', 'motif']
    ordering_fields = ['date_creation', 'montant']
    ordering = ['-date_creation']

    def get_serializer_class(self):
        if self.action == 'list':
            return QuittanceListSerializer
        return QuittanceSerializer

    def perform_create(self, serializer):
        """Assigne automatiquement le journal selon le mode de paiement."""
        from apps.comptabilite.models import Journal, ExerciceComptable
        instance = serializer.save()
        # Déterminer le journal
        mapping = {
            'especes': 'JC',
            'cheque': 'JB',
            'carte': 'JB',
            'mobile_money': 'JMM',
            'virement': 'JB',
            'assurance': 'JOD',
        }
        code_journal = mapping.get(instance.mode_paiement, 'JOD')
        try:
            journal = Journal.objects.get(code=code_journal)
            instance.journal = journal
        except Journal.DoesNotExist:
            pass
        # Exercice courant
        try:
            exercice = ExerciceComptable.objects.get(statut='ouvert')
            instance.exercice = exercice
        except ExerciceComptable.DoesNotExist:
            pass
        instance.save()

    @action(detail=False, methods=['get'], url_path='a_comptabiliser')
    def a_comptabiliser(self, request):
        """Quittances validées non encore comptabilisées — pour le comptable."""
        qs = self.get_queryset().filter(est_validee=True, est_comptabilisee=False)
        serializer = QuittanceListSerializer(qs, many=True)
        return Response({'nombre': qs.count(), 'quittances': serializer.data})

    @action(detail=True, methods=['post'], url_path='generer_ecriture')
    def generer_ecriture(self, request, pk=None):
        """
        Le COMPTABLE génère l'écriture comptable en partie double depuis une quittance.
        Débit : compte de trésorerie (571 Caisse ou 521 Banque)
        Crédit : compte de produit (classe 7) fourni en paramètre
        """
        from apps.comptabilite.models import (
            EcritureComptable, LigneEcriture, CompteComptable, Journal
        )
        quittance = self.get_object()

        if not quittance.est_validee:
            return Response({'error': 'La quittance doit être validée.'}, status=400)
        if quittance.est_comptabilisee:
            return Response({'error': 'Cette quittance est déjà comptabilisée.'}, status=400)

        compte_produit_id = request.data.get('compte_produit_id')
        if not compte_produit_id:
            return Response({'error': 'compte_produit_id est requis.'}, status=400)

        try:
            compte_produit = CompteComptable.objects.get(pk=compte_produit_id, classe='7')
        except CompteComptable.DoesNotExist:
            return Response({'error': 'Compte de produit (classe 7) introuvable.'}, status=400)

        # Compte de trésorerie selon mode de paiement
        mapping_tresorerie = {
            'especes': '571',
            'cheque': '521',
            'carte': '521',
            'mobile_money': '521',
            'virement': '521',
            'assurance': '411',
        }
        num_tresorerie = mapping_tresorerie.get(quittance.mode_paiement, '571')
        try:
            compte_tresorerie = CompteComptable.objects.filter(
                numero_compte__startswith=num_tresorerie
            ).first()
            if not compte_tresorerie:
                raise CompteComptable.DoesNotExist
        except CompteComptable.DoesNotExist:
            return Response({'error': f'Compte de trésorerie {num_tresorerie} introuvable.'}, status=400)

        journal = quittance.journal
        if not journal:
            try:
                journal = Journal.objects.get(code='JV')
            except Journal.DoesNotExist:
                return Response({'error': 'Journal introuvable.'}, status=400)

        with transaction.atomic():
            ecriture = EcritureComptable.objects.create(
                date_ecriture=quittance.date_creation.date(),
                libelle=f"Encaissement quittance {quittance.numero} — {quittance.motif}",
                journal=journal,
                exercice=quittance.exercice,
                statut='validee',
                piece_justificative=quittance.numero,
                quittance_id=quittance.id,
                date_validation=timezone.now(),
            )
            # Débit trésorerie
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_tresorerie,
                libelle=f"Encaissement {quittance.numero}",
                montant_debit=quittance.montant,
                montant_credit=None,
            )
            # Crédit produit
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_produit,
                libelle=f"Recette {quittance.type_recette} — {quittance.numero}",
                montant_debit=None,
                montant_credit=quittance.montant,
            )
            quittance.est_comptabilisee = True
            quittance.save()

        return Response({
            'message': 'Écriture générée avec succès.',
            'numero_ecriture': ecriture.numero_ecriture,
            'quittance': quittance.numero,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='du_jour')
    def du_jour(self, request):
        today = timezone.now().date()
        qs = self.get_queryset().filter(date_creation__date=today)
        total = qs.aggregate(t=Sum('montant'))['t'] or 0
        return Response({
            'date': today,
            'nombre': qs.count(),
            'total': float(total),
            'quittances': QuittanceListSerializer(qs, many=True).data,
        })

    @action(detail=False, methods=['get'], url_path='de_la_semaine')
    def de_la_semaine(self, request):
        from datetime import timedelta
        debut = timezone.now().date() - timedelta(days=7)
        qs = self.get_queryset().filter(date_creation__date__gte=debut)
        total = qs.aggregate(t=Sum('montant'))['t'] or 0
        return Response({'nombre': qs.count(), 'total': float(total),
                         'quittances': QuittanceListSerializer(qs, many=True).data})

    @action(detail=False, methods=['get'], url_path='du_mois')
    def du_mois(self, request):
        now = timezone.now()
        qs = self.get_queryset().filter(
            date_creation__year=now.year, date_creation__month=now.month
        )
        total = qs.aggregate(t=Sum('montant'))['t'] or 0
        return Response({'mois': now.month, 'annee': now.year,
                         'nombre': qs.count(), 'total': float(total),
                         'quittances': QuittanceListSerializer(qs, many=True).data})

    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        qs = self.get_queryset()
        today = timezone.now().date()
        par_mode = {}
        for code, label in Quittance.MODE_PAIEMENT_CHOICES:
            sub = qs.filter(mode_paiement=code)
            par_mode[code] = {'label': label, 'nombre': sub.count(),
                               'total': float(sub.aggregate(t=Sum('montant'))['t'] or 0)}
        par_type = {}
        for code, label in Quittance.TYPE_RECETTE_CHOICES:
            sub = qs.filter(type_recette=code)
            par_type[code] = {'label': label, 'nombre': sub.count(),
                               'total': float(sub.aggregate(t=Sum('montant'))['t'] or 0)}
        return Response({
            'total_quittances': qs.count(),
            'total_montant': float(qs.aggregate(t=Sum('montant'))['t'] or 0),
            'a_comptabiliser': qs.filter(est_validee=True, est_comptabilisee=False).count(),
            'par_mode_paiement': par_mode,
            'par_type_recette': par_type,
        })

    @action(detail=False, methods=['get'], url_path='statistiques_avancees')
    def statistiques_avancees(self, request):
        from datetime import date
        annee = int(request.query_params.get('annee', timezone.now().year))
        mois_data = []
        for mois in range(1, 13):
            qs = self.get_queryset().filter(date_creation__year=annee, date_creation__month=mois)
            mois_data.append({
                'mois': mois, 'nombre': qs.count(),
                'total': float(qs.aggregate(t=Sum('montant'))['t'] or 0),
            })
        return Response({'annee': annee, 'evolution_mensuelle': mois_data})

    @action(detail=False, methods=['get'], url_path='journal_ventilation')
    def journal_ventilation(self, request):
        from apps.comptabilite.models import CompteComptable
        qs = self.get_queryset().filter(est_comptabilisee=True)
        return Response({
            'total_comptabilisees': qs.count(),
            'total_montant': float(qs.aggregate(t=Sum('montant'))['t'] or 0),
        })

    @action(detail=True, methods=['get'], url_path='export_pdf')
    def export_pdf(self, request, pk=None):
        q = self.get_object()
        return Response({
            'numero': q.numero, 'montant': float(q.montant),
            'motif': q.motif, 'type_recette': q.type_recette,
            'mode_paiement': q.mode_paiement, 'date': q.date_creation,
            'est_assure': q.est_assure,
            'montant_patient': float(q.montant_patient or q.montant),
            'montant_assurance': float(q.montant_assurance or 0),
        })

    @action(detail=False, methods=['get'], url_path='export_csv')
    def export_csv(self, request):
        qs = self.get_queryset()
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut:
            qs = qs.filter(date_creation__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_creation__date__lte=date_fin)
        data = QuittanceListSerializer(qs, many=True).data
        return Response({'nombre': qs.count(), 'quittances': data})


# ─────────────────────────────────────────────────────────────────────
#  CHÈQUES  (5 endpoints)
# ─────────────────────────────────────────────────────────────────────

class ChequeViewSet(viewsets.ModelViewSet):
    queryset = Cheque.objects.select_related('quittance')
    serializer_class = ChequeDetailSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['est_encaisse']
    search_fields = ['numero', 'banque', 'titulaire']

    @action(detail=True, methods=['post'], url_path='encaisser')
    def encaisser(self, request, pk=None):
        cheque = self.get_object()
        if cheque.est_encaisse:
            return Response({'error': 'Ce chèque est déjà encaissé.'}, status=400)
        cheque.est_encaisse = True
        cheque.date_encaissement = timezone.now().date()
        cheque.save()
        return Response({'message': 'Chèque encaissé.', 'cheque': ChequeDetailSerializer(cheque).data})

    @action(detail=False, methods=['get'], url_path='non-encaisses')
    def non_encaisses(self, request):
        qs = self.get_queryset().filter(est_encaisse=False)
        return Response({'nombre': qs.count(), 'cheques': ChequeDetailSerializer(qs, many=True).data})

    @action(detail=False, methods=['get'], url_path='encaisses')
    def encaisses(self, request):
        qs = self.get_queryset().filter(est_encaisse=True)
        return Response({'nombre': qs.count(), 'cheques': ChequeDetailSerializer(qs, many=True).data})


# ─────────────────────────────────────────────────────────────────────
#  CAISSE JOURNALIÈRE  (3 endpoints)
# ─────────────────────────────────────────────────────────────────────

class CaisseJournaliereViewSet(viewsets.ModelViewSet):
    queryset = CaisseJournaliere.objects.all()
    serializer_class = CaisseJournaliereSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['statut', 'date']
    ordering = ['-date']

    @action(detail=False, methods=['post'], url_path='ouvrir')
    def ouvrir(self, request):
        today = timezone.now().date()
        if CaisseJournaliere.objects.filter(date=today).exists():
            return Response({'error': 'Une caisse est déjà ouverte pour aujourd\'hui.'}, status=400)
        solde = request.data.get('solde_ouverture', 0)
        caisse = CaisseJournaliere.objects.create(
            date=today,
            solde_ouverture=solde,
            solde_theorique=solde,
            caissier_id=request.data.get('caissier_id'),
        )
        return Response(CaisseJournaliereSerializer(caisse).data, status=201)

    @action(detail=True, methods=['patch'], url_path='fermer')
    def fermer(self, request, pk=None):
        caisse = self.get_object()
        if caisse.statut == 'fermee':
            return Response({'error': 'Cette caisse est déjà fermée.'}, status=400)
        solde_physique = request.data.get('solde_physique')
        if solde_physique is None:
            return Response({'error': 'solde_physique est requis.'}, status=400)
        solde_theorique = caisse.calculer_solde_theorique()
        caisse.solde_theorique = solde_theorique
        caisse.solde_physique = Decimal(str(solde_physique))
        caisse.ecart = caisse.solde_physique - solde_theorique
        caisse.statut = 'fermee'
        caisse.date_fermeture = timezone.now()
        caisse.save()
        return Response(CaisseJournaliereSerializer(caisse).data)


# ─────────────────────────────────────────────────────────────────────
#  INVENTAIRE DE CAISSE  (3 endpoints)
# ─────────────────────────────────────────────────────────────────────

class InventaireCaisseViewSet(viewsets.ModelViewSet):
    queryset = InventaireCaisse.objects.all()
    serializer_class = InventaireCaisseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['statut', 'annee', 'mois']
    ordering = ['-annee', '-mois']

    @action(detail=True, methods=['patch'], url_path='clore')
    def clore(self, request, pk=None):
        inventaire = self.get_object()
        if inventaire.statut == 'clos':
            return Response({'error': 'Inventaire déjà clos.'}, status=400)
        inventaire.statut = 'clos'
        if 'ecart_justifie' in request.data:
            inventaire.ecart_justifie = request.data['ecart_justifie']
        if 'observations' in request.data:
            inventaire.observations = request.data['observations']
        inventaire.save()
        return Response(InventaireCaisseSerializer(inventaire).data)


# ─────────────────────────────────────────────────────────────────────
#  DÉPENSES MENUES  (2 endpoints)
# ─────────────────────────────────────────────────────────────────────

class DepenseMenueViewSet(viewsets.ModelViewSet):
    queryset = DepenseMenue.objects.select_related('caisse', 'categorie_sortie')
    serializer_class = DepenseMenueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['caisse', 'categorie_sortie']
    search_fields = ['motif']
    ordering = ['-date_creation']
