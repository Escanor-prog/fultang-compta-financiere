"""
Commande de seed : plan comptable OHADA minimal + journaux + exercice 2026.
Usage : python manage.py seed_initial
"""
from django.core.management.base import BaseCommand
from django.db import transaction


COMPTES = [
    # Classe 1 — Capitaux
    ('10', 'Capital', '1', 'passif'),
    ('101', 'Capital social', '1', 'passif'),
    ('12', 'Report à nouveau', '1', 'passif'),
    ('121', 'Report à nouveau créditeur', '1', 'passif'),
    ('129', 'Report à nouveau débiteur', '1', 'passif'),
    ('13', 'Résultat net de l\'exercice', '1', 'passif'),
    ('131', 'Résultat net — Bénéfice', '1', 'passif'),
    ('139', 'Résultat net — Perte', '1', 'passif'),
    # Classe 2 — Immobilisations
    ('21', 'Immobilisations incorporelles', '2', 'actif'),
    ('22', 'Terrains', '2', 'actif'),
    ('23', 'Bâtiments', '2', 'actif'),
    ('24', 'Matériel et mobilier', '2', 'actif'),
    ('241', 'Matériel médical', '2', 'actif'),
    ('242', 'Matériel informatique', '2', 'actif'),
    ('28', 'Amortissements des immobilisations', '2', 'actif'),
    # Classe 3 — Stocks
    ('31', 'Marchandises', '3', 'actif'),
    ('32', 'Matières premières', '3', 'actif'),
    ('37', 'Stocks de médicaments', '3', 'actif'),
    # Classe 4 — Tiers
    ('40', 'Fournisseurs', '4', 'passif'),
    ('401', 'Fournisseurs — dettes en compte', '4', 'passif'),
    ('41', 'Clients', '4', 'actif'),
    ('411', 'Clients divers', '4', 'actif'),
    ('4111', 'Clients — patients non assurés', '4', 'actif'),
    ('41110', 'ACTIVA Assurances', '4', 'actif'),
    ('41111', 'CHANAS Assurances', '4', 'actif'),
    ('41112', 'SAAR Assurances', '4', 'actif'),
    ('42', 'Personnel', '4', 'passif'),
    ('421', 'Personnel — rémunérations dues', '4', 'passif'),
    ('43', 'Organismes sociaux', '4', 'passif'),
    ('431', 'CNPS', '4', 'passif'),
    ('44', 'État et collectivités', '4', 'passif'),
    ('447', 'État — impôts et taxes', '4', 'passif'),
    # Classe 5 — Trésorerie
    ('52', 'Banques', '5', 'tresorerie'),
    ('521', 'Banque principale', '5', 'tresorerie'),
    ('57', 'Caisse', '5', 'tresorerie'),
    ('571', 'Caisse principale', '5', 'tresorerie'),
    ('58', 'Mobile Money', '5', 'tresorerie'),
    ('581', 'Orange Money', '5', 'tresorerie'),
    ('582', 'MTN Mobile Money', '5', 'tresorerie'),
    # Classe 6 — Charges
    ('60', 'Achats', '6', 'charge'),
    ('601', 'Achats de médicaments', '6', 'charge'),
    ('602', 'Achats de fournitures médicales', '6', 'charge'),
    ('603', 'Achats de fournitures de bureau', '6', 'charge'),
    ('61', 'Services extérieurs', '6', 'charge'),
    ('62', 'Autres services extérieurs', '6', 'charge'),
    ('63', 'Impôts et taxes', '6', 'charge'),
    ('64', 'Charges de personnel', '6', 'charge'),
    ('641', 'Salaires et traitements', '6', 'charge'),
    ('645', 'Charges sociales', '6', 'charge'),
    ('66', 'Charges financières', '6', 'charge'),
    ('68', 'Dotations aux amortissements', '6', 'charge'),
    ('681', 'Dotations aux amortissements d\'exploitation', '6', 'charge'),
    # Classe 7 — Produits
    ('70', 'Ventes de prestations de services', '7', 'produit'),
    ('701', 'Consultations médicales', '7', 'produit'),
    ('702', 'Hospitalisations', '7', 'produit'),
    ('703', 'Examens de laboratoire', '7', 'produit'),
    ('704', 'Imagerie médicale', '7', 'produit'),
    ('705', 'Actes chirurgicaux', '7', 'produit'),
    ('706', 'Pharmacie', '7', 'produit'),
    ('707', 'Soins infirmiers', '7', 'produit'),
    ('75', 'Autres produits d\'exploitation', '7', 'produit'),
    ('77', 'Produits financiers', '7', 'produit'),
]

JOURNAUX = [
    ('JA', 'Journal des Achats', '401'),
    ('JV', 'Journal des Ventes', '411'),
    ('JC', 'Journal de Caisse', '571'),
    ('JB', 'Journal de Banque', '521'),
    ('JMM', 'Journal Mobile Money', '581'),
    ('JOD', 'Journal des Opérations Diverses', None),
    ('JRN', 'Journal de Report à Nouveau', None),
]

