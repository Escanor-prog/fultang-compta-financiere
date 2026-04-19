"""
Tests unitaires — App Sorties.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.comptabilite.models import CompteComptable
from apps.sorties.models import CategorieSortie, Fournisseur


def creer_compte_charge():
    return CompteComptable.objects.get_or_create(
        numero_compte='601',
        defaults={'libelle': 'Achats médicaments', 'classe': '6', 'type_compte': 'charge'}
    )[0]


def creer_compte_fournisseur():
    return CompteComptable.objects.get_or_create(
        numero_compte='401',
        defaults={'libelle': 'Fournisseurs', 'classe': '4', 'type_compte': 'passif'}
    )[0]


class CategorieSortieTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.compte = creer_compte_charge()

    def test_create_categorie(self):
        r = self.client.post('/api/categories-sortie/', {
            'code': 'CAT-MED', 'libelle': 'Médicaments',
            'type_categorie': 'achat', 'compte_comptable': self.compte.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_list_categories(self):
        r = self.client.get('/api/categories-sortie/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_categorie(self):
        CategorieSortie.objects.create(
            code='CAT-TEST', libelle='Test', type_categorie='achat',
            compte_comptable=self.compte
        )
        r = self.client.get('/api/categories-sortie/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class FournisseurTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.compte = creer_compte_fournisseur()

    def test_create_fournisseur(self):
        r = self.client.post('/api/fournisseurs/', {
            'raison_sociale': 'Pharma Cameroun SARL',
            'niu': 'P123456789',
            'telephone': '699000000',
            'compte_comptable': self.compte.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_list_fournisseurs(self):
        r = self.client.get('/api/fournisseurs/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_fournisseur(self):
        f = Fournisseur.objects.create(
            raison_sociale='Test SA', compte_comptable=self.compte
        )
        r = self.client.get(f'/api/fournisseurs/{f.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class DemandeAchatTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_demande(self):
        r = self.client.post('/api/demandes-achat/', {
            'montant_estime': '500000', 'priorite': 'normale',
            'description': 'Achat médicaments urgents',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data['numero'].startswith('DA-'))

    def test_list_demandes(self):
        r = self.client.get('/api/demandes-achat/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_evaluer_demande(self):
        r = self.client.post('/api/demandes-achat/', {
            'montant_estime': '200000', 'priorite': 'haute',
        }, format='json')
        did = r.data['id']
        r2 = self.client.patch(f'/api/demandes-achat/{did}/evaluer/', {
            'avis_comptable': 'favorable',
            'commentaire_budgetaire': 'Budget disponible',
        }, format='json')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data['avis_comptable'], 'favorable')


class OrdrePaiementTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_ordre(self):
        r = self.client.post('/api/ordres-paiement/', {
            'type_sortie': 'fournisseur', 'montant': '150000',
            'mode_paiement': 'virement', 'beneficiaire': 'Pharma SA',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data['numero'].startswith('OP-'))

    def test_list_ordres(self):
        r = self.client.get('/api/ordres-paiement/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_workflow_validation_double(self):
        """RÈGLE MÉTIER : comptable valide → directeur approuve → exécution."""
        r = self.client.post('/api/ordres-paiement/', {
            'type_sortie': 'charge', 'montant': '50000',
            'mode_paiement': 'caisse', 'beneficiaire': 'Test',
        }, format='json')
        oid = r.data['id']
        # Valider (comptable)
        r2 = self.client.patch(f'/api/ordres-paiement/{oid}/valider/')
        self.assertEqual(r2.data['statut'], 'valide_comptable')
        # Approuver (directeur)
        r3 = self.client.patch(f'/api/ordres-paiement/{oid}/approuver/')
        self.assertEqual(r3.data['statut'], 'approuve_directeur')
        # Exécuter
        r4 = self.client.patch(f'/api/ordres-paiement/{oid}/executer/')
        self.assertEqual(r4.data['statut'], 'execute')
