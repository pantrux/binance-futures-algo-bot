#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
WEB_BASE_URL="${WEB_BASE_URL:-http://127.0.0.1:3000}"
METRICS_API_KEY="${METRICS_API_KEY:-}"

CURL_OPTS=(
  -sS
  -L
  --max-time 15
  --connect-timeout 5
)

fail() {
  echo "❌ $1" >&2
  exit 1
}

check_status() {
  local name="$1"
  local url="$2"
  local expected_status="${3:-200}"
  local header_name="${4:-}"
  local header_value="${5:-}"
  local status
  local tmpfile

  echo "→ ${name}: ${url}"

  tmpfile="$(mktemp)"

  if [[ -n "${header_name}" && -n "${header_value}" ]]; then
    status="$(curl "${CURL_OPTS[@]}" -o "${tmpfile}" -w "%{http_code}" -H "${header_name}: ${header_value}" "${url}" || true)"
  else
    status="$(curl "${CURL_OPTS[@]}" -o "${tmpfile}" -w "%{http_code}" "${url}" || true)"
  fi

  if [[ "${status}" != "${expected_status}" ]]; then
    echo "Respuesta inesperada (${status})"
    echo "--- body ---"
    cat "${tmpfile}" || true
    echo "------------"
    rm -f "${tmpfile}"
    fail "${name} no cumple (esperado ${expected_status})"
  fi

  rm -f "${tmpfile}"
  echo "✅ ${name} (${status})"
}

check_contains() {
  local name="$1"
  local url="$2"
  local needle="$3"

  echo "→ ${name}: ${url} contiene '${needle}'"
  local body
  body="$(curl "${CURL_OPTS[@]}" "${url}")"
  if ! grep -q "${needle}" <<<"${body}"; then
    echo "--- body ---"
    echo "${body}"
    echo "------------"
    fail "${name} no contiene '${needle}'"
  fi
  echo "✅ ${name}"
}

echo "🚦 Iniciando smoke tests Synology"
echo "API_BASE_URL=${API_BASE_URL}"
echo "WEB_BASE_URL=${WEB_BASE_URL}"

check_status "API /health" "${API_BASE_URL}/health" 200
check_status "API /dashboard/summary" "${API_BASE_URL}/dashboard/summary" 200
check_status "API /trade-plans" "${API_BASE_URL}/trade-plans" 200
check_status "API /integrations/binance/testnet/ping" "${API_BASE_URL}/integrations/binance/testnet/ping" 200

if [[ -n "${METRICS_API_KEY}" ]]; then
  check_status "API /metrics (auth)" "${API_BASE_URL}/metrics" 200 "x-metrics-key" "${METRICS_API_KEY}"
else
  check_status "API /metrics" "${API_BASE_URL}/metrics" 200
fi

check_contains "WEB /" "${WEB_BASE_URL}/" "Trading Bot"

echo "✅ Smoke tests Synology completados"
