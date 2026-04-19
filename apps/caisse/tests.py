"""
Tests unitaires — App Caisse.
"""
from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.comptabilite.models import CompteComptable, Journal, ExerciceComptable
from apps.caisse.models import Quittance, CaisseJournaliere


def setup_base():
    compte = CompteComptable.objects.get_or_create(
        numero_compte='571', defaults={'libelle': 'Caisse', 'classe': '5', 'type_compte': 'tresorerie'}
    )[0]
    journal = Journal.objects.get_or_create(
        code='JC', defaults={'libelle': 'Journal de Caisse', 'compte_contrepartie': compte}
    )[0]
    exercice = ExerciceComptable.objects.get_or_create(
        annee=2026, defaults={'date_debut': date(2026, 1, 1), 'date_fin': date(2026, 12, 31), 'statut': 'ouvert'}
    )[0]
    return compte, journal, exercice


class QuittanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        setup_base()

    def test_create_quittance(self):
        r = self.client.post('/api/quittances/', {
            'montant': '15000.00', 'motif': 'Consultation',
            'type_recette': 'consultation', 'mode_paiement': 'especes',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data['numero'].startswith('QT-'))
        self.assertTrue(r.data['est_validee'])

    def test_list_quittances(self):
        r = self.client.get('/api/quittances/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_quittance(self):
        r = self.client.post('/api/quittances/', {
            'montant': '5000.00', 'motif': 'Labo',
            'type_recette': 'laboratoire', 'mode_paiement': 'mobile_money',
        }, format='json')
        qid = r.data['id']
        r2 = self.client.get(f'/api/quittances/{qid}/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

    def test_quittance_assurance_calcul_parts(self):
        """RÈGLE MÉTIER : calcul automatique part patient / part assurance."""
        r = self.client.post('/api/quittances/', {
            'montant': '20000.00', 'motif': 'Consultation assuré',
            'type_recette': 'consultation', 'mode_paiement': 'assurance',
            'est_assure': True, 'taux_couverture': '80.00',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(r.data['montant_assurance']), 16000.0)
        self.assertEqual(float(r.data['montant_patient']), 4000.0)

    def test_du_jour(self):
        r = self.client.get('/api/quittances/du_jour/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('total', r.data)

    def test_a_comptabiliser(self):
        r = self.client.get('/api/quittances/a_comptabiliser/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class CaisseJournaliereTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_ouvrir_caisse(self):
        r = self.client.post('/api/caisse-journaliere/ouvrir/', {
            'solde_ouverture': '100000.00'
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['statut'], 'ouverte')

    def test_double_ouverture_meme_jour_retourne_400(self):
        """RÈGLE MÉTIER : une seule caisse par jour."""
        self.client.post('/api/caisse-journaliere/ouvrir/', {'solde_ouverture': '100000'}, format='json')
        r = self.client.post('/api/caisse-journaliere/ouvrir/', {'solde_ouverture': '50000'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_caisses(self):
        r = self.client.get('/api/caisse-journaliere/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_fermer_caisse(self):
        r = self.client.post('/api/caisse-journaliere/ouvrir/', {'solde_ouverture': '100000'}, format='json')
        cid = r.data['id']
        r2 = self.client.patch(f'/api/caisse-journaliere/{cid}/fermer/', {'solde_physique': '98000'}, format='json')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data['statut'], 'fermee')
