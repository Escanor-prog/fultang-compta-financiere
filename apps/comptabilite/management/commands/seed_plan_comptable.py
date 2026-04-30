"""
Commande de seed — Plan comptable OHADA, Journaux, Exercice, Prestations, Catégories.
Usage : python manage.py seed_plan_comptable
"""
from django.core.management.base import BaseCommand
from apps.comptabilite.models import (
    CompteComptable, Journal, ExerciceComptable,
    PrestationDeService, BudgetPrevisionnel,
)


class Command(BaseCommand):
    help = "Injecte le plan comptable OHADA, les journaux, l'exercice et les données de base."

    def handle(self, *args, **options):
        self.stdout.write("═" * 60)
        self.stdout.write("  SEED — Comptabilité Financière Fultang")
        self.stdout.write("═" * 60)

        self._seed_comptes()
        self._seed_journaux()
        self._seed_exercice()
        self._seed_prestations()
        self._seed_categories()

        self.stdout.write(self.style.SUCCESS("\n✅ Seed terminé avec succès !"))

    def _seed_comptes(self):
        comptes = [
            # Classe 1 — Capitaux propres
            ("10", "Capital", 1, "passif"),
            ("101", "Capital social", 1, "passif"),
            ("12", "Résultat de l'exercice", 1, "passif"),
            ("13", "Résultat net — Report à nouveau", 1, "passif"),
            # Classe 2 — Immobilisations
            ("21", "Immobilisations corporelles", 2, "actif"),
            ("215", "Matériel médical", 2, "actif"),
            ("28", "Amortissements", 2, "actif"),
            # Classe 3 — Stocks
            ("31", "Stocks de médicaments", 3, "actif"),
            ("32", "Stocks de consommables", 3, "actif"),
            # Classe 4 — Tiers
            ("40", "Fournisseurs et comptes rattachés", 4, "passif"),
            ("401", "Fournisseurs", 4, "passif"),
            ("4011", "Fournisseurs locaux", 4, "passif"),
            ("411", "Clients divers", 4, "actif"),
            ("4111", "Clients — Patients", 4, "actif"),
            ("421", "Personnel — Rémunérations dues", 4, "passif"),
            ("431", "Sécurité sociale (CNPS)", 4, "passif"),
            ("44", "État et collectivités", 4, "passif"),
            ("443", "TVA facturée", 4, "passif"),
            ("445", "TVA récupérable", 4, "actif"),
            ("511", "Assureurs — ACTIVA", 4, "actif"),
            ("512", "Assureurs — CHANAS", 4, "actif"),
            ("513", "Assureurs — SAAR", 4, "actif"),
            # Classe 5 — Trésorerie
            ("52", "Banques", 5, "tresorerie"),
            ("521", "Banque principale", 5, "tresorerie"),
            ("57", "Caisse", 5, "tresorerie"),
            ("571", "Caisse principale", 5, "tresorerie"),
            ("572", "Caisse menues dépenses", 5, "tresorerie"),
            ("58", "Virements internes", 5, "tresorerie"),
            # Classe 6 — Charges
            ("60", "Achats et variations de stocks", 6, "charge"),
            ("601", "Achats de médicaments", 6, "charge"),
            ("602", "Achats de consommables médicaux", 6, "charge"),
            ("604", "Achats de fournitures de bureau", 6, "charge"),
            ("61", "Transports", 6, "charge"),
            ("62", "Services extérieurs", 6, "charge"),
            ("63", "Autres services extérieurs", 6, "charge"),
            ("64", "Charges de personnel", 6, "charge"),
            ("641", "Salaires et traitements", 6, "charge"),
            ("645", "Charges sociales (CNPS)", 6, "charge"),
            ("66", "Charges financières", 6, "charge"),
            ("68", "Dotations aux amortissements", 6, "charge"),
            # Classe 7 — Produits
            ("70", "Ventes de produits et services", 7, "produit"),
            ("701", "Recettes consultations", 7, "produit"),
            ("702", "Recettes hospitalisations", 7, "produit"),
            ("703", "Recettes laboratoire", 7, "produit"),
            ("704", "Recettes imagerie", 7, "produit"),
            ("705", "Recettes pharmacie", 7, "produit"),
            ("706", "Recettes chirurgie", 7, "produit"),
            ("707", "Recettes maternité", 7, "produit"),
            ("708", "Autres recettes médicales", 7, "produit"),
            ("75", "Autres produits", 7, "produit"),
            ("77", "Produits financiers", 7, "produit"),
        ]

        created = 0
        for numero, libelle, classe, type_c in comptes:
            _, is_new = CompteComptable.objects.get_or_create(
                numero_compte=numero,
                defaults={
                    'libelle': libelle,
                    'classe': str(classe),
                    'type_compte': type_c,
                    'actif': True,
                }
            )
            if is_new:
                created += 1

        # Relier les parents
        for c in CompteComptable.objects.all():
            if len(c.numero_compte) > 2:
                parent_num = c.numero_compte[:-1]
                parent = CompteComptable.objects.filter(numero_compte=parent_num).first()
                if parent and c.compte_parent != parent:
                    c.compte_parent = parent
                    c.save()

        self.stdout.write(f"  📊 Comptes comptables : {created} créés / {CompteComptable.objects.count()} total")

    def _seed_journaux(self):
        journaux = [
            ("JA", "Journal des Achats", "521"),
            ("JV", "Journal des Ventes", "411"),
            ("JC", "Journal de Caisse", "571"),
            ("JB", "Journal de Banque", "521"),
            ("JMM", "Journal Mobile Money", "521"),
            ("JOD", "Journal des Opérations Diverses", None),
            ("JRN", "Journal de Report à Nouveau", None),
        ]
        created = 0
        for code, libelle, num_compte in journaux:
            contrepartie = None
            if num_compte:
                contrepartie = CompteComptable.objects.filter(numero_compte=num_compte).first()
            _, is_new = Journal.objects.get_or_create(
                code=code,
                defaults={'libelle': libelle, 'compte_contrepartie': contrepartie}
            )
            if is_new:
                created += 1
        self.stdout.write(f"  📒 Journaux : {created} créés / {Journal.objects.count()} total")

    def _seed_exercice(self):
        from datetime import date
        exercice, created = ExerciceComptable.objects.get_or_create(
            annee=2026,
            defaults={
                'date_debut': date(2026, 1, 1),
                'date_fin': date(2026, 12, 31),
                'statut': 'ouvert',
            }
        )
        status = "créé" if created else "existant"
        self.stdout.write(f"  📅 Exercice 2026 : {status} (statut: {exercice.statut})")

    def _seed_prestations(self):
        prestations = [
            ("CONS-GEN", "Consultation Générale", "consultation", 5000),
            ("CONS-SPE", "Consultation Spécialisée", "consultation", 10000),
            ("HOSP-STD", "Hospitalisation Standard (par jour)", "hospitalisation", 15000),
            ("HOSP-VIP", "Hospitalisation VIP (par jour)", "hospitalisation", 35000),
            ("LAB-NFS", "Numération Formule Sanguine", "laboratoire", 3500),
            ("LAB-GS", "Groupe Sanguin", "laboratoire", 2500),
            ("LAB-HIV", "Test VIH", "laboratoire", 5000),
            ("LAB-PALU", "Test Paludisme (GE)", "laboratoire", 2000),
            ("IMG-RX", "Radiographie Standard", "imagerie", 8000),
            ("IMG-ECHO", "Échographie", "imagerie", 15000),
            ("CHIR-MIN", "Chirurgie Mineure", "chirurgie", 50000),
            ("MAT-ACC", "Accouchement Normal", "maternite", 75000),
        ]
        type_to_compte = {
            "consultation": "701", "hospitalisation": "702",
            "laboratoire": "703", "imagerie": "704",
            "chirurgie": "706", "maternite": "707",
        }
        created = 0
        for code, libelle, type_p, tarif in prestations:
            num = type_to_compte.get(type_p, "708")
            compte = CompteComptable.objects.filter(numero_compte=num).first()
            _, is_new = PrestationDeService.objects.get_or_create(
                code=code,
                defaults={
                    'libelle': libelle,
                    'type_prestation': type_p,
                    'tarif': tarif,
                    'compte_comptable': compte,
                }
            )
            if is_new:
                created += 1
        self.stdout.write(f"  🏥 Prestations : {created} créées / {PrestationDeService.objects.count()} total")

    def _seed_categories(self):
        from apps.sorties.models import CategorieSortie
        categories = [
            ("ACH-MED", "Achats médicaments", "achat", "601"),
            ("ACH-CONS", "Achats consommables", "achat", "602"),
            ("ACH-FOUR", "Fournitures bureau", "achat", "604"),
            ("SRV-EXT", "Services extérieurs", "service", "62"),
            ("SAL", "Salaires et traitements", "salaire", "641"),
            ("CHG-SOC", "Charges sociales CNPS", "charge", "645"),
            ("INV-MAT", "Investissement matériel", "investissement", "215"),
        ]
        created = 0
        for code, libelle, type_c, num_compte in categories:
            compte = CompteComptable.objects.filter(numero_compte=num_compte).first()
            _, is_new = CategorieSortie.objects.get_or_create(
                code=code,
                defaults={
                    'libelle': libelle,
                    'type_categorie': type_c,
                    'compte_comptable': compte,
                }
            )
            if is_new:
                created += 1
        self.stdout.write(f"  📦 Catégories de sortie : {created} créées / {CategorieSortie.objects.count()} total")
