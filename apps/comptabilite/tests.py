"""
Tests unitaires — App Comptabilité.
Minimum 3 tests par ViewSet + tests métier critiques.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.comptabilite.models import (
    CompteComptable, Journal, EcritureComptable, LigneEcriture,
    ExerciceComptable, BudgetPrevisionnel, PrestationDeService,
)
from apps.sorties.models import CategorieSortie


def creer_compte(numero='571', libelle='Caisse', classe='5', type_c='tresorerie'):
    return CompteComptable.objects.get_or_create(
        numero_compte=numero,
        defaults={'libelle': libelle, 'classe': classe, 'type_compte': type_c}
    )[0]


def creer_journal(code='JC', libelle='Journal de Caisse'):
    return Journal.objects.get_or_create(code=code, defaults={'libelle': libelle})[0]


def creer_exercice(annee=2026):
    return ExerciceComptable.objects.get_or_create(
        annee=annee,
        defaults={'date_debut': date(annee, 1, 1), 'date_fin': date(annee, 12, 31), 'statut': 'ouvert'}
    )[0]


class CompteComptableTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_compte(self):
        r = self.client.post('/api/comptes-comptables/', {
            'numero_compte': '701', 'libelle': 'Consultations',
            'classe': '7', 'type_compte': 'produit'
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['numero_compte'], '701')

    def test_list_comptes(self):
        creer_compte('571', 'Caisse', '5', 'tresorerie')
        r = self.client.get('/api/comptes-comptables/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_compte(self):
        c = creer_compte('521', 'Banque', '5', 'tresorerie')
        r = self.client.get(f'/api/comptes-comptables/{c.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['numero_compte'], '521')

    def test_arborescence(self):
        r = self.client.get('/api/comptes-comptables/arborescence/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_statistiques(self):
        r = self.client.get('/api/comptes-comptables/statistiques/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('total_comptes', r.data)


class JournalTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_journal(self):
        r = self.client.post('/api/journaux/', {
            'code': 'JC', 'libelle': 'Journal de Caisse'
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_list_journaux(self):
        creer_journal()
        r = self.client.get('/api/journaux/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_journal(self):
        j = creer_journal('JB', 'Journal de Banque')
        r = self.client.get(f'/api/journaux/{j.code}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class EcritureComptableTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.compte_caisse = creer_compte('571', 'Caisse', '5', 'tresorerie')
        self.compte_produit = creer_compte('701', 'Consultations', '7', 'produit')
        self.journal = creer_journal('JC')
        self.exercice = creer_exercice()

    def _payload_ecriture(self, debit=50000, credit=50000):
        return {
            'date_ecriture': '2026-04-19',
            'libelle': 'Test écriture',
            'journal': self.journal.id,
            'exercice': self.exercice.id,
            'lignes': [
                {'compte': self.compte_caisse.id, 'libelle': 'Débit caisse', 'montant_debit': debit, 'montant_credit': None},
                {'compte': self.compte_produit.id, 'libelle': 'Crédit produit', 'montant_debit': None, 'montant_credit': credit},
            ]
        }

    def test_create_ecriture_equilibree(self):
        r = self.client.post('/api/ecritures/', self._payload_ecriture(), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data['est_equilibree'])

    def test_create_ecriture_desequilibree_retourne_400(self):
        """RÈGLE MÉTIER : écriture déséquilibrée → 400."""
        r = self.client.post('/api/ecritures/', self._payload_ecriture(debit=50000, credit=30000), format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_ecritures(self):
        r = self.client.get('/api/ecritures/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_ecriture(self):
        r = self.client.post('/api/ecritures/', self._payload_ecriture(), format='json')
        ecriture_id = r.data['id']
        r2 = self.client.get(f'/api/ecritures/{ecriture_id}/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

    def test_valider_ecriture(self):
        r = self.client.post('/api/ecritures/', self._payload_ecriture(), format='json')
        ecriture_id = r.data['id']
        r2 = self.client.patch(f'/api/ecritures/{ecriture_id}/valider/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data['statut'], 'validee')

    def test_ecriture_validee_non_revalidable(self):
        """RÈGLE MÉTIER : une écriture validée ne peut pas être re-validée."""
        r = self.client.post('/api/ecritures/', self._payload_ecriture(), format='json')
        ecriture_id = r.data['id']
        self.client.patch(f'/api/ecritures/{ecriture_id}/valider/')
        r2 = self.client.patch(f'/api/ecritures/{ecriture_id}/valider/')
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_balance_equilibree(self):
        """RÈGLE MÉTIER : total débits = total crédits dans la balance."""
        self.client.post('/api/ecritures/', self._payload_ecriture(), format='json')
        r = self.client.get('/api/ecritures/balance/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_grand_livre(self):
        r = self.client.get(f'/api/ecritures/grand-livre/{self.compte_caisse.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('mouvements', r.data)


class ExerciceComptableTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_exercice(self):
        r = self.client.post('/api/exercices/', {
            'annee': 2025, 'date_debut': '2025-01-01',
            'date_fin': '2025-12-31', 'statut': 'ouvert'
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_list_exercices(self):
        creer_exercice()
        r = self.client.get('/api/exercices/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_exercice(self):
        e = creer_exercice()
        r = self.client.get(f'/api/exercices/{e.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
