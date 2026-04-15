"""
ViewSets de l'app Comptabilité — Passo.
Tous les 34 endpoints du module comptabilité.
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Q, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.comptabilite.models import (
    CompteComptable, Journal, EcritureComptable, LigneEcriture,
    ExerciceComptable, BudgetPrevisionnel, PrestationDeService,
    AuditLog,
)
from apps.comptabilite.serializers import (
    CompteComptableSerializer, CompteComptableArborescenceSerializer,
    CompteComptableListSerializer,
    JournalSerializer, JournalListSerializer,
    EcritureComptableSerializer, EcritureComptableListSerializer,
    ExerciceComptableSerializer,
    BudgetPrevisionnelSerializer,
    PrestationDeServiceSerializer,
    AuditLogSerializer,
)


# =====================================================================
#                     COMPTES COMPTABLES (6 endpoints)
# =====================================================================

class CompteComptableViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les Comptes Comptables OHADA.

    Endpoints:
    - GET/POST  /api/comptes-comptables/
    - GET/PUT   /api/comptes-comptables/{id}/
    - GET       /api/comptes-comptables/par-classe/{n}/
    - GET       /api/comptes-comptables/produits/
    - GET       /api/comptes-comptables/arborescence/
    - GET       /api/comptes-comptables/statistiques/
    """
    queryset = CompteComptable.objects.all()
    serializer_class = CompteComptableSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['classe', 'type_compte', 'actif']
    search_fields = ['numero_compte', 'libelle', 'description']
    ordering_fields = ['numero_compte', 'classe', 'date_creation']
    ordering = ['numero_compte']

    @action(detail=False, methods=['get'], url_path='par-classe/(?P<classe>[1-7])')
    def par_classe(self, request, classe=None):
        """Retourne les comptes d'une classe donnée (1 à 7)."""
        comptes = self.get_queryset().filter(classe=classe, actif=True)
        serializer = CompteComptableListSerializer(comptes, many=True)
        return Response({
            'classe': classe,
            'nombre': comptes.count(),
            'comptes': serializer.data,
        })

    @action(detail=False, methods=['get'], url_path='produits')
    def produits(self, request):
        """Retourne uniquement les comptes de produit (classe 7)."""
        comptes = self.get_queryset().filter(classe='7', actif=True)
        serializer = CompteComptableListSerializer(comptes, many=True)
        return Response({
            'nombre': comptes.count(),
            'comptes': serializer.data,
        })

    @action(detail=False, methods=['get'], url_path='arborescence')
    def arborescence(self, request):
        """Plan comptable en arborescence."""
        racines = self.get_queryset().filter(
            compte_parent__isnull=True, actif=True
        ).order_by('numero_compte')
        serializer = CompteComptableArborescenceSerializer(racines, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """Statistiques du plan comptable."""
        stats_classe = {}
        for code, label in CompteComptable.CLASSE_CHOICES:
            count = self.get_queryset().filter(classe=code).count()
            actifs = self.get_queryset().filter(classe=code, actif=True).count()
            stats_classe[code] = {
                'label': label, 'total': count,
                'actifs': actifs, 'inactifs': count - actifs,
            }
        stats_type = {}
        for code, label in CompteComptable.TYPE_COMPTE_CHOICES:
            stats_type[code] = {
                'label': label,
                'total': self.get_queryset().filter(type_compte=code).count(),
            }
        return Response({
            'total_comptes': self.get_queryset().count(),
            'total_actifs': self.get_queryset().filter(actif=True).count(),
            'par_classe': stats_classe,
            'par_type': stats_type,
        })


# =====================================================================
#                     JOURNAUX (4 endpoints)
# =====================================================================

class JournalViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les Journaux Comptables.

    Endpoints:
    - GET/POST  /api/journaux/
    - GET       /api/journaux/{code}/
    - GET       /api/journaux/{code}/ecritures/
    - GET       /api/journaux/statistiques/
    """
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    lookup_field = 'code'
    filter_backends = [SearchFilter]
    search_fields = ['code', 'libelle']

    @action(detail=True, methods=['get'], url_path='ecritures')
    def ecritures(self, request, code=None):
        """Écritures d'un journal avec filtres par période."""
        journal = self.get_object()
        ecritures = journal.ecritures.all()

        # Filtres optionnels par date
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut:
            ecritures = ecritures.filter(date_ecriture__gte=date_debut)
        if date_fin:
            ecritures = ecritures.filter(date_ecriture__lte=date_fin)

        serializer = EcritureComptableListSerializer(ecritures, many=True)
        return Response({
            'journal': journal.code,
            'nombre': ecritures.count(),
            'ecritures': serializer.data,
        })

    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """Statistiques par journal."""
        stats = []
        for journal in Journal.objects.all():
            ecritures = journal.ecritures.filter(statut='validee')
            stats.append({
                'code': journal.code,
                'libelle': journal.libelle,
                'total_ecritures': journal.ecritures.count(),
                'ecritures_validees': ecritures.count(),
            })
        return Response(stats)


# =====================================================================
#                  ÉCRITURES COMPTABLES (7 endpoints)
# =====================================================================

class EcritureComptableViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les Écritures Comptables.

    Endpoints:
    - POST      /api/ecritures/                    — Créer avec lignes
    - GET       /api/ecritures/                    — Liste filtrée
    - GET       /api/ecritures/{id}/               — Détail avec lignes
    - PATCH     /api/ecritures/{id}/valider/       — Valider
    - GET       /api/ecritures/grand-livre/{id}/   — Grand Livre d'un compte
    - GET       /api/ecritures/balance/            — Balance Générale
    - GET       /api/ecritures/statistiques/       — Stats
    """
    queryset = EcritureComptable.objects.prefetch_related('lignes', 'lignes__compte', 'journal')
    serializer_class = EcritureComptableSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'journal', 'exercice']
    search_fields = ['numero_ecriture', 'libelle', 'piece_justificative']
    ordering_fields = ['date_ecriture', 'numero_ecriture']
    ordering = ['-date_ecriture']

    def get_serializer_class(self):
        if self.action == 'list':
            return EcritureComptableListSerializer
        return EcritureComptableSerializer

    @action(detail=True, methods=['patch'], url_path='valider')
    def valider(self, request, pk=None):
        """Valider une écriture brouillon."""
        ecriture = self.get_object()
        if ecriture.statut != 'brouillon':
            return Response(
                {'error': f"Impossible de valider : statut actuel = '{ecriture.statut}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not ecriture.est_equilibree:
            return Response(
                {'error': f"L'écriture n'est pas équilibrée : "
                          f"débit={ecriture.total_debit}, crédit={ecriture.total_credit}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        ecriture.statut = 'validee'
        ecriture.date_validation = timezone.now()
        ecriture.save()
        return Response(EcritureComptableSerializer(ecriture).data)

    @action(detail=False, methods=['get'], url_path='grand-livre/(?P<compte_id>[0-9]+)')
    def grand_livre(self, request, compte_id=None):
        """Grand Livre d'un compte : mouvements chronologiques + solde cumulé."""
        try:
            compte = CompteComptable.objects.get(pk=compte_id)
        except CompteComptable.DoesNotExist:
            return Response(
                {'error': 'Compte non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        lignes = LigneEcriture.objects.filter(
            compte=compte,
            ecriture__statut='validee'
        ).select_related('ecriture', 'ecriture__journal').order_by('ecriture__date_ecriture', 'id')

        # Filtres optionnels
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut:
            lignes = lignes.filter(ecriture__date_ecriture__gte=date_debut)
        if date_fin:
            lignes = lignes.filter(ecriture__date_ecriture__lte=date_fin)

        mouvements = []
        solde_cumule = Decimal('0.00')
        for ligne in lignes:
            debit = ligne.montant_debit or Decimal('0.00')
            credit = ligne.montant_credit or Decimal('0.00')
            solde_cumule += debit - credit
            mouvements.append({
                'date': ligne.ecriture.date_ecriture,
                'numero_ecriture': ligne.ecriture.numero_ecriture,
                'journal': ligne.ecriture.journal.code,
                'libelle': ligne.libelle or ligne.ecriture.libelle,
                'debit': float(debit),
                'credit': float(credit),
                'solde_cumule': float(solde_cumule),
            })

        return Response({
            'compte': {
                'id': compte.id,
                'numero': compte.numero_compte,
                'libelle': compte.libelle,
            },
            'nombre_mouvements': len(mouvements),
            'total_debit': float(sum(m['debit'] for m in mouvements)),
            'total_credit': float(sum(m['credit'] for m in mouvements)),
            'solde_final': float(solde_cumule),
            'mouvements': mouvements,
        })

    @action(detail=False, methods=['get'], url_path='balance')
    def balance(self, request):
        """Balance Générale : tous les comptes avec débits, crédits, soldes."""
        comptes = CompteComptable.objects.filter(actif=True).order_by('numero_compte')

        # Filtres optionnels
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        classe = request.query_params.get('classe')
        if classe:
            comptes = comptes.filter(classe=classe)

        lignes_filter = Q(lignes_ecriture__ecriture__statut='validee')
        if date_debut:
            lignes_filter &= Q(lignes_ecriture__ecriture__date_ecriture__gte=date_debut)
        if date_fin:
            lignes_filter &= Q(lignes_ecriture__ecriture__date_ecriture__lte=date_fin)

        balance = []
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')

        for compte in comptes:
            agg = LigneEcriture.objects.filter(
                compte=compte,
                ecriture__statut='validee'
            )
            if date_debut:
                agg = agg.filter(ecriture__date_ecriture__gte=date_debut)
            if date_fin:
                agg = agg.filter(ecriture__date_ecriture__lte=date_fin)

            totaux = agg.aggregate(
                debit=Sum('montant_debit'),
                credit=Sum('montant_credit')
            )
            debit = totaux['debit'] or Decimal('0.00')
            credit = totaux['credit'] or Decimal('0.00')

            if debit == 0 and credit == 0:
                continue  # Pas de mouvements

            solde = debit - credit
            total_debits += debit
            total_credits += credit

            balance.append({
                'numero_compte': compte.numero_compte,
                'libelle': compte.libelle,
                'classe': compte.classe,
                'total_debit': float(debit),
                'total_credit': float(credit),
                'solde_debiteur': float(solde) if solde > 0 else 0,
                'solde_crediteur': float(abs(solde)) if solde < 0 else 0,
            })

        return Response({
            'nombre_comptes': len(balance),
            'total_debits': float(total_debits),
            'total_credits': float(total_credits),
            'equilibre': abs(total_debits - total_credits) < Decimal('0.01'),
            'balance': balance,
        })

    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """Statistiques des écritures."""
        qs = self.get_queryset()
        return Response({
            'total': qs.count(),
            'brouillons': qs.filter(statut='brouillon').count(),
            'validees': qs.filter(statut='validee').count(),
            'annulees': qs.filter(statut='annulee').count(),
        })


# =====================================================================
#                  EXERCICE COMPTABLE (4 endpoints)
# =====================================================================

class ExerciceComptableViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les Exercices Comptables.

    Endpoints:
    - GET/POST  /api/exercices/
    - GET       /api/exercices/{id}/
    - POST      /api/exercices/{id}/cloturer/
    - POST      /api/exercices/{id}/report-nouveau/
    """
    queryset = ExerciceComptable.objects.all()
    serializer_class = ExerciceComptableSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['statut', 'annee']
    ordering = ['-annee']

    @action(detail=True, methods=['post'], url_path='cloturer')
    def cloturer(self, request, pk=None):
        """Clôturer l'exercice : calcul du résultat net."""
        exercice = self.get_object()
        if exercice.statut == 'cloture':
            return Response(
                {'error': "Cet exercice est déjà clôturé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcul du résultat : total produits (classe 7) - total charges (classe 6)
        ecritures_validees = LigneEcriture.objects.filter(
            ecriture__exercice=exercice,
            ecriture__statut='validee'
        )
        total_produits = ecritures_validees.filter(
            compte__classe='7'
        ).aggregate(
            debit=Sum('montant_debit'),
            credit=Sum('montant_credit')
        )
        total_charges = ecritures_validees.filter(
            compte__classe='6'
        ).aggregate(
            debit=Sum('montant_debit'),
            credit=Sum('montant_credit')
        )

        produits = (total_produits['credit'] or 0) - (total_produits['debit'] or 0)
        charges = (total_charges['debit'] or 0) - (total_charges['credit'] or 0)
        resultat_net = produits - charges

        exercice.statut = 'cloture'
        exercice.resultat_net = resultat_net
        exercice.date_cloture = timezone.now()
        exercice.save()

        return Response({
            'message': f"Exercice {exercice.annee} clôturé avec succès.",
            'total_produits': float(produits),
            'total_charges': float(charges),
            'resultat_net': float(resultat_net),
            'type_resultat': 'Bénéfice' if resultat_net >= 0 else 'Perte',
            'exercice': ExerciceComptableSerializer(exercice).data,
        })

    @action(detail=True, methods=['post'], url_path='report-nouveau')
    def report_nouveau(self, request, pk=None):
        """Générer les écritures de report à nouveau pour N+1."""
        exercice = self.get_object()
        if exercice.statut != 'cloture':
            return Response(
                {'error': "L'exercice doit être clôturé avant de générer le report."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier que l'exercice N+1 existe
        try:
            exercice_suivant = ExerciceComptable.objects.get(annee=exercice.annee + 1)
        except ExerciceComptable.DoesNotExist:
            return Response(
                {'error': f"L'exercice {exercice.annee + 1} n'existe pas. Créez-le d'abord."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier le journal JRN
        try:
            journal_jrn = Journal.objects.get(code='JRN')
        except Journal.DoesNotExist:
            return Response(
                {'error': "Le journal JRN (Report à Nouveau) n'existe pas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculer les soldes bilan (classes 1 à 5)
        comptes_bilan = CompteComptable.objects.filter(
            classe__in=['1', '2', '3', '4', '5'], actif=True
        )
        lignes_report = []
        for compte in comptes_bilan:
            agg = LigneEcriture.objects.filter(
                compte=compte,
                ecriture__exercice=exercice,
                ecriture__statut='validee'
            ).aggregate(debit=Sum('montant_debit'), credit=Sum('montant_credit'))
            solde = (agg['debit'] or 0) - (agg['credit'] or 0)
            if solde != 0:
                lignes_report.append({
                    'compte': compte,
                    'solde': solde,
                })

        if not lignes_report:
            return Response({'message': "Aucun solde à reporter.", 'ecritures_creees': 0})

        # Créer l'écriture de report
        ecriture = EcritureComptable.objects.create(
            date_ecriture=exercice_suivant.date_debut,
            libelle=f"Report à nouveau — Exercice {exercice.annee}",
            journal=journal_jrn,
            exercice=exercice_suivant,
            statut='validee',
            date_validation=timezone.now(),
        )
        for item in lignes_report:
            if item['solde'] > 0:
                LigneEcriture.objects.create(
                    ecriture=ecriture, compte=item['compte'],
                    libelle=f"Report {item['compte'].numero_compte}",
                    montant_debit=item['solde'], montant_credit=None
                )
            else:
                LigneEcriture.objects.create(
                    ecriture=ecriture, compte=item['compte'],
                    libelle=f"Report {item['compte'].numero_compte}",
                    montant_debit=None, montant_credit=abs(item['solde'])
                )

        return Response({
            'message': f"Report à nouveau généré pour l'exercice {exercice_suivant.annee}.",
            'numero_ecriture': ecriture.numero_ecriture,
            'comptes_reportes': len(lignes_report),
        })


# =====================================================================
#                  BUDGET PRÉVISIONNEL (3 endpoints)
# =====================================================================

class BudgetPrevisionnelViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les Budgets Prévisionnels.

    Endpoints:
    - GET/POST  /api/budgets/
    - GET       /api/budgets/par-service/{id}/
    - GET       /api/budgets/evaluation/
    """
    queryset = BudgetPrevisionnel.objects.select_related('exercice', 'categorie')
    serializer_class = BudgetPrevisionnelSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['exercice', 'priorite', 'service_hospitalier']
    search_fields = ['libelle', 'service_hospitalier']
    ordering = ['-exercice__annee', 'categorie']

    @action(detail=False, methods=['get'], url_path='par-service/(?P<service_id>[0-9]+)')
    def par_service(self, request, service_id=None):
        """Budget d'un service hospitalier."""
        budgets = self.get_queryset().filter(service_hospitalier_id=service_id)
        serializer = self.get_serializer(budgets, many=True)
        total_prevu = budgets.aggregate(t=Sum('montant_prevu'))['t'] or 0
        total_consomme = budgets.aggregate(t=Sum('montant_consomme'))['t'] or 0
        return Response({
            'service_id': int(service_id),
            'nombre_budgets': budgets.count(),
            'total_prevu': float(total_prevu),
            'total_consomme': float(total_consomme),
            'total_disponible': float(total_prevu - total_consomme),
            'budgets': serializer.data,
        })

    @action(detail=False, methods=['get'], url_path='evaluation')
    def evaluation(self, request):
        """Évaluation budgétaire globale."""
        qs = self.get_queryset()
        exercice_id = request.query_params.get('exercice')
        if exercice_id:
            qs = qs.filter(exercice_id=exercice_id)

        total_prevu = qs.aggregate(t=Sum('montant_prevu'))['t'] or 0
        total_consomme = qs.aggregate(t=Sum('montant_consomme'))['t'] or 0
        taux = round((total_consomme / total_prevu * 100), 2) if total_prevu > 0 else 0

        # Par priorité
        par_priorite = {}
        for code, label in BudgetPrevisionnel.PRIORITE_CHOICES:
            sub = qs.filter(priorite=code)
            prevu = sub.aggregate(t=Sum('montant_prevu'))['t'] or 0
            consomme = sub.aggregate(t=Sum('montant_consomme'))['t'] or 0
            par_priorite[code] = {
                'nombre': sub.count(),
                'prevu': float(prevu),
                'consomme': float(consomme),
                'disponible': float(prevu - consomme),
            }

        return Response({
            'total_prevu': float(total_prevu),
            'total_consomme': float(total_consomme),
            'total_disponible': float(total_prevu - total_consomme),
            'taux_consommation': taux,
            'par_priorite': par_priorite,
        })


# =====================================================================
#                  PRESTATIONS DE SERVICE (2 endpoints)
# =====================================================================

class PrestationDeServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les Prestations de Service.

    Endpoints:
    - GET/POST  /api/prestations-de-service/
    - GET       /api/prestations-de-service/by-service/{id}/
    """
    queryset = PrestationDeService.objects.select_related('compte_comptable')
    serializer_class = PrestationDeServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type_prestation', 'actif']
    search_fields = ['code', 'libelle']
    ordering = ['type_prestation', 'code']

    @action(detail=False, methods=['get'], url_path='by-service/(?P<service_id>[0-9]+)')
    def by_service(self, request, service_id=None):
        """Prestations d'un service hospitalier."""
        prestations = self.get_queryset().filter(
            service_hospitalier_id=service_id, actif=True
        )
        serializer = self.get_serializer(prestations, many=True)
        return Response({
            'service_id': int(service_id),
            'nombre': prestations.count(),
            'prestations': serializer.data,
        })


# =====================================================================
#                  ÉTATS FINANCIERS SYSCOHADA (4 endpoints)
# =====================================================================

class EtatsFinanciersViewSet(viewsets.ViewSet):
    """
    ViewSet pour les États Financiers SYSCOHADA.
    Endpoints en lecture seule — générés depuis les écritures validées.

    Endpoints:
    - GET  /api/etats-financiers/bilan/
    - GET  /api/etats-financiers/compte-resultat/
    - GET  /api/etats-financiers/flux-tresorerie/
    - GET  /api/etats-financiers/resultat-par-service/
    """

    def _get_date_filters(self, request):
        """Extraire les filtres de date communs."""
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        exercice_id = request.query_params.get('exercice')
        filters = Q(ecriture__statut='validee')
        if date_debut:
            filters &= Q(ecriture__date_ecriture__gte=date_debut)
        if date_fin:
            filters &= Q(ecriture__date_ecriture__lte=date_fin)
        if exercice_id:
            filters &= Q(ecriture__exercice_id=exercice_id)
        return filters

    def _solde_classe(self, filters, classe):
        """Calculer le solde d'une classe de comptes."""
        agg = LigneEcriture.objects.filter(
            filters, compte__classe=classe
        ).aggregate(debit=Sum('montant_debit'), credit=Sum('montant_credit'))
        return {
            'debit': agg['debit'] or Decimal('0'),
            'credit': agg['credit'] or Decimal('0'),
        }

    def _soldes_par_compte(self, filters, classes):
        """Calculer les soldes par compte pour des classes données."""
        comptes = CompteComptable.objects.filter(
            classe__in=classes, actif=True
        ).order_by('numero_compte')
        resultats = []
        for compte in comptes:
            agg = LigneEcriture.objects.filter(
                filters, compte=compte
            ).aggregate(debit=Sum('montant_debit'), credit=Sum('montant_credit'))
            debit = agg['debit'] or Decimal('0')
            credit = agg['credit'] or Decimal('0')
            if debit == 0 and credit == 0:
                continue
            solde = debit - credit
            resultats.append({
                'numero_compte': compte.numero_compte,
                'libelle': compte.libelle,
                'debit': float(debit),
                'credit': float(credit),
                'solde': float(solde),
            })
        return resultats

    @action(detail=False, methods=['get'], url_path='bilan')
    def bilan(self, request):
        """
        Bilan SYSCOHADA.
        Actif : classes 2 (Immobilisations), 3 (Stocks), 4 débiteurs, 5 (Trésorerie active)
        Passif : classe 1 (Capitaux), 4 créditeurs, 5 (Trésorerie passive)
        """
        filters = self._get_date_filters(request)

        # ACTIF
        actif_immobilisations = self._soldes_par_compte(filters, ['2'])
        actif_stocks = self._soldes_par_compte(filters, ['3'])
        actif_tresorerie = self._soldes_par_compte(filters, ['5'])
        actif_clients = self._soldes_par_compte(filters, ['4'])
        # Filtrer classe 4 : comptes débiteurs = actif, créditeurs = passif
        actif_tiers = [c for c in actif_clients if c['solde'] > 0]
        passif_tiers = [c for c in actif_clients if c['solde'] < 0]
        actif_tresorerie_active = [c for c in actif_tresorerie if c['solde'] > 0]
        passif_tresorerie = [c for c in actif_tresorerie if c['solde'] < 0]

        total_actif = sum(c['solde'] for c in actif_immobilisations) + \
                      sum(c['solde'] for c in actif_stocks) + \
                      sum(c['solde'] for c in actif_tiers) + \
                      sum(c['solde'] for c in actif_tresorerie_active)

        # PASSIF
        passif_capitaux = self._soldes_par_compte(filters, ['1'])
        total_passif = sum(abs(c['solde']) for c in passif_capitaux) + \
                       sum(abs(c['solde']) for c in passif_tiers) + \
                       sum(abs(c['solde']) for c in passif_tresorerie)

        return Response({
            'titre': 'Bilan — SYSCOHADA',
            'actif': {
                'immobilisations': actif_immobilisations,
                'stocks': actif_stocks,
                'creances_tiers': actif_tiers,
                'tresorerie_active': actif_tresorerie_active,
                'total_actif': float(total_actif),
            },
            'passif': {
                'capitaux_propres': passif_capitaux,
                'dettes_tiers': passif_tiers,
                'tresorerie_passive': passif_tresorerie,
                'total_passif': float(total_passif),
            },
            'equilibre': abs(total_actif - total_passif) < 0.01,
        })

    @action(detail=False, methods=['get'], url_path='compte-resultat')
    def compte_resultat(self, request):
        """
        Compte de Résultat SYSCOHADA.
        Charges (classe 6) vs Produits (classe 7).
        """
        filters = self._get_date_filters(request)

        charges_detail = self._soldes_par_compte(filters, ['6'])
        produits_detail = self._soldes_par_compte(filters, ['7'])

        # Charges = débit - crédit (solde débiteur)
        total_charges = sum(c['solde'] for c in charges_detail)
        # Produits = crédit - débit (solde créditeur, donc on inverse)
        total_produits = sum(abs(c['solde']) for c in produits_detail)

        resultat_net = total_produits - total_charges

        return Response({
            'titre': 'Compte de Résultat — SYSCOHADA',
            'charges': {
                'detail': charges_detail,
                'total': float(total_charges),
            },
            'produits': {
                'detail': produits_detail,
                'total': float(total_produits),
            },
            'resultat_net': float(resultat_net),
            'type_resultat': 'Bénéfice' if resultat_net >= 0 else 'Perte',
        })

    @action(detail=False, methods=['get'], url_path='flux-tresorerie')
    def flux_tresorerie(self, request):
        """
        Tableau des Flux de Trésorerie (TFT) SYSCOHADA.
        3 catégories : opérationnels, investissement, financement.
        """
        filters = self._get_date_filters(request)

        # Flux opérationnels : recettes (classe 7) - charges (classe 6) via trésorerie
        tresorerie = self._solde_classe(filters, '5')
        flux_tresorerie_net = tresorerie['debit'] - tresorerie['credit']

        # Flux d'investissement : mouvements classe 2 (immobilisations)
        investissement = self._solde_classe(filters, '2')
        flux_investissement = -(investissement['debit'] - investissement['credit'])

        # Flux de financement : mouvements classe 1 (capitaux)
        financement = self._solde_classe(filters, '1')
        flux_financement = financement['credit'] - financement['debit']

        # Flux opérationnels = total - investissement - financement
        produits = self._solde_classe(filters, '7')
        charges = self._solde_classe(filters, '6')
        flux_operationnel = (produits['credit'] - produits['debit']) - \
                           (charges['debit'] - charges['credit'])

        return Response({
            'titre': 'Tableau des Flux de Trésorerie — SYSCOHADA',
            'flux_operationnels': float(flux_operationnel),
            'flux_investissement': float(flux_investissement),
            'flux_financement': float(flux_financement),
            'variation_tresorerie': float(flux_tresorerie_net),
        })

    @action(detail=False, methods=['get'], url_path='resultat-par-service')
    def resultat_par_service(self, request):
        """Résultat par service hospitalier (comptabilité analytique simplifiée)."""
        filters = self._get_date_filters(request)

        # Regrouper les prestations par service
        services = PrestationDeService.objects.values(
            'service_hospitalier', 'service_hospitalier_id'
        ).distinct().exclude(service_hospitalier__isnull=True)

        resultats = []
        for service in services:
            # Produits : écritures liées aux comptes de ce service
            comptes_service = PrestationDeService.objects.filter(
                service_hospitalier=service['service_hospitalier']
            ).values_list('compte_comptable_id', flat=True)

            agg = LigneEcriture.objects.filter(
                filters,
                compte_id__in=comptes_service
            ).aggregate(debit=Sum('montant_debit'), credit=Sum('montant_credit'))

            recettes = (agg['credit'] or 0) - (agg['debit'] or 0)
            resultats.append({
                'service': service['service_hospitalier'],
                'service_id': service['service_hospitalier_id'],
                'recettes': float(recettes),
            })

        resultats.sort(key=lambda x: x['recettes'], reverse=True)
        return Response({
            'titre': 'Résultat par Service Hospitalier',
            'nombre_services': len(resultats),
            'services': resultats,
        })


# =====================================================================
#                  AUDIT LOG — PISTE D'AUDIT (2 endpoints)
# =====================================================================

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour la Piste d'Audit (lecture seule).

    Endpoints:
    - GET  /api/audit-log/
    - GET  /api/audit-log/par-utilisateur/{id}/
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'module', 'utilisateur_id']
    search_fields = ['description', 'objet_reference', 'utilisateur_nom']
    ordering = ['-date_action']

    @action(detail=False, methods=['get'], url_path='par-utilisateur/(?P<user_id>[0-9]+)')
    def par_utilisateur(self, request, user_id=None):
        """Activité d'un utilisateur spécifique."""
        logs = self.get_queryset().filter(utilisateur_id=user_id)

        # Stats par action
        par_action = {}
        for code, label in AuditLog.ACTION_CHOICES:
            count = logs.filter(action=code).count()
            if count > 0:
                par_action[code] = {'label': label, 'count': count}

        serializer = self.get_serializer(logs[:50], many=True)
        return Response({
            'utilisateur_id': int(user_id),
            'total_actions': logs.count(),
            'par_action': par_action,
            'dernieres_actions': serializer.data,
        })


# =====================================================================
#                  TABLEAU DE BORD FINANCIER (2 endpoints)
# =====================================================================

class TableauDeBordViewSet(viewsets.ViewSet):
    """
    ViewSet pour le Tableau de Bord Financier.

    Endpoints:
    - GET  /api/tableau-de-bord/
    - GET  /api/tableau-de-bord/evolution-mensuelle/
    """

    @action(detail=False, methods=['get'], url_path='')
    def dashboard(self, request):
        """KPIs financiers globaux."""
        # Écritures validées
        ecritures_validees = LigneEcriture.objects.filter(ecriture__statut='validee')

        # Total recettes (classe 7)
        produits = ecritures_validees.filter(compte__classe='7').aggregate(
            debit=Sum('montant_debit'), credit=Sum('montant_credit')
        )
        total_recettes = (produits['credit'] or 0) - (produits['debit'] or 0)

        # Total dépenses (classe 6)
        charges = ecritures_validees.filter(compte__classe='6').aggregate(
            debit=Sum('montant_debit'), credit=Sum('montant_credit')
        )
        total_depenses = (charges['debit'] or 0) - (charges['credit'] or 0)

        # Trésorerie (classe 5)
        tresorerie = ecritures_validees.filter(compte__classe='5').aggregate(
            debit=Sum('montant_debit'), credit=Sum('montant_credit')
        )
        solde_tresorerie = (tresorerie['debit'] or 0) - (tresorerie['credit'] or 0)

        # Créances clients (classe 4 débiteurs)
        clients = ecritures_validees.filter(
            compte__classe='4', compte__numero_compte__startswith='41'
        ).aggregate(debit=Sum('montant_debit'), credit=Sum('montant_credit'))
        creances = (clients['debit'] or 0) - (clients['credit'] or 0)

        # Dettes fournisseurs (classe 4 créditeurs)
        fournisseurs = ecritures_validees.filter(
            compte__classe='4', compte__numero_compte__startswith='40'
        ).aggregate(debit=Sum('montant_debit'), credit=Sum('montant_credit'))
        dettes = (fournisseurs['credit'] or 0) - (fournisseurs['debit'] or 0)

        # Ratios
        resultat_net = float(total_recettes) - float(total_depenses)
        marge = round((resultat_net / float(total_recettes) * 100), 2) if total_recettes else 0

        # Counts
        nb_ecritures = EcritureComptable.objects.count()
        nb_ecritures_validees = EcritureComptable.objects.filter(statut='validee').count()
        nb_brouillons = EcritureComptable.objects.filter(statut='brouillon').count()

        # Budget
        budgets = BudgetPrevisionnel.objects.aggregate(
            prevu=Sum('montant_prevu'), consomme=Sum('montant_consomme')
        )
        budget_prevu = budgets['prevu'] or 0
        budget_consomme = budgets['consomme'] or 0

        return Response({
            'titre': 'Tableau de Bord Financier',
            'kpis': {
                'total_recettes': float(total_recettes),
                'total_depenses': float(total_depenses),
                'resultat_net': resultat_net,
                'marge_nette_pct': marge,
                'solde_tresorerie': float(solde_tresorerie),
                'creances_clients': float(creances),
                'dettes_fournisseurs': float(dettes),
            },
            'ecritures': {
                'total': nb_ecritures,
                'validees': nb_ecritures_validees,
                'brouillons': nb_brouillons,
            },
            'budget': {
                'prevu': float(budget_prevu),
                'consomme': float(budget_consomme),
                'disponible': float(budget_prevu - budget_consomme),
                'taux_consommation': round(float(budget_consomme / budget_prevu * 100), 2) if budget_prevu else 0,
            },
        })

    @action(detail=False, methods=['get'], url_path='evolution-mensuelle')
    def evolution_mensuelle(self, request):
        """Évolution mensuelle des recettes et dépenses."""
        annee = request.query_params.get('annee', timezone.now().year)

        mois_data = []
        for mois in range(1, 13):
            lignes = LigneEcriture.objects.filter(
                ecriture__statut='validee',
                ecriture__date_ecriture__year=annee,
                ecriture__date_ecriture__month=mois
            )
            produits = lignes.filter(compte__classe='7').aggregate(
                debit=Sum('montant_debit'), credit=Sum('montant_credit')
            )
            charges_agg = lignes.filter(compte__classe='6').aggregate(
                debit=Sum('montant_debit'), credit=Sum('montant_credit')
            )
            recettes = float((produits['credit'] or 0) - (produits['debit'] or 0))
            depenses = float((charges_agg['debit'] or 0) - (charges_agg['credit'] or 0))

            mois_data.append({
                'mois': mois,
                'recettes': recettes,
                'depenses': depenses,
                'resultat': recettes - depenses,
            })

        total_recettes = sum(m['recettes'] for m in mois_data)
        total_depenses = sum(m['depenses'] for m in mois_data)

        return Response({
            'annee': int(annee),
            'total_recettes': total_recettes,
            'total_depenses': total_depenses,
            'resultat_annuel': total_recettes - total_depenses,
            'mois': mois_data,
        })
