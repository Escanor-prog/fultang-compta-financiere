# 🏥 Microservice Comptabilité Financière — Polyclinique Fultang

> Service Django REST dédié à la comptabilité financière hospitalière, conforme au référentiel **SYSCOHADA**.

---

## 📋 Table des matières

- [Architecture](#architecture)
- [Modules fonctionnels](#modules-fonctionnels)
- [Installation et lancement](#installation-et-lancement)
- [Endpoints API](#endpoints-api)
- [Tests](#tests)
- [Scénarios de test E2E](#scénarios-de-test-e2e)
- [Structure du projet](#structure-du-projet)

---

## Architecture

```
                    ┌────────────────────────────────┐
                    │   Polyclinique Fultang (Frontend)   │
                    └──────────────┬─────────────────┘
                                   │ REST API
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
    ┌────▼─────┐            ┌──────▼──────┐           ┌──────▼──────┐
    │  Caisse  │            │ Comptabilité │           │   Sorties   │
    │  (5 UC)  │            │   (12 UC)   │           │   (5 UC)    │
    └──────────┘            └─────────────┘           └─────────────┘
```

| Élément        | Technologie                        |
|----------------|------------------------------------|
| Framework      | Django 4.2+ / Django REST Framework |
| Base de données| PostgreSQL (SQLite en dev/test)     |
| Auth           | JWT (SimpleJWT)                    |
| Documentation  | Swagger (drf-spectacular)          |
| Conteneur      | Docker + docker-compose            |

---

## Modules fonctionnels

### 🟢 Module Caisse (`apps/caisse`)

Gestion des encaissements patients et de la trésorerie journalière.

| Fonctionnalité | Description |
|----------------|-------------|
| **Quittances** | Émission, validation, comptabilisation automatique |
| **Caisse journalière** | Ouverture/fermeture avec calcul d'écart |
| **Inventaire de caisse** | Inventaire mensuel avec justification |
| **Dépenses menues** | Enregistrement des petites dépenses |
| **Modes de paiement** | Espèces, chèque, carte, mobile money, virement, assurance |
| **Assurance** | Calcul automatique part patient / part assurance |
| **Chèques** | Suivi encaissement (non encaissé → encaissé) |

### 🟣 Module Comptabilité (`apps/comptabilite`)

Comptabilité en partie double conforme SYSCOHADA.

| Fonctionnalité | Description |
|----------------|-------------|
| **Plan comptable OHADA** | Classes 1 à 7, arborescence, statistiques |
| **Journaux** | JC, JB, JMM, JV, JA, JOD, JRN |
| **Écritures comptables** | Partie double, validation, contre-écriture |
| **Exercices comptables** | Ouverture, clôture, calcul résultat, report à nouveau |
| **États financiers** | Bilan, Compte de résultat, Flux de trésorerie |
| **Budget prévisionnel** | Par service, taux de consommation |
| **Tableau de bord** | KPIs, évolution mensuelle, résultat par service |
| **Prestations** | Catalogue des actes avec paliers tarifaires |
| **Audit** | Journal d'audit traçant toutes les opérations |

### 🔴 Module Sorties (`apps/sorties`)

Cycle achat-paiement et gestion de la paie.

| Fonctionnalité | Description |
|----------------|-------------|
| **Demandes d'achat** | Soumission → évaluation comptable → approbation directeur |
| **Bons de commande** | Création, validation comptable, approbation, envoi |
| **Ordres de paiement** | Workflow triple : comptable → directeur → exécution |
| **Fournisseurs** | Répertoire avec historique des commandes |
| **Factures** | Réception, suivi paiement, factures impayées |
| **Salaires** | Génération bulletins, calcul net, paiement, masse salariale |
| **Charges sociales** | CNPS, assurance, impôts |

---

## Installation et lancement

### Option 1 : Docker (recommandé)

```bash
# Cloner le projet
git clone https://github.com/Escanor-prog/fultang-compta-financiere.git
cd fultang-compta-financiere

# Lancer avec docker-compose
docker-compose up --build
```

Le serveur démarre sur `http://localhost:8001/api/`.

### Option 2 : Installation locale

```bash
# Cloner et entrer dans le projet
git clone https://github.com/Escanor-prog/fultang-compta-financiere.git
cd fultang-compta-financiere

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Charger les données initiales (plan comptable OHADA + journaux + exercice)
python manage.py seed_initial

# Lancer le serveur (port 8001 pour éviter les conflits)
python manage.py runserver 8001
```

### Vérification du bon fonctionnement

```bash
# Health check
curl http://localhost:8001/api/health/

# Réponse attendue :
# {"service": "Comptabilité Financière", "status": "ok", "version": "1.0.0"}
```

### Documentation Swagger

Accéder à la documentation interactive : [http://localhost:8001/api/docs/](http://localhost:8001/api/docs/)

---

## Endpoints API

### Caisse (`/api/`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET/POST` | `/api/quittances/` | Lister / Créer une quittance |
| `GET` | `/api/quittances/{id}/` | Détail d'une quittance |
| `GET` | `/api/quittances/du_jour/` | Quittances du jour (nombre + total) |
| `GET` | `/api/quittances/du_mois/` | Quittances du mois en cours |
| `GET` | `/api/quittances/a_comptabiliser/` | Quittances en attente de comptabilisation |
| `POST` | `/api/quittances/{id}/generer_ecriture/` | Générer l'écriture comptable |
| `GET` | `/api/quittances/statistiques/` | Statistiques globales |
| `GET` | `/api/quittances/statistiques_avancees/` | Évolution mensuelle |
| `GET` | `/api/quittances/export_csv/` | Export CSV par période |
| `POST` | `/api/caisse-journaliere/ouvrir/` | Ouvrir la caisse du jour |
| `PATCH` | `/api/caisse-journaliere/{id}/fermer/` | Fermer avec comptage physique |
| `POST` | `/api/inventaires-caisse/` | Créer un inventaire mensuel |
| `PATCH` | `/api/inventaires-caisse/{id}/clore/` | Clôturer l'inventaire |
| `GET/POST` | `/api/depenses-menues/` | Dépenses menues |
| `GET/POST` | `/api/cheques/` | Gestion des chèques |
| `POST` | `/api/cheques/{id}/encaisser/` | Encaisser un chèque |
| `GET` | `/api/cheques/non-encaisses/` | Chèques en attente |

### Comptabilité (`/api/`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET/POST` | `/api/comptes-comptables/` | Plan comptable OHADA |
| `GET` | `/api/comptes-comptables/arborescence/` | Arborescence par classe |
| `GET` | `/api/comptes-comptables/statistiques/` | Stats du plan comptable |
| `GET/POST` | `/api/journaux/` | Journaux comptables |
| `GET/POST` | `/api/ecritures/` | Écritures comptables |
| `PATCH` | `/api/ecritures/{id}/valider/` | Valider une écriture |
| `GET` | `/api/ecritures/grand-livre/{compte_id}/` | Grand livre d'un compte |
| `GET` | `/api/ecritures/balance/` | Balance générale |
| `GET` | `/api/ecritures/statistiques/` | Statistiques des écritures |
| `GET/POST` | `/api/exercices/` | Exercices comptables |
| `POST` | `/api/exercices/{id}/cloturer/` | Clôturer un exercice |
| `POST` | `/api/exercices/{id}/report-nouveau/` | Générer le report à nouveau |
| `GET` | `/api/etats-financiers/bilan/` | Bilan SYSCOHADA |
| `GET` | `/api/etats-financiers/compte-resultat/` | Compte de résultat |
| `GET` | `/api/etats-financiers/flux-tresorerie/` | Tableau des flux |
| `GET/POST` | `/api/budgets/` | Budgets prévisionnels |
| `GET` | `/api/budgets/evaluation/` | Évaluation budgétaire globale |
| `GET` | `/api/budgets/par-service/{id}/` | Budget par service |
| `GET` | `/api/tableau-de-bord/dashboard/` | KPIs financiers |
| `GET` | `/api/tableau-de-bord/evolution-mensuelle/` | Courbe mensuelle |
| `GET` | `/api/tableau-de-bord/resultat-par-service/` | Résultat par service hospitalier |
| `GET/POST` | `/api/prestations-de-service/` | Catalogue des prestations |
| `GET` | `/api/audit-log/` | Journal d'audit |

### Sorties (`/api/`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET/POST` | `/api/demandes-achat/` | Demandes d'achat |
| `PATCH` | `/api/demandes-achat/{id}/evaluer/` | Évaluation comptable |
| `PATCH` | `/api/demandes-achat/{id}/approuver/` | Approbation directeur |
| `GET/POST` | `/api/bons-commande/` | Bons de commande |
| `PATCH` | `/api/bons-commande/{id}/valider/` | Validation comptable |
| `GET/POST` | `/api/ordres-paiement/` | Ordres de paiement |
| `PATCH` | `/api/ordres-paiement/{id}/valider/` | Validation comptable |
| `PATCH` | `/api/ordres-paiement/{id}/approuver/` | Approbation directeur |
| `PATCH` | `/api/ordres-paiement/{id}/executer/` | Exécuter le paiement |
| `GET/POST` | `/api/fournisseurs/` | Répertoire fournisseurs |
| `GET` | `/api/fournisseurs/{id}/historique/` | Historique d'un fournisseur |
| `GET/POST` | `/api/factures-fournisseur/` | Factures fournisseurs |
| `GET` | `/api/factures-fournisseur/impayees/` | Factures impayées |
| `POST` | `/api/salaires/generer/` | Générer les bulletins |
| `PATCH` | `/api/salaires/{id}/payer/` | Payer un salaire |
| `GET` | `/api/salaires/masse-salariale/` | Masse salariale annuelle |
| `GET/POST` | `/api/charges-sociales/` | Charges sociales |
| `GET/POST` | `/api/categories-sortie/` | Catégories de dépenses |

---

## Tests

Le microservice dispose de **3 niveaux de tests** :

### 1️⃣ Tests unitaires Django (automatisés)

Tests Django classiques avec la base de test SQLite. **Aucun serveur requis.**

```bash
# Lancer TOUS les tests unitaires
python manage.py test --settings=config.settings_test -v 2

# Lancer les tests d'un module spécifique
python manage.py test apps.caisse --settings=config.settings_test -v 2
python manage.py test apps.comptabilite --settings=config.settings_test -v 2
python manage.py test apps.sorties --settings=config.settings_test -v 2
```

**Couverture des tests unitaires :**

| Module | Fichier | Tests |
|--------|---------|-------|
| Caisse | `apps/caisse/tests.py` | Création quittance, quittance assurée (calcul parts), quittances du jour, ouverture/fermeture caisse, double ouverture refusée |
| Comptabilité | `apps/comptabilite/tests.py` | CRUD comptes/journaux/exercices, écriture équilibrée, écriture déséquilibrée (→ 400), validation, double validation refusée, balance, grand livre |
| Sorties | `apps/sorties/tests.py` | CRUD catégories/fournisseurs, demande d'achat + évaluation, ordres de paiement + workflow complet |

### 2️⃣ Tests de scénarios Python (automatisés)

Tests réalistes simulant une vraie journée de travail à la polyclinique. **Aucun serveur requis.**

```bash
python manage.py test apps.comptabilite.tests_scenarios --settings=config.settings_test -v 2
```

| Scénario | Description | Ce qui est testé |
|----------|-------------|-----------------|
| **Scénario 1** | Journée complète | Ouverture caisse → 3 patients (espèces, mobile money, assurance) → génération écritures → vérification balance → fermeture caisse → tableau de bord |
| **Scénario 2** | Achat fournisseur | Création fournisseur → DA → évaluation comptable → approbation directeur → BC avec lignes → OP → workflow triple validation → exécution |
| **Scénario 3** | Règles métier SYSCOHADA | Écriture déséquilibrée refusée, double caisse refusée, double validation refusée, double comptabilisation refusée, OP sans approbation refusé, balance équilibrée |
| **Scénario 4** | Paie mensuelle | Génération 3 bulletins → calcul net automatique → déduction écart caisse → masse salariale |

### 3️⃣ Tests E2E API (curl — serveur requis)

Scripts bash qui testent l'API en conditions réelles avec `curl`. **Le serveur doit tourner.**

```bash
# ⚠️ PRÉREQUIS : le serveur doit être lancé sur le port 8001
python manage.py runserver 8001

# Dans un autre terminal :

# Test rapide de tous les endpoints (20+ tests)
bash test_api.sh

# Scénarios métier 5 à 9 (clôture exercice, urgence, inventaire, grand livre, budget)
bash test_scenarios.sh

# Scénarios métier 10 à 15 (cycle achat complet, paie, assurance, chèque, audit, stats)
bash test_scenarios_10_15.sh
```

#### Détail des scénarios E2E

| Script | Scénario | Description |
|--------|----------|-------------|
| `test_scenarios.sh` | **5 — Clôture exercice** | Écritures recettes/charges → bilan → résultat → clôture → report à nouveau 2027 |
| `test_scenarios.sh` | **6 — Urgence + régularisation** | Quittance urgence non validée → patient revient payer → validation → comptabilisation → double comptabilisation refusée |
| `test_scenarios.sh` | **7 — Inventaire mensuel** | Ouverture caisse → 3 quittances espèces → fermeture avec écart → inventaire mensuel → clôture avec justification |
| `test_scenarios.sh` | **8 — Grand livre + balance** | Grand livre compte 571 → balance générale → vérification équilibre → statistiques |
| `test_scenarios.sh` | **9 — Budget prévisionnel** | Budget laboratoire 5M FCFA → consommation 1,75M → évaluation → budget par service → dashboard KPIs |
| `test_scenarios_10_15.sh` | **10 — Cycle achat complet** | Fournisseur → DA → évaluation → approbation → BC avec 3 lignes → facture → factures impayées → OP → validation → approbation → exécution → facture marquée payée → historique fournisseur |
| `test_scenarios_10_15.sh` | **11 — Paie mensuelle** | Génération 4 bulletins → calcul salaire net → charge CNPS → paiement → double paiement refusé → masse salariale |
| `test_scenarios_10_15.sh` | **12 — Patient assuré** | Quittance 150 000 FCFA assurance 70% → vérification parts (45k patient / 105k assurance) → écriture comptable |
| `test_scenarios_10_15.sh` | **13 — Chèque** | Quittance par chèque → enregistrement détails → chèques non encaissés → encaissement → double encaissement refusé |
| `test_scenarios_10_15.sh` | **14 — Audit trail** | Journal d'audit global → filtrage par module (quittance) → filtrage par action (création) → audit écritures |
| `test_scenarios_10_15.sh` | **15 — Statistiques** | Stats quittances → évolution mensuelle → quittances jour/mois → export CSV → catalogue prestations |

---

## Structure du projet

```
fultang-compta-financiere/
├── apps/
│   ├── caisse/                     # Module Caisse
│   │   ├── models/
│   │   │   ├── quittance.py        # Quittance (pivot du module)
│   │   │   ├── caisse_journaliere.py # Caisse + Inventaire
│   │   │   └── paiements.py        # Chèque, Mobile Money, Carte, Virement
│   │   ├── serializers/
│   │   ├── views/
│   │   ├── urls.py
│   │   └── tests.py                # 7 tests unitaires
│   │
│   ├── comptabilite/               # Module Comptabilité
│   │   ├── models/
│   │   │   ├── compte_comptable.py  # Plan comptable OHADA
│   │   │   ├── journal.py           # Journaux (JC, JB, JMM...)
│   │   │   ├── ecriture_comptable.py# Partie double
│   │   │   ├── exercice_comptable.py# Exercices annuels
│   │   │   ├── budget_previsionnel.py
│   │   │   ├── prestation_de_service.py
│   │   │   └── audit_log.py        # Traçabilité SYSCOHADA
│   │   ├── management/commands/
│   │   │   ├── seed_initial.py      # Données initiales
│   │   │   └── seed_plan_comptable.py
│   │   ├── serializers/
│   │   ├── views/
│   │   ├── urls.py
│   │   ├── tests.py                # 13 tests unitaires
│   │   └── tests_scenarios.py      # 4 scénarios réalistes
│   │
│   └── sorties/                    # Module Sorties
│       ├── models/
│       │   ├── demande_achat.py     # DA + Bon de commande
│       │   ├── facture.py           # Facture + Ordre de paiement
│       │   ├── fournisseur.py       # Répertoire fournisseurs
│       │   ├── salaire.py           # Paie + Charges sociales
│       │   └── categorie_sortie.py  # Catégories de dépenses
│       ├── serializers/
│       ├── views/
│       ├── urls.py
│       └── tests.py                # 9 tests unitaires
│
├── config/
│   ├── settings.py                 # Configuration principale
│   ├── settings_test.py            # Config tests (SQLite)
│   └── urls.py                     # Routes API
│
├── test_api.sh                     # Tests E2E rapides (20+ endpoints)
├── test_scenarios.sh               # Scénarios E2E 5-9
├── test_scenarios_10_15.sh         # Scénarios E2E 10-15
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

---

## Règles métier implémentées

| Code | Règle | Module |
|------|-------|--------|
| RG-01 | Toute écriture comptable doit être équilibrée (total débits = total crédits) | Comptabilité |
| RG-02 | Une seule caisse journalière peut être ouverte par jour | Caisse |
| RG-03 | Une écriture validée ne peut pas être modifiée ni re-validée | Comptabilité |
| RG-04 | Une quittance comptabilisée ne peut pas être re-comptabilisée | Caisse |
| RG-05 | Un ordre de paiement doit suivre le workflow : comptable → directeur → exécution | Sorties |
| RG-06 | La balance générale doit toujours être équilibrée | Comptabilité |
| RG-07 | Le calcul automatique des parts patient/assurance selon le taux de couverture | Caisse |
| RG-08 | Le salaire net = brut − CNPS − impôts − déduction écart caisse | Sorties |
| RG-09 | Un salaire déjà payé ne peut pas être re-payé | Sorties |
| RG-10 | Un chèque déjà encaissé ne peut pas être re-encaissé | Caisse |
| RG-11 | L'exécution d'un OP marque automatiquement la facture liée comme payée | Sorties |
| RG-12 | Une demande banque de sang peut être approuvée sans évaluation comptable | Sorties |

---

## Auteurs

- **Charles-Henry** — Module Caisse
- **Moffo** — Module Sorties

Microservice développé dans le cadre du projet **Polyclinique Fultang** — Architecture Microservices.
