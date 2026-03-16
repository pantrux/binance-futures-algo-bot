#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8010}"
WEB_BASE_URL="${WEB_BASE_URL:-http://127.0.0.1:3012}"
METRICS_API_KEY="${METRICS_API_KEY:-}"
STRICT_EXTERNAL_CHECKS="${STRICT_EXTERNAL_CHECKS:-true}"
COMMAND_CENTER_CONTEXT_PRESENT="false"

CURL_OPTS=(
  -sS
  -L
  --max-time 15
  --connect-timeout 5
)

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
  trap 'rm -f "${tmpfile}"' RETURN

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
    echo "❌ ${name} no cumple (esperado ${expected_status})" >&2
    return 1
  fi

  echo "✅ ${name} (${status})"
}

check_contains() {
  local name="$1"
  local url="$2"
  local needle="$3"
  local status
  local body
  local tmpfile

  echo "→ ${name}: ${url} contiene '${needle}'"

  tmpfile="$(mktemp)"
  trap 'rm -f "${tmpfile}"' RETURN

  status="$(curl "${CURL_OPTS[@]}" -o "${tmpfile}" -w "%{http_code}" "${url}" || true)"
  body="$(cat "${tmpfile}" || true)"

  if [[ "${status}" != "200" ]]; then
    echo "--- body ---"
    echo "${body}"
    echo "------------"
    echo "❌ ${name} respondió HTTP ${status} (esperado 200)" >&2
    return 1
  fi

  if [[ -z "${body}" ]]; then
    echo "❌ ${name} sin respuesta desde ${url}" >&2
    return 1
  fi

  if ! grep -qF "${needle}" <<<"${body}"; then
    echo "--- body ---"
    echo "${body}"
    echo "------------"
    echo "❌ ${name} no contiene '${needle}'" >&2
    return 1
  fi

  echo "✅ ${name}"
}

fetch_body() {
  local name="$1"
  local url="$2"
  local tmpfile
  local status
  local body

  echo "→ ${name}: descargando ${url}" >&2

  tmpfile="$(mktemp)"
  trap 'rm -f "${tmpfile}"' RETURN

  status="$(curl "${CURL_OPTS[@]}" -o "${tmpfile}" -w "%{http_code}" "${url}" || true)"
  body="$(cat "${tmpfile}" || true)"

  if [[ "${status}" != "200" ]]; then
    echo "--- body ---" >&2
    echo "${body}" >&2
    echo "------------" >&2
    echo "❌ ${name} respondió HTTP ${status} (esperado 200)" >&2
    return 1
  fi

  if [[ -z "${body}" ]]; then
    echo "❌ ${name} sin respuesta desde ${url}" >&2
    return 1
  fi

  printf '%s' "${body}"
}

check_body_contains() {
  local name="$1"
  local body="$2"
  local needle="$3"

  echo "→ ${name}: contiene '${needle}'"

  if ! grep -qF "${needle}" <<<"${body}"; then
    echo "--- body ---"
    echo "${body}"
    echo "------------"
    echo "❌ ${name} no contiene '${needle}'" >&2
    return 1
  fi

  echo "✅ ${name}"
}

