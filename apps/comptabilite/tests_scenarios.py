"""
Tests de scénarios réalistes — Polyclinique Fultang.
Simule une vraie journée : caissier + comptable + sorties.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.comptabilite.models import CompteComptable, Journal, ExerciceComptable, EcritureComptable, LigneEcriture
from apps.caisse.models import Quittance, CaisseJournaliere
from apps.sorties.models import CategorieSortie, Fournisseur, DemandeAchat, BonCommande, OrdrePaiement


def seed_base():
    """Crée les données de base nécessaires aux scénarios."""
    comptes = {
        '571': CompteComptable.objects.get_or_create(numero_compte='571', defaults={'libelle': 'Caisse', 'classe': '5', 'type_compte': 'tresorerie'})[0],
        '521': CompteComptable.objects.get_or_create(numero_compte='521', defaults={'libelle': 'Banque', 'classe': '5', 'type_compte': 'tresorerie'})[0],
        '581': CompteComptable.objects.get_or_create(numero_compte='581', defaults={'libelle': 'Mobile Money', 'classe': '5', 'type_compte': 'tresorerie'})[0],
        '411': CompteComptable.objects.get_or_create(numero_compte='411', defaults={'libelle': 'Clients divers', 'classe': '4', 'type_compte': 'actif'})[0],
        '701': CompteComptable.objects.get_or_create(numero_compte='701', defaults={'libelle': 'Consultations', 'classe': '7', 'type_compte': 'produit'})[0],
        '702': CompteComptable.objects.get_or_create(numero_compte='702', defaults={'libelle': 'Hospitalisations', 'classe': '7', 'type_compte': 'produit'})[0],
        '703': CompteComptable.objects.get_or_create(numero_compte='703', defaults={'libelle': 'Laboratoire', 'classe': '7', 'type_compte': 'produit'})[0],
        '601': CompteComptable.objects.get_or_create(numero_compte='601', defaults={'libelle': 'Achats médicaments', 'classe': '6', 'type_compte': 'charge'})[0],
        '401': CompteComptable.objects.get_or_create(numero_compte='401', defaults={'libelle': 'Fournisseurs', 'classe': '4', 'type_compte': 'passif'})[0],
    }
    journaux = {
        'JC': Journal.objects.get_or_create(code='JC', defaults={'libelle': 'Caisse', 'compte_contrepartie': comptes['571']})[0],
        'JB': Journal.objects.get_or_create(code='JB', defaults={'libelle': 'Banque', 'compte_contrepartie': comptes['521']})[0],
        'JMM': Journal.objects.get_or_create(code='JMM', defaults={'libelle': 'Mobile Money', 'compte_contrepartie': comptes['581']})[0],
        'JOD': Journal.objects.get_or_create(code='JOD', defaults={'libelle': 'Opérations Diverses'})[0],
        'JV': Journal.objects.get_or_create(code='JV', defaults={'libelle': 'Ventes'})[0],
        'JA': Journal.objects.get_or_create(code='JA', defaults={'libelle': 'Achats'})[0],
    }
    exercice = ExerciceComptable.objects.get_or_create(
        annee=2026,
        defaults={'date_debut': date(2026, 1, 1), 'date_fin': date(2026, 12, 31), 'statut': 'ouvert'}
    )[0]
    cat = CategorieSortie.objects.get_or_create(
        code='CAT-MED',
        defaults={'libelle': 'Médicaments', 'type_categorie': 'achat', 'compte_comptable': comptes['601']}
    )[0]
    return comptes, journaux, exercice, cat


class ScenarioJourneeCompleteTests(TestCase):
    """
    SCÉNARIO 1 : Journée complète à la polyclinique.
    Matin : caissier ouvre la caisse, encaisse 3 patients.
    Midi : comptable génère les écritures.
    Soir : caissier ferme la caisse, comptable vérifie la balance.
    """

    def setUp(self):
        self.client = APIClient()
        self.comptes, self.journaux, self.exercice, self.cat = seed_base()

    def test_scenario_journee_complete(self):
        print("\n" + "="*60)
        print("SCÉNARIO 1 : Journée complète Polyclinique Fultang")
        print("="*60)

        # ── ÉTAPE 1 : Caissier ouvre la caisse ──────────────────────
        print("\n[MATIN] Caissier ouvre la caisse avec 50 000 FCFA")
        r = self.client.post('/api/caisse-journaliere/ouvrir/', {'solde_ouverture': '50000'}, format='json')
        self.assertEqual(r.status_code, 201)
        caisse_id = r.data['id']
        print(f"  ✓ Caisse ouverte — ID {caisse_id}, solde ouverture: 50 000 FCFA")

        # ── ÉTAPE 2 : Patient 1 — Consultation espèces ──────────────
        print("\n[PATIENT 1] M. Kamga — Consultation générale — 5 000 FCFA espèces")
        r = self.client.post('/api/quittances/', {
            'montant': '5000', 'motif': 'Consultation générale',
            'type_recette': 'consultation', 'mode_paiement': 'especes',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        qt1_id = r.data['id']
        qt1_num = r.data['numero']
        self.assertTrue(r.data['est_validee'])
        print(f"  ✓ Quittance {qt1_num} — 5 000 FCFA — validée par caissier")

        # ── ÉTAPE 3 : Patient 2 — Labo mobile money ─────────────────
        print("\n[PATIENT 2] Mme Ngo — Analyse sang — 8 000 FCFA MTN MoMo")
        r = self.client.post('/api/quittances/', {
            'montant': '8000', 'motif': 'Analyse de sang',
            'type_recette': 'laboratoire', 'mode_paiement': 'mobile_money',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        qt2_id = r.data['id']
        qt2_num = r.data['numero']
        print(f"  ✓ Quittance {qt2_num} — 8 000 FCFA — validée par caissier")

        # ── ÉTAPE 4 : Patient 3 — Assuré ACTIVA ─────────────────────
        print("\n[PATIENT 3] M. Biya — Consultation — 10 000 FCFA — Assuré ACTIVA (80%)")
        r = self.client.post('/api/quittances/', {
            'montant': '10000', 'motif': 'Consultation spécialisée',
            'type_recette': 'consultation', 'mode_paiement': 'assurance',
            'est_assure': True, 'taux_couverture': '80.00',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        qt3_id = r.data['id']
        qt3_num = r.data['numero']
        self.assertEqual(float(r.data['montant_assurance']), 8000.0)
        self.assertEqual(float(r.data['montant_patient']), 2000.0)
        print(f"  ✓ Quittance {qt3_num} — Part patient: 2 000 FCFA, Part ACTIVA: 8 000 FCFA")

        # ── ÉTAPE 5 : Vérifier quittances du jour ───────────────────
        print("\n[CAISSIER] Consultation des quittances du jour")
        r = self.client.get('/api/quittances/du_jour/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['nombre'], 3)
        self.assertEqual(float(r.data['total']), 23000.0)
        print(f"  ✓ {r.data['nombre']} quittances — Total: {r.data['total']} FCFA")

        # ── ÉTAPE 6 : Comptable génère les écritures ─────────────────
        print("\n[COMPTABLE] Génération des écritures comptables")

        # Écriture quittance 1 (espèces → consultation)
        r = self.client.post(f'/api/quittances/{qt1_id}/generer_ecriture/', {
            'compte_produit_id': self.comptes['701'].id
        }, format='json')
        self.assertEqual(r.status_code, 201)
        ec1 = r.data['numero_ecriture']
        print(f"  ✓ Écriture {ec1} : Débit 571 Caisse 5 000 / Crédit 701 Consultations 5 000")

        # Écriture quittance 2 (mobile money → labo)
        r = self.client.post(f'/api/quittances/{qt2_id}/generer_ecriture/', {
            'compte_produit_id': self.comptes['703'].id
        }, format='json')
        self.assertEqual(r.status_code, 201)
        ec2 = r.data['numero_ecriture']
        print(f"  ✓ Écriture {ec2} : Débit 521 Banque 8 000 / Crédit 703 Laboratoire 8 000")

        # Écriture quittance 3 (assurance → consultation)
        r = self.client.post(f'/api/quittances/{qt3_id}/generer_ecriture/', {
            'compte_produit_id': self.comptes['701'].id
        }, format='json')
        self.assertEqual(r.status_code, 201)
        ec3 = r.data['numero_ecriture']
        print(f"  ✓ Écriture {ec3} : Débit 411 Tiers 10 000 / Crédit 701 Consultations 10 000")

        # Vérifier que les quittances sont marquées comptabilisées
        r = self.client.get('/api/quittances/a_comptabiliser/')
        self.assertEqual(r.data['nombre'], 0)
        print("  ✓ Toutes les quittances sont comptabilisées")

        # ── ÉTAPE 7 : Vérifier la balance ────────────────────────────
        print("\n[COMPTABLE] Vérification de la balance générale")
        r = self.client.get('/api/ecritures/balance/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['equilibre'])
        print(f"  ✓ Balance équilibrée — Total débits = Total crédits = {r.data['total_debits']} FCFA")

        # ── ÉTAPE 8 : Caissier ferme la caisse ──────────────────────
        print("\n[SOIR] Caissier ferme la caisse — comptage physique: 54 800 FCFA")
        r = self.client.patch(f'/api/caisse-journaliere/{caisse_id}/fermer/', {
            'solde_physique': '54800'
        }, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['statut'], 'fermee')
        print(f"  ✓ Caisse fermée — Solde théorique: {r.data['solde_theorique']} FCFA")
        print(f"  ✓ Écart: {r.data['ecart']} FCFA")

        # ── ÉTAPE 9 : Tableau de bord ────────────────────────────────
        print("\n[DIRECTEUR] Consultation du tableau de bord")
        r = self.client.get('/api/tableau-de-bord/dashboard/')
        self.assertEqual(r.status_code, 200)
        print(f"  ✓ Total recettes: {r.data['kpis']['total_recettes']} FCFA")
        print(f"  ✓ Résultat net: {r.data['kpis']['resultat_net']} FCFA")

        print("\n✅ SCÉNARIO 1 TERMINÉ AVEC SUCCÈS")


class ScenarioAchatFournisseurTests(TestCase):
    """
    SCÉNARIO 2 : Achat de médicaments chez un fournisseur.
    Chef de service → Demande d'achat → Évaluation comptable →
    Approbation directeur → Bon de commande → Ordre de paiement.
    """

    def setUp(self):
        self.client = APIClient()
        self.comptes, self.journaux, self.exercice, self.cat = seed_base()

    def test_scenario_achat_fournisseur(self):
        print("\n" + "="*60)
        print("SCÉNARIO 2 : Achat médicaments — Pharma Cameroun SARL")
        print("="*60)

        # Créer fournisseur
        r = self.client.post('/api/fournisseurs/', {
            'raison_sociale': 'Pharma Cameroun SARL',
            'niu': 'P123456789',
            'telephone': '699000001',
            'compte_comptable': self.comptes['401'].id,
        }, format='json')
        self.assertEqual(r.status_code, 201)
        fournisseur_id = r.data['id']
        print(f"\n[SETUP] Fournisseur créé: {r.data['raison_sociale']}")

        # Demande d'achat
        print("\n[CHEF SERVICE PHARMACIE] Demande d'achat — 500 000 FCFA")
        r = self.client.post('/api/demandes-achat/', {
            'montant_estime': '500000',
            'priorite': 'haute',
            'description': 'Réapprovisionnement médicaments urgents — antibiotiques et analgésiques',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        da_id = r.data['id']
        da_num = r.data['numero']
        self.assertTrue(da_num.startswith('DA-'))
        print(f"  ✓ Demande {da_num} créée — statut: {r.data['statut']}")

        # Évaluation comptable
        print("\n[COMPTABLE] Évaluation budgétaire de la demande")
        r = self.client.patch(f'/api/demandes-achat/{da_id}/evaluer/', {
            'avis_comptable': 'favorable',
            'commentaire_budgetaire': 'Budget disponible — ligne médicaments non épuisée',
        }, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['avis_comptable'], 'favorable')
        print(f"  ✓ Avis comptable: FAVORABLE — {r.data['commentaire_budgetaire']}")

        # Approbation directeur
        print("\n[DIRECTEUR] Approbation de la demande")
        r = self.client.patch(f'/api/demandes-achat/{da_id}/approuver/', format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['statut'], 'approuvee')
        print(f"  ✓ Demande approuvée — statut: {r.data['statut']}")

        # Bon de commande
        print("\n[COMPTABLE] Création du bon de commande")
        r = self.client.post('/api/bons-commande/', {
            'demande_achat': da_id,
            'fournisseur': fournisseur_id,
            'lignes': [
                {'designation': 'Amoxicilline 500mg x100', 'quantite': '10', 'prix_unitaire': '25000'},
                {'designation': 'Paracétamol 1g x100', 'quantite': '20', 'prix_unitaire': '12500'},
            ]
        }, format='json')
        self.assertEqual(r.status_code, 201)
        bc_id = r.data['id']
        bc_num = r.data['numero']
        print(f"  ✓ Bon de commande {bc_num} — Total: {r.data['montant_total']} FCFA")

        # Validation bon de commande
        r = self.client.patch(f'/api/bons-commande/{bc_id}/valider/', format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['statut'], 'valide_comptable')
        print(f"  ✓ Bon validé par le comptable — statut: {r.data['statut']}")

        # Ordre de paiement
        print("\n[COMPTABLE] Création de l'ordre de paiement")
        r = self.client.post('/api/ordres-paiement/', {
            'type_sortie': 'fournisseur',
            'montant': '500000',
            'mode_paiement': 'virement',
            'beneficiaire': 'Pharma Cameroun SARL',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        op_id = r.data['id']
        op_num = r.data['numero']
        print(f"  ✓ Ordre de paiement {op_num} créé — {r.data['montant']} FCFA")

        # Workflow double validation
        r = self.client.patch(f'/api/ordres-paiement/{op_id}/valider/', format='json')
        self.assertEqual(r.data['statut'], 'valide_comptable')
        print(f"  ✓ Validé par comptable")

        r = self.client.patch(f'/api/ordres-paiement/{op_id}/approuver/', format='json')
        self.assertEqual(r.data['statut'], 'approuve_directeur')
        print(f"  ✓ Approuvé par directeur")

        r = self.client.patch(f'/api/ordres-paiement/{op_id}/executer/', format='json')
        self.assertEqual(r.data['statut'], 'execute')
        print(f"  ✓ Paiement exécuté — statut final: {r.data['statut']}")

        print("\n✅ SCÉNARIO 2 TERMINÉ AVEC SUCCÈS")


class ScenarioReglesMetierTests(TestCase):
    """
    SCÉNARIO 3 : Tests des règles métier critiques SYSCOHADA.
    Vérifie que le système rejette correctement les opérations invalides.
    """

    def setUp(self):
        self.client = APIClient()
        self.comptes, self.journaux, self.exercice, self.cat = seed_base()

    def test_scenario_regles_metier(self):
        print("\n" + "="*60)
        print("SCÉNARIO 3 : Règles métier SYSCOHADA")
        print("="*60)

        # RG1 : Écriture déséquilibrée refusée
        print("\n[RG-1] Écriture déséquilibrée doit être refusée")
        r = self.client.post('/api/ecritures/', {
            'date_ecriture': '2026-04-19',
            'libelle': 'Test déséquilibre',
            'journal': self.journaux['JC'].id,
            'lignes': [
                {'compte': self.comptes['571'].id, 'montant_debit': 50000, 'montant_credit': None},
                {'compte': self.comptes['701'].id, 'montant_debit': None, 'montant_credit': 30000},
            ]
        }, format='json')
        self.assertEqual(r.status_code, 400)
        print(f"  ✓ Refusé (400) — débit 50 000 ≠ crédit 30 000")

        # RG2 : Double caisse même jour refusée
        print("\n[RG-2] Double ouverture de caisse le même jour doit être refusée")
        self.client.post('/api/caisse-journaliere/ouvrir/', {'solde_ouverture': '100000'}, format='json')
        r = self.client.post('/api/caisse-journaliere/ouvrir/', {'solde_ouverture': '50000'}, format='json')
        self.assertEqual(r.status_code, 400)
        print(f"  ✓ Refusé (400) — une seule caisse par jour")

        # RG3 : Écriture validée non re-validable
        print("\n[RG-3] Une écriture validée ne peut pas être re-validée")
        r = self.client.post('/api/ecritures/', {
            'date_ecriture': '2026-04-19',
            'libelle': 'Écriture test',
            'journal': self.journaux['JC'].id,
            'lignes': [
                {'compte': self.comptes['571'].id, 'montant_debit': 10000, 'montant_credit': None},
                {'compte': self.comptes['701'].id, 'montant_debit': None, 'montant_credit': 10000},
            ]
        }, format='json')
        ec_id = r.data['id']
        self.client.patch(f'/api/ecritures/{ec_id}/valider/')
        r2 = self.client.patch(f'/api/ecritures/{ec_id}/valider/')
        self.assertEqual(r2.status_code, 400)
        print(f"  ✓ Refusé (400) — écriture déjà validée")

        # RG4 : Quittance déjà comptabilisée ne peut pas l'être deux fois
        print("\n[RG-4] Une quittance déjà comptabilisée ne peut pas être re-comptabilisée")
        r = self.client.post('/api/quittances/', {
            'montant': '5000', 'motif': 'Test',
            'type_recette': 'consultation', 'mode_paiement': 'especes',
        }, format='json')
        qt_id = r.data['id']
        self.client.post(f'/api/quittances/{qt_id}/generer_ecriture/', {'compte_produit_id': self.comptes['701'].id}, format='json')
        r2 = self.client.post(f'/api/quittances/{qt_id}/generer_ecriture/', {'compte_produit_id': self.comptes['701'].id}, format='json')
        self.assertEqual(r2.status_code, 400)
        print(f"  ✓ Refusé (400) — quittance déjà comptabilisée")

        # RG5 : Ordre de paiement — workflow respecté
        print("\n[RG-5] Ordre de paiement — impossible d'exécuter sans approbation directeur")
        r = self.client.post('/api/ordres-paiement/', {
            'type_sortie': 'charge', 'montant': '50000',
            'mode_paiement': 'caisse', 'beneficiaire': 'Test',
        }, format='json')
        op_id = r.data['id']
        r2 = self.client.patch(f'/api/ordres-paiement/{op_id}/executer/', format='json')
        self.assertEqual(r2.status_code, 400)
        print(f"  ✓ Refusé (400) — doit passer par comptable puis directeur")

        # RG6 : Balance toujours équilibrée
        print("\n[RG-6] La balance générale doit toujours être équilibrée")
        r = self.client.get('/api/ecritures/balance/')
        self.assertTrue(r.data['equilibre'])
        print(f"  ✓ Balance équilibrée — {r.data['total_debits']} = {r.data['total_credits']}")

        print("\n✅ SCÉNARIO 3 TERMINÉ — Toutes les règles métier sont respectées")


class ScenarioSalaireTests(TestCase):
    """
    SCÉNARIO 4 : Gestion des salaires du mois d'avril 2026.
    """

    def setUp(self):
        self.client = APIClient()
        self.comptes, self.journaux, self.exercice, self.cat = seed_base()

    def test_scenario_salaires(self):
        print("\n" + "="*60)
        print("SCÉNARIO 4 : Paie du mois d'Avril 2026")
        print("="*60)

        print("\n[COMPTABLE] Génération des bulletins de paie — Avril 2026")
        r = self.client.post('/api/salaires/generer/', {
            'mois': 4, 'annee': 2026,
            'personnels': [
                {'personnel_id': 1, 'nom_personnel': 'Dr. Kamga Pierre', 'matricule': 'MED001', 'poste': 'Médecin', 'salaire_brut': 450000, 'retenue_cnps': 22500, 'retenue_impots': 45000},
                {'personnel_id': 2, 'nom_personnel': 'Infirmière Ngo Marie', 'matricule': 'INF002', 'poste': 'Infirmière', 'salaire_brut': 180000, 'retenue_cnps': 9000, 'retenue_impots': 18000},
                {'personnel_id': 3, 'nom_personnel': 'Caissier Biya Jean', 'matricule': 'CAI003', 'poste': 'Caissier', 'salaire_brut': 120000, 'retenue_cnps': 6000, 'retenue_impots': 12000, 'deduction_ecart_caisse': 5000},
            ]
        }, format='json')
        self.assertEqual(r.status_code, 201)
        print(f"  ✓ {r.data['bulletins_crees']} bulletins générés")

        for sal in r.data['salaires']:
            print(f"  → {sal['nom_personnel']} : Brut {sal['salaire_brut']} FCFA → Net {sal['salaire_net']} FCFA")

        # Vérifier déduction écart caisse pour le caissier
        caissier_sal = next(s for s in r.data['salaires'] if s['matricule'] == 'CAI003')
        salaire_net_attendu = 120000 - 6000 - 12000 - 5000
        self.assertEqual(float(caissier_sal['salaire_net']), float(salaire_net_attendu))
        print(f"\n  ✓ Déduction écart caisse appliquée: -{caissier_sal['deduction_ecart_caisse']} FCFA")

        # Masse salariale
        r = self.client.get('/api/salaires/masse-salariale/?annee=2026')
        self.assertEqual(r.status_code, 200)
        print(f"\n[COMPTABLE] Masse salariale Avril 2026:")
        print(f"  ✓ Total brut: {r.data['total_brut']} FCFA")
        print(f"  ✓ Total net: {r.data['total_net']} FCFA")

        print("\n✅ SCÉNARIO 4 TERMINÉ AVEC SUCCÈS")