CATEGORIES_SORTIE = [
    ('CAT-MED', 'Médicaments et consommables', 'achat', '601'),
    ('CAT-FOUR', 'Fournitures médicales', 'achat', '602'),
    ('CAT-BUREAU', 'Fournitures de bureau', 'achat', '603'),
    ('CAT-SERV', 'Services extérieurs', 'service', '61'),
    ('CAT-SAL', 'Salaires', 'salaire', '641'),
    ('CAT-SOC', 'Charges sociales', 'charge_sociale', '645'),
    ('CAT-INV', 'Investissements', 'investissement', '24'),
    ('CAT-FONC', 'Fonctionnement général', 'fonctionnement', '62'),
]

PRESTATIONS = [
    ('PREST-CONS-001', 'Consultation générale', 'consultation', '701', 5000),
    ('PREST-CONS-002', 'Consultation spécialisée', 'consultation', '701', 10000),
    ('PREST-HOSP-001', 'Hospitalisation (1-5 jours)', 'hospitalisation', '702', 35000),
    ('PREST-HOSP-002', 'Hospitalisation (6+ jours)', 'hospitalisation', '702', 0),
    ('PREST-LAB-001', 'Analyse de sang', 'laboratoire', '703', 8000),
    ('PREST-LAB-002', 'Analyse d\'urine', 'laboratoire', '703', 5000),
    ('PREST-IMG-001', 'Radiographie', 'imagerie', '704', 15000),
    ('PREST-IMG-002', 'Échographie', 'imagerie', '704', 25000),
    ('PREST-CHIR-001', 'Acte chirurgical mineur', 'chirurgie', '705', 50000),
    ('PREST-PHARM-001', 'Dispensation médicaments', 'pharmacie', '706', 0),
]


class Command(BaseCommand):
    help = 'Seed initial : plan comptable OHADA, journaux, exercice 2026, catégories, prestations'

    def handle(self, *args, **options):
        from apps.comptabilite.models import CompteComptable, Journal, ExerciceComptable
        from apps.sorties.models import CategorieSortie
        from apps.comptabilite.models import PrestationDeService
        from datetime import date

        with transaction.atomic():
            self.stdout.write('📊 Création du plan comptable OHADA...')
            comptes_map = {}
            for numero, libelle, classe, type_c in COMPTES:
                obj, created = CompteComptable.objects.get_or_create(
                    numero_compte=numero,
                    defaults={'libelle': libelle, 'classe': classe, 'type_compte': type_c}
                )
                comptes_map[numero] = obj
                if created:
                    self.stdout.write(f'  ✓ {numero} — {libelle}')

            self.stdout.write('📒 Création des journaux...')
            for code, libelle, compte_num in JOURNAUX:
                contrepartie = comptes_map.get(compte_num) if compte_num else None
                obj, created = Journal.objects.get_or_create(
                    code=code,
                    defaults={'libelle': libelle, 'compte_contrepartie': contrepartie}
                )
                if created:
                    self.stdout.write(f'  ✓ {code} — {libelle}')

            self.stdout.write('📅 Création de l\'exercice 2026...')
            exercice, created = ExerciceComptable.objects.get_or_create(
                annee=2026,
                defaults={
                    'date_debut': date(2026, 1, 1),
                    'date_fin': date(2026, 12, 31),
                    'statut': 'ouvert',
                }
            )
            if created:
                self.stdout.write('  ✓ Exercice 2026 créé')

            self.stdout.write('🗂️  Création des catégories de sortie...')
            for code, libelle, type_c, compte_num in CATEGORIES_SORTIE:
                compte = comptes_map.get(compte_num)
                if compte:
                    obj, created = CategorieSortie.objects.get_or_create(
                        code=code,
                        defaults={'libelle': libelle, 'type_categorie': type_c, 'compte_comptable': compte}
                    )
                    if created:
                        self.stdout.write(f'  ✓ {code} — {libelle}')

            self.stdout.write('🏥 Création des prestations de service...')
            for code, libelle, type_p, compte_num, tarif in PRESTATIONS:
                compte = comptes_map.get(compte_num)
                if compte:
                    obj, created = PrestationDeService.objects.get_or_create(
                        code=code,
                        defaults={
                            'libelle': libelle,
                            'type_prestation': type_p,
                            'tarif': tarif,
                            'compte_comptable': compte,
                        }
                    )
                    if created:
                        self.stdout.write(f'  ✓ {code} — {libelle}')

        self.stdout.write(self.style.SUCCESS('\n✅ Seed terminé avec succès !'))
        self.stdout.write(f'   Comptes : {CompteComptable.objects.count()}')
        self.stdout.write(f'   Journaux : {Journal.objects.count()}')
        self.stdout.write(f'   Exercices : {ExerciceComptable.objects.count()}')
        self.stdout.write(f'   Catégories : {CategorieSortie.objects.count()}')
        self.stdout.write(f'   Prestations : {PrestationDeService.objects.count()}')