check_command_center_json() {
  local name="$1"
  local url="$2"
  local tmpfile
  local status

  echo "→ ${name}: ${url} responde payload enriquecido"

  tmpfile="$(mktemp)"
  trap 'rm -f "${tmpfile}"' RETURN

  status="$(curl "${CURL_OPTS[@]}" -o "${tmpfile}" -w "%{http_code}" "${url}" || true)"

  if [[ "${status}" != "200" ]]; then
    echo "--- body ---"
    cat "${tmpfile}" || true
    echo "------------"
    echo "❌ ${name} respondió HTTP ${status} (esperado 200)" >&2
    return 1
  fi

  local validation_output

  validation_output="$(python3 - <<'PY' "${tmpfile}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
ops = payload.get('operation_snapshots')
assert isinstance(ops, list), 'operation_snapshots no es lista'
has_non_empty_context = False
if not ops:
    print('WARN_EMPTY_OPERATION_SNAPSHOTS')
else:
    op = ops[0]
    required = [
        'order_history',
        'position_history',
        'risk_event_history',
        'timeline_history',
        'reconciliation_recommended_actions',
        'latest_risk_context',
    ]
    missing = [key for key in required if key not in op]
    assert not missing, f'faltan campos en operation_snapshot: {missing}'
    assert isinstance(op['timeline_history'], list), 'timeline_history no es lista'
    assert len(op['timeline_history']) <= 20, 'timeline_history excede límite esperado de 20'
    assert op['latest_risk_context'] is None or isinstance(op['latest_risk_context'], dict), 'latest_risk_context debe ser dict o None'
    has_non_empty_context = bool(op['latest_risk_context'])
recent = payload.get('recent_risk_events')
assert isinstance(recent, list), 'recent_risk_events no es lista'
if recent:
    for item in recent:
        assert 'context' in item, 'recent_risk_events[*] no expone context'
        assert item.get('context') is None or isinstance(item.get('context'), dict), 'recent_risk_events[*].context debe ser dict o None'
        has_non_empty_context = has_non_empty_context or bool(item.get('context'))
print('OK')
print(f"HAS_NON_EMPTY_CONTEXT={'1' if has_non_empty_context else '0'}")
PY
)"

  echo "${validation_output}"
  if grep -q 'HAS_NON_EMPTY_CONTEXT=1' <<<"${validation_output}"; then
    COMMAND_CENTER_CONTEXT_PRESENT="true"
  else
    COMMAND_CENTER_CONTEXT_PRESENT="false"
  fi

  echo "✅ ${name}"
}

echo "🚦 Iniciando smoke tests Synology"
echo "API_BASE_URL=${API_BASE_URL}"
echo "WEB_BASE_URL=${WEB_BASE_URL}"

check_status "API /health" "${API_BASE_URL}/health" 200
check_status "API /dashboard/summary" "${API_BASE_URL}/dashboard/summary" 200
check_status "API /trade-plans" "${API_BASE_URL}/trade-plans" 200
check_command_center_json "API /dashboard/command-center payload" "${API_BASE_URL}/dashboard/command-center"
if [[ "${STRICT_EXTERNAL_CHECKS}" == "true" ]]; then
  check_status "API /integrations/binance/testnet/ping" "${API_BASE_URL}/integrations/binance/testnet/ping" 200
else
  if ! check_status "API /integrations/binance/testnet/ping" "${API_BASE_URL}/integrations/binance/testnet/ping" 200; then
    echo "⚠️ Se omite fallo de testnet/ping por STRICT_EXTERNAL_CHECKS=false (dependencia externa Binance)."
  fi
fi

if [[ -n "${METRICS_API_KEY}" ]]; then
  check_status "API /metrics (auth)" "${API_BASE_URL}/metrics" 200 "x-metrics-key" "${METRICS_API_KEY}"
else
  metrics_tmpfile="$(mktemp)"
  trap 'rm -f "${metrics_tmpfile}"' EXIT
  metrics_status="$(curl "${CURL_OPTS[@]}" -o "${metrics_tmpfile}" -w "%{http_code}" "${API_BASE_URL}/metrics" || true)"
  case "${metrics_status}" in
    200)
      echo "✅ API /metrics (200 sin auth)"
      ;;
    401|403)
      echo "ℹ️ API /metrics requiere auth y no se recibió METRICS_API_KEY; se considera esperado (${metrics_status})."
      ;;
    *)
      echo "--- body ---"
      cat "${metrics_tmpfile}" || true
      echo "------------"
      echo "❌ API /metrics respondió estado inesperado (${metrics_status}) sin METRICS_API_KEY" >&2
      exit 1
      ;;
  esac
fi

web_home_body="$(fetch_body "WEB /" "${WEB_BASE_URL}/")"
check_body_contains "WEB /" "${web_home_body}" "bot"
check_body_contains "WEB command center" "${web_home_body}" "Detalle por trade plan"
check_body_contains "WEB command center" "${web_home_body}" "Historial de órdenes"
check_body_contains "WEB command center" "${web_home_body}" "Historial de posiciones"
check_body_contains "WEB command center" "${web_home_body}" "Historial de riesgo"
check_body_contains "WEB command center" "${web_home_body}" "Reconcile actual"
if [[ "${COMMAND_CENTER_CONTEXT_PRESENT}" == "true" ]]; then
  check_body_contains "WEB command center" "${web_home_body}" "context-list"
  check_body_contains "WEB command center" "${web_home_body}" "context-chip"
else
  echo "ℹ️ Se omiten marcadores context-list/context-chip porque el payload no trae contexto de riesgo no vacío."
fi

echo "✅ Smoke tests Synology completados"
