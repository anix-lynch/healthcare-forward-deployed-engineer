#!/usr/bin/env bash
# Post-deploy smoke test.
#
# Usage:
#   ./deployment/smoke_test.sh [HOST]
#
# Default HOST = http://localhost:8000

set -e
HOST="${1:-http://localhost:8000}"
# Admin endpoints require ADMIN_BEARER_TOKEN. Falls back to dev placeholder
# so the smoke can run against a local docker-compose without manual setup.
ADMIN_TOKEN="${ADMIN_BEARER_TOKEN:-dev-token-not-secret}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local expected_code="$2"
  local code="$3"
  if [ "$code" = "$expected_code" ]; then
    echo "  ✅ $name ($code)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $name (got $code, expected $expected_code)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== smoke test against $HOST ==="

# 1. Health
code=$(curl -s -o /dev/null -w "%{http_code}" "$HOST/health")
check "GET /health" "200" "$code"

# 2. Status
code=$(curl -s -o /dev/null -w "%{http_code}" "$HOST/status")
check "GET /status" "200" "$code"

# 3. Triage (valid case)
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$HOST/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"case_id":"SMOKE-001","chief_complaint":"chest pain","age":62}')
check "POST /v1/ask (valid)" "200" "$code"

# 4. Triage (empty CC — should reject with 400)
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$HOST/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"case_id":"SMOKE-002","chief_complaint":""}')
check "POST /v1/ask (empty CC blocked)" "422" "$code"

# 5. Admin mode switch (bearer-auth required)
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$HOST/admin/mode" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"rules_fallback"}')
check "POST /admin/mode rules_fallback (auth)" "200" "$code"

# 6. Admin mode rejects missing token (security smoke)
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$HOST/admin/mode" \
  -H "Content-Type: application/json" \
  -d '{"mode":"off"}')
check "POST /admin/mode missing-token blocked" "401" "$code"

# Restore default
curl -s -X POST "$HOST/admin/mode" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"ai_assist"}' > /dev/null

echo ""
echo "=== summary: $PASS pass · $FAIL fail ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
