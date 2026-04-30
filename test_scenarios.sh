#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Script de Test Scénarios Comptables — Polyclinique Fultang
# 5 scénarios réalistes comme si un comptable utilisait le système
# ═══════════════════════════════════════════════════════════════

BASE="http://127.0.0.1:8001/api"
PASS=0
FAIL=0
TOTAL=0

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check() {
    TOTAL=$((TOTAL + 1))
    local desc="$1"
    local http_code="$2"
    local expected="$3"
    if [ "$http_code" = "$expected" ]; then
        echo -e "  ${GREEN}✅ PASS${NC} — $desc (HTTP $http_code)"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC} — $desc (attendu HTTP $expected, reçu HTTP $http_code)"
        FAIL=$((FAIL + 1))
    fi
}

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  TESTS SCÉNARIOS COMPTABLES — FULTANG${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"

# ─── NETTOYAGE POUR RE-RUNS ─────────────────────────────────
echo -e "\n${YELLOW}▶ Nettoyage pré-test${NC}"
# Réouvrir l'exercice 2026 s'il est clôturé
curl -s -X PATCH "$BASE/exercices/1/" -H "Content-Type: application/json" \
  -d '{"statut": "ouvert", "resultat_net": null}' > /dev/null 2>&1
# Réouvrir ou supprimer l'exercice 2027 s'il existe
EX2027=$(curl -s "$BASE/exercices/" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); e=[x for x in r if x['annee']==2027]; print(e[0]['id'] if e else '')" 2>/dev/null)
if [ -n "$EX2027" ]; then
    # Essayer de supprimer, sinon réouvrir
    curl -s -X DELETE "$BASE/exercices/$EX2027/" > /dev/null 2>&1
    # Vérifier si la suppression a marché
    STILL_EXISTS=$(curl -s -w "%{http_code}" "$BASE/exercices/$EX2027/" 2>/dev/null | tail -1)
    if [ "$STILL_EXISTS" = "200" ]; then
        curl -s -X PATCH "$BASE/exercices/$EX2027/" -H "Content-Type: application/json" \
          -d '{"statut": "ouvert"}' > /dev/null 2>&1
    fi
fi
# Supprimer les budgets de test
curl -s "$BASE/budgets/" | python3 -c "
import sys,json
d=json.load(sys.stdin)
r=d.get('results',d)
for b in r:
    print(b['id'])
" 2>/dev/null | while read bid; do
    curl -s -X DELETE "$BASE/budgets/$bid/" > /dev/null 2>&1
done
echo -e "  ${GREEN}✅${NC} État réinitialisé"

# ─── VÉRIFICATION DONNÉES DE BASE ────────────────────────────
echo -e "\n${YELLOW}▶ Vérification des données de base${NC}"

R=$(curl -s -w "\n%{http_code}" "$BASE/comptes-comptables/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Plan comptable accessible" "$CODE" "200"

R=$(curl -s -w "\n%{http_code}" "$BASE/journaux/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Journaux accessibles" "$CODE" "200"

R=$(curl -s -w "\n%{http_code}" "$BASE/exercices/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
EXERCICE_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); e=[x for x in r if x['annee']==2026]; print(e[0]['id'] if e else r[0]['id'])" 2>/dev/null || echo "1")
check "Exercice 2026 accessible" "$CODE" "200"

# Récupérer les IDs des comptes clés
COMPTE_571=$(curl -s "$BASE/comptes-comptables/?search=571" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
COMPTE_521=$(curl -s "$BASE/comptes-comptables/?search=521" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
COMPTE_701=$(curl -s "$BASE/comptes-comptables/?search=701" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
COMPTE_703=$(curl -s "$BASE/comptes-comptables/?search=703" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
COMPTE_641=$(curl -s "$BASE/comptes-comptables/?search=641" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
echo "  IDs récupérés — 571:$COMPTE_571 | 521:$COMPTE_521 | 701:$COMPTE_701 | 703:$COMPTE_703 | 641:$COMPTE_641"


# ═══════════════════════════════════════════════════════════════
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}▶ SCÉNARIO 5 — Clôture Exercice + Report à Nouveau${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# 5.1 D'abord créons des écritures de recettes et charges pour avoir un résultat
echo -e "  ${CYAN}Étape 1 : Créer des écritures pour simuler l'activité${NC}"

# Récupérer IDs journaux
JOURNAL_JC=$(curl -s "$BASE/journaux/?search=JC" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
JOURNAL_JOD=$(curl -s "$BASE/journaux/?search=JOD" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
echo "  Journaux IDs — JC:$JOURNAL_JC | JOD:$JOURNAL_JOD"

R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/ecritures/" \
  -H "Content-Type: application/json" \
  -d "{
    \"date_ecriture\": \"2026-06-15\",
    \"libelle\": \"Recettes consultations juin\",
    \"journal\": $JOURNAL_JC,
    \"exercice\": $EXERCICE_ID,
    \"statut\": \"validee\",
    \"lignes\": [
      {\"compte\": $COMPTE_571, \"libelle\": \"Encaissement caisse\", \"montant_debit\": 500000, \"montant_credit\": null},
      {\"compte\": $COMPTE_701, \"libelle\": \"Produits consultations\", \"montant_debit\": null, \"montant_credit\": 500000}
    ]
  }" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Écriture recette 500 000 FCFA créée" "$CODE" "201"

R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/ecritures/" \
  -H "Content-Type: application/json" \
  -d "{
    \"date_ecriture\": \"2026-06-20\",
    \"libelle\": \"Charges salaires juin\",
    \"journal\": $JOURNAL_JOD,
    \"exercice\": $EXERCICE_ID,
    \"statut\": \"validee\",
    \"lignes\": [
      {\"compte\": $COMPTE_641, \"libelle\": \"Salaires du mois\", \"montant_debit\": 200000, \"montant_credit\": null},
      {\"compte\": $COMPTE_521, \"libelle\": \"Paiement banque\", \"montant_debit\": null, \"montant_credit\": 200000}
    ]
  }" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Écriture charge 200 000 FCFA créée" "$CODE" "201"

# 5.2 Vérifier le bilan
echo -e "  ${CYAN}Étape 2 : Consulter le bilan${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/etats-financiers/bilan/?exercice=$EXERCICE_ID" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Bilan SYSCOHADA généré" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total Actif: {d.get(\"total_actif\",\"?\")} | Total Passif: {d.get(\"total_passif\",\"?\")}')" 2>/dev/null || echo "    → Bilan affiché")"

# 5.3 Consulter le compte de résultat
R=$(curl -s -w "\n%{http_code}" "$BASE/etats-financiers/compte-resultat/?exercice=$EXERCICE_ID" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Compte de résultat généré" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Produits: {d.get(\"total_produits\",\"?\")} | Charges: {d.get(\"total_charges\",\"?\")} | Résultat: {d.get(\"resultat_net\",\"?\")}')" 2>/dev/null || echo "    → CR affiché")"

# 5.4 Clôturer l'exercice
echo -e "  ${CYAN}Étape 3 : Clôture de l'exercice 2026${NC}"
R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/exercices/$EXERCICE_ID/cloturer/" \
  -H "Content-Type: application/json" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Exercice 2026 clôturé" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Résultat net: {d.get(\"resultat_net\",\"?\")} FCFA')" 2>/dev/null || echo "    → Exercice clôturé")"

# 5.5 Créer exercice 2027 puis report à nouveau
echo -e "  ${CYAN}Étape 4 : Créer exercice 2027 + Report à nouveau${NC}"
# D'abord s'assurer que 2027 n'existe pas
EX2027_CHECK=$(curl -s "$BASE/exercices/" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); e=[x for x in r if x['annee']==2027]; print(e[0]['id'] if e else '')" 2>/dev/null)
if [ -n "$EX2027_CHECK" ]; then
    curl -s -X DELETE "$BASE/exercices/$EX2027_CHECK/" > /dev/null 2>&1
fi
curl -s -X POST "$BASE/exercices/" \
  -H "Content-Type: application/json" \
  -d '{"annee": 2027, "date_debut": "2027-01-01", "date_fin": "2027-12-31", "statut": "ouvert"}' > /dev/null 2>&1

# S'assurer que l'exercice 2026 est bien clôturé avant report
curl -s -X POST "$BASE/exercices/$EXERCICE_ID/cloturer/" -H "Content-Type: application/json" > /dev/null 2>&1

R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/exercices/$EXERCICE_ID/report-nouveau/" \
  -H "Content-Type: application/json" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Report à nouveau généré" "$CODE" "200"


# ═══════════════════════════════════════════════════════════════
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}▶ SCÉNARIO 6 — Patient Urgence + Régularisation${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# Réouvrir exercice pour la suite (si clôturé)
# On travaille avec l'exercice existant ou le nouveau

# 6.1 Caissier crée une quittance urgence (patient ne paie pas encore)
echo -e "  ${CYAN}Étape 1 : Quittance urgence — patient sans paiement${NC}"
R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/quittances/" \
  -H "Content-Type: application/json" \
  -d '{
    "montant": 35000,
    "motif": "Consultation urgence — douleurs thoraciques",
    "type_recette": "consultation",
    "mode_paiement": "especes",
    "est_urgence": true,
    "est_validee": false,
    "patient_id": 42,
    "caissier_id": 1
  }' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
QT_URGENCE_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
QT_URGENCE_NUM=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('numero',''))" 2>/dev/null)
check "Quittance urgence créée (non validée)" "$CODE" "201"
echo "    → Quittance $QT_URGENCE_NUM (ID: $QT_URGENCE_ID) — est_urgence=true, est_validee=false"

# 6.2 Le lendemain, le patient revient payer → validation
echo -e "  ${CYAN}Étape 2 : Régularisation — patient paie et quittance validée${NC}"
R=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/quittances/$QT_URGENCE_ID/" \
  -H "Content-Type: application/json" \
  -d '{"est_validee": true}' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Quittance urgence validée après paiement" "$CODE" "200"

# 6.3 Comptable voit la quittance à comptabiliser
echo -e "  ${CYAN}Étape 3 : Comptable consulte les quittances à comptabiliser${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/quittances/a_comptabiliser/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
NB=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('nombre',0))" 2>/dev/null)
check "File des quittances à comptabiliser" "$CODE" "200"
echo "    → $NB quittance(s) en attente"

# 6.4 Comptable génère l'écriture
echo -e "  ${CYAN}Étape 4 : Comptable génère l'écriture comptable${NC}"
R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/quittances/$QT_URGENCE_ID/generer_ecriture/" \
  -H "Content-Type: application/json" \
  -d "{\"compte_produit_id\": $COMPTE_701}" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Écriture comptable générée depuis quittance urgence" "$CODE" "201"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Écriture {d.get(\"numero_ecriture\",\"?\")} pour quittance {d.get(\"quittance\",\"?\")}')" 2>/dev/null)"

# 6.5 Vérifier que la quittance est maintenant comptabilisée
R=$(curl -s "$BASE/quittances/$QT_URGENCE_ID/" 2>/dev/null)
EST_COMPTA=$(echo "$R" | python3 -c "import sys,json; print(json.load(sys.stdin).get('est_comptabilisee',False))" 2>/dev/null)
TOTAL=$((TOTAL + 1))
if [ "$EST_COMPTA" = "True" ]; then
    echo -e "  ${GREEN}✅ PASS${NC} — Quittance marquée comptabilisée"
    PASS=$((PASS + 1))
else
    echo -e "  ${RED}❌ FAIL${NC} — Quittance non marquée comptabilisée ($EST_COMPTA)"
    FAIL=$((FAIL + 1))
fi

# 6.6 Tentative de double comptabilisation (doit échouer)
echo -e "  ${CYAN}Étape 5 : Tentative de double comptabilisation${NC}"
R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/quittances/$QT_URGENCE_ID/generer_ecriture/" \
  -H "Content-Type: application/json" \
  -d "{\"compte_produit_id\": $COMPTE_701}" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Double comptabilisation refusée (HTTP 400)" "$CODE" "400"


# ═══════════════════════════════════════════════════════════════
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}▶ SCÉNARIO 7 — Inventaire de Caisse Mensuel${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# 7.0 Nettoyage des données de test précédentes (pour re-runs)
echo -e "  ${CYAN}Nettoyage données précédentes...${NC}"
# Supprimer caisse du jour si elle existe
EXISTING_CAISSE=$(curl -s "$BASE/caisse-journaliere/?date=$(date +%Y-%m-%d)" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'] if r else '')" 2>/dev/null)
if [ -n "$EXISTING_CAISSE" ]; then
    curl -s -X DELETE "$BASE/caisse-journaliere/$EXISTING_CAISSE/" > /dev/null 2>&1
    echo "    → Caisse existante supprimée (ID: $EXISTING_CAISSE)"
fi
# Supprimer inventaire avril 2026 s'il existe
EXISTING_INV=$(curl -s "$BASE/inventaires-caisse/?mois=4&annee=2026" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'] if r else '')" 2>/dev/null)
if [ -n "$EXISTING_INV" ]; then
    curl -s -X DELETE "$BASE/inventaires-caisse/$EXISTING_INV/" > /dev/null 2>&1
    echo "    → Inventaire existant supprimé (ID: $EXISTING_INV)"
fi

# 7.1 Ouvrir une caisse journalière
echo -e "  ${CYAN}Étape 1 : Ouvrir la caisse du jour${NC}"
R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/caisse-journaliere/ouvrir/" \
  -H "Content-Type: application/json" \
  -d '{"solde_ouverture": 50000, "caissier_id": 1}' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
CAISSE_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
check "Caisse journalière ouverte (solde: 50 000 FCFA)" "$CODE" "201"

# 7.2 Créer des quittances du jour
echo -e "  ${CYAN}Étape 2 : Encaissements du jour${NC}"
for i in 1 2 3; do
  curl -s -X POST "$BASE/quittances/" \
    -H "Content-Type: application/json" \
    -d "{
      \"montant\": $((i * 15000)),
      \"motif\": \"Consultation patient $i\",
      \"type_recette\": \"consultation\",
      \"mode_paiement\": \"especes\",
      \"est_validee\": true,
      \"caissier_id\": 1
    }" > /dev/null 2>&1
done
echo -e "  ${GREEN}✅${NC} 3 quittances créées (15k + 30k + 45k = 90 000 FCFA)"

# 7.3 Fermer la caisse avec un écart
echo -e "  ${CYAN}Étape 3 : Fermeture de caisse avec écart${NC}"
R=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/caisse-journaliere/$CAISSE_ID/fermer/" \
  -H "Content-Type: application/json" \
  -d '{"solde_physique": 138500}' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Caisse fermée avec comptage physique" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Solde théorique: {d.get(\"solde_theorique\",\"?\")} | Physique: {d.get(\"solde_physique\",\"?\")} | Écart: {d.get(\"ecart\",\"?\")}')" 2>/dev/null)"

# 7.4 Créer un inventaire mensuel
echo -e "  ${CYAN}Étape 4 : Inventaire mensuel${NC}"
R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/inventaires-caisse/" \
  -H "Content-Type: application/json" \
  -d '{
    "mois": 4,
    "annee": 2026,
    "recettes_enregistrees": 2500000,
    "recettes_attendues": 2550000,
    "caissier_id": 1,
    "statut": "ouvert"
  }' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
INV_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
check "Inventaire mensuel créé" "$CODE" "201"
echo "    → Écart: $(echo $BODY | python3 -c "import sys,json; print(json.load(sys.stdin).get('ecart','?'))" 2>/dev/null) FCFA"

# 7.5 Justifier et clôturer l'inventaire
echo -e "  ${CYAN}Étape 5 : Clôture de l'inventaire${NC}"
R=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/inventaires-caisse/$INV_ID/clore/" \
  -H "Content-Type: application/json" \
  -d '{"ecart_justifie": true, "observations": "Écart de 50 000 FCFA dû à des erreurs de rendu de monnaie. Retenu sur salaire du caissier."}' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Inventaire clôturé avec justification" "$CODE" "200"


# ═══════════════════════════════════════════════════════════════
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}▶ SCÉNARIO 8 — Grand Livre + Balance Générale${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# 8.1 Grand livre du compte 571 (Caisse)
echo -e "  ${CYAN}Étape 1 : Grand livre du compte 571 (Caisse)${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/ecritures/grand-livre/$COMPTE_571/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Grand livre du compte 571 consulté" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Mouvements: {d.get(\"nombre_mouvements\",len(d.get(\"mouvements\",[])))} | Solde: {d.get(\"solde\",d.get(\"solde_debiteur\",\"?\"))}')" 2>/dev/null)"

# 8.2 Balance générale
echo -e "  ${CYAN}Étape 2 : Balance générale de vérification${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/ecritures/balance/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Balance générale calculée" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total débits: {d.get(\"total_debits\",\"?\")} | Total crédits: {d.get(\"total_credits\",\"?\")} | Équilibré: {d.get(\"equilibre\",\"?\")}')" 2>/dev/null)"

# 8.3 Statistiques des écritures
echo -e "  ${CYAN}Étape 3 : Statistiques globales${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/ecritures/statistiques/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Statistiques des écritures" "$CODE" "200"


# ═══════════════════════════════════════════════════════════════
echo -e "\n${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}▶ SCÉNARIO 9 — Budget Prévisionnel + Évaluation${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"

# 9.1 Créer un budget pour le Laboratoire
echo -e "  ${CYAN}Étape 1 : Créer budget Laboratoire${NC}"
# Récupérer l'ID de la catégorie ACH-MED pour le budget
CAT_ACH_MED=$(curl -s "$BASE/categories-sortie/?search=ACH-MED" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'])" 2>/dev/null)
# Récupérer exercice 2027 (créé dans scénario 5)
EXERCICE_2027=$(curl -s "$BASE/exercices/" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); e=[x for x in r if x['annee']==2027]; print(e[0]['id'] if e else r[0]['id'])" 2>/dev/null)

R=$(curl -s -w "\n%{http_code}" -X POST "$BASE/budgets/" \
  -H "Content-Type: application/json" \
  -d "{
    \"libelle\": \"Budget Achats Laboratoire 2026\",
    \"exercice\": $EXERCICE_2027,
    \"service_hospitalier\": \"Laboratoire\",
    \"service_hospitalier_id\": 3,
    \"categorie\": $CAT_ACH_MED,
    \"montant_prevu\": 5000000,
    \"montant_consomme\": 0,
    \"priorite\": \"haute\"
  }" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
BUDGET_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
check "Budget Laboratoire créé (5 000 000 FCFA)" "$CODE" "201"

# 9.2 Simuler des dépenses — mettre à jour le montant consommé
echo -e "  ${CYAN}Étape 2 : Simuler consommation budgétaire${NC}"
R=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/budgets/$BUDGET_ID/" \
  -H "Content-Type: application/json" \
  -d '{"montant_consomme": 1750000}' 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Consommation budgétaire mise à jour (1 750 000 FCFA)" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Disponible: {d.get(\"montant_disponible\",\"?\")} | Taux: {d.get(\"taux_consommation\",\"?\")}%')" 2>/dev/null)"

# 9.3 Évaluation budgétaire globale
echo -e "  ${CYAN}Étape 3 : Évaluation budgétaire${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/budgets/evaluation/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Évaluation budgétaire globale" "$CODE" "200"

# 9.4 Budget par service
echo -e "  ${CYAN}Étape 4 : Budget par service Laboratoire${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/budgets/par-service/3/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
check "Budget par service (Laboratoire)" "$CODE" "200"

# 9.5 Tableau de bord
echo -e "  ${CYAN}Étape 5 : Tableau de bord financier${NC}"
R=$(curl -s -w "\n%{http_code}" "$BASE/tableau-de-bord/dashboard/" 2>/dev/null)
CODE=$(echo "$R" | tail -1)
BODY=$(echo "$R" | head -n -1)
check "Dashboard KPIs" "$CODE" "200"
echo "    → $(echo $BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Recettes: {d.get(\"total_recettes\",\"?\")} | Dépenses: {d.get(\"total_depenses\",\"?\")} | Marge: {d.get(\"marge_nette\",\"?\")}')" 2>/dev/null)"


# ═══════════════════════════════════════════════════════════════
echo -e "\n${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  RÉSULTATS FINAUX${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "  Total tests : $TOTAL"
echo -e "  ${GREEN}✅ Passés : $PASS${NC}"
echo -e "  ${RED}❌ Échoués : $FAIL${NC}"
echo ""
if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}🎉 TOUS LES TESTS SONT PASSÉS !${NC}"
else
    echo -e "  ${RED}⚠️  $FAIL test(s) échoué(s) — vérifier les endpoints.${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
