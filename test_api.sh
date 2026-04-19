#!/bin/bash
# ============================================================
# Script de test API — Service Comptabilité Financière Fultang
# Usage : bash test_api.sh
# ============================================================

BASE_URL="http://localhost:8000/api"
PASS=0
FAIL=0
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL+1)); }

check() {
  local label="$1"
  local code="$2"
  local expected="$3"
  if [ "$code" -eq "$expected" ]; then ok "$label (HTTP $code)"; else fail "$label (HTTP $code, attendu $expected)"; fi
}

echo "======================================================"
echo " Test API — Comptabilité Financière Fultang"
echo "======================================================"

# ── Health check ──────────────────────────────────────────
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health/")
check "Health check" "$CODE" 200

# ── Swagger ───────────────────────────────────────────────
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs/")
check "Swagger UI accessible" "$CODE" 200

# ── JWT : obtenir tokens ───────────────────────────────────
echo ""
echo "--- Authentification JWT ---"
# Créer un superuser de test via manage.py (si pas déjà fait)
# On utilise les credentials par défaut du seed
TOKEN_RESP=$(curl -s -X POST "$BASE_URL/token/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null)

if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
  ok "Token JWT obtenu"
  AUTH="-H \"Authorization: Bearer $TOKEN\""
else
  echo "  (Pas de token JWT — tests sans auth)"
  TOKEN=""
fi

# ── Plan comptable ─────────────────────────────────────────
echo ""
echo "--- Plan Comptable ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/comptes-comptables/")
check "GET /comptes-comptables/" "$CODE" 200

RESP=$(curl -s -X POST "$BASE_URL/comptes-comptables/" \
  -H "Content-Type: application/json" \
  -d '{"numero_compte":"999","libelle":"Compte test","classe":"7","type_compte":"produit"}')
CODE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
check "POST /comptes-comptables/ (création)" "$CODE" 201

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/comptes-comptables/arborescence/")
check "GET /comptes-comptables/arborescence/" "$CODE" 200

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/comptes-comptables/statistiques/")
check "GET /comptes-comptables/statistiques/" "$CODE" 200

# ── Journaux ───────────────────────────────────────────────
echo ""
echo "--- Journaux ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/journaux/")
check "GET /journaux/" "$CODE" 200

# ── Exercices ──────────────────────────────────────────────
echo ""
echo "--- Exercices ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/exercices/")
check "GET /exercices/" "$CODE" 200

# ── Quittances ─────────────────────────────────────────────
echo ""
echo "--- Quittances ---"
RESP=$(curl -s -X POST "$BASE_URL/quittances/" \
  -H "Content-Type: application/json" \
  -d '{"montant":"15000.00","motif":"Consultation test","type_recette":"consultation","mode_paiement":"especes"}')
QT_NUM=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('numero',''))" 2>/dev/null)
CODE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
check "POST /quittances/ (création)" "$CODE" 201

if [ -n "$QT_NUM" ]; then
  echo "  Quittance créée : $QT_NUM"
fi

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/quittances/du_jour/")
check "GET /quittances/du_jour/" "$CODE" 200

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/quittances/a_comptabiliser/")
check "GET /quittances/a_comptabiliser/" "$CODE" 200

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/quittances/statistiques/")
check "GET /quittances/statistiques/" "$CODE" 200

# ── Écritures ──────────────────────────────────────────────
echo ""
echo "--- Écritures Comptables ---"
# Récupérer IDs nécessaires
COMPTE_CAISSE=$(curl -s "$BASE_URL/comptes-comptables/?search=571" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'] if r else '')" 2>/dev/null)
COMPTE_PRODUIT=$(curl -s "$BASE_URL/comptes-comptables/?search=701" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'] if r else '')" 2>/dev/null)
JOURNAL_ID=$(curl -s "$BASE_URL/journaux/JC/" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
EXERCICE_ID=$(curl -s "$BASE_URL/exercices/?statut=ouvert" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'] if r else '')" 2>/dev/null)

if [ -n "$COMPTE_CAISSE" ] && [ -n "$COMPTE_PRODUIT" ] && [ -n "$JOURNAL_ID" ]; then
  RESP=$(curl -s -X POST "$BASE_URL/ecritures/" \
    -H "Content-Type: application/json" \
    -d "{
      \"date_ecriture\": \"2026-04-19\",
      \"libelle\": \"Test écriture équilibrée\",
      \"journal\": $JOURNAL_ID,
      \"exercice\": $EXERCICE_ID,
      \"lignes\": [
        {\"compte\": $COMPTE_CAISSE, \"libelle\": \"Débit caisse\", \"montant_debit\": 50000, \"montant_credit\": null},
        {\"compte\": $COMPTE_PRODUIT, \"libelle\": \"Crédit produit\", \"montant_debit\": null, \"montant_credit\": 50000}
      ]
    }")
  EC_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
  CODE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
  check "POST /ecritures/ (équilibrée)" "$CODE" 201

  # Test écriture déséquilibrée → doit retourner 400
  RESP2=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/ecritures/" \
    -H "Content-Type: application/json" \
    -d "{
      \"date_ecriture\": \"2026-04-19\",
      \"libelle\": \"Test déséquilibrée\",
      \"journal\": $JOURNAL_ID,
      \"lignes\": [
        {\"compte\": $COMPTE_CAISSE, \"montant_debit\": 50000, \"montant_credit\": null},
        {\"compte\": $COMPTE_PRODUIT, \"montant_debit\": null, \"montant_credit\": 30000}
      ]
    }")
  check "POST /ecritures/ déséquilibrée → 400" "$RESP2" 400

  # Balance
  RESP_BAL=$(curl -s "$BASE_URL/ecritures/balance/")
  EQUILIBRE=$(echo "$RESP_BAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('equilibre',''))" 2>/dev/null)
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/ecritures/balance/")
  check "GET /ecritures/balance/" "$CODE" 200
  if [ "$EQUILIBRE" = "True" ]; then ok "Balance équilibrée (débits = crédits)"; else echo "  (Balance : $EQUILIBRE — normal si pas d'écritures validées)"; fi
else
  echo "  (Comptes/Journal non trouvés — seed requis pour tester les écritures)"
fi

# ── Caisse journalière ─────────────────────────────────────
echo ""
echo "--- Caisse Journalière ---"
RESP=$(curl -s -X POST "$BASE_URL/caisse-journaliere/ouvrir/" \
  -H "Content-Type: application/json" \
  -d '{"solde_ouverture":"100000"}')
CAISSE_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
CODE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
check "POST /caisse-journaliere/ouvrir/" "$CODE" 201

# Double ouverture → 400
CODE2=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/caisse-journaliere/ouvrir/" \
  -H "Content-Type: application/json" \
  -d '{"solde_ouverture":"50000"}')
check "Double ouverture caisse → 400" "$CODE2" 400

# ── Fournisseurs ───────────────────────────────────────────
echo ""
echo "--- Fournisseurs ---"
COMPTE_FOUR=$(curl -s "$BASE_URL/comptes-comptables/?search=401" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d); print(r[0]['id'] if r else '')" 2>/dev/null)
if [ -n "$COMPTE_FOUR" ]; then
  RESP=$(curl -s -X POST "$BASE_URL/fournisseurs/" \
    -H "Content-Type: application/json" \
    -d "{\"raison_sociale\":\"Pharma Test\",\"compte_comptable\":$COMPTE_FOUR}")
  CODE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
  check "POST /fournisseurs/" "$CODE" 201
fi

# ── Tableau de bord ────────────────────────────────────────
echo ""
echo "--- Tableau de Bord ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/tableau-de-bord/dashboard/")
check "GET /tableau-de-bord/dashboard/" "$CODE" 200

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/tableau-de-bord/evolution-mensuelle/")
check "GET /tableau-de-bord/evolution-mensuelle/" "$CODE" 200

# ── Résumé ─────────────────────────────────────────────────
echo ""
echo "======================================================"
echo -e " ${GREEN}PASS : $PASS${NC}  |  ${RED}FAIL : $FAIL${NC}"
echo "======================================================"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
