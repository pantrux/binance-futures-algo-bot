#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_PATH="${REPORT_PATH:-${REPO_ROOT}/artifacts/synology-release-gate.md}"

# Preflight env
COMPOSE_DIR="${COMPOSE_DIR:-${REPO_ROOT}/infra/docker/synology}"
ENV_FILE="${ENV_FILE:-${COMPOSE_DIR}/.env}"
REQUIRE_SECRETS="${REQUIRE_SECRETS:-false}"
AUTO_CREATE_DATA_DIRS="${AUTO_CREATE_DATA_DIRS:-false}"
SKIP_COMPOSE_VALIDATION="${SKIP_COMPOSE_VALIDATION:-false}"

# Smoke env
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
WEB_BASE_URL="${WEB_BASE_URL:-http://127.0.0.1:3000}"
METRICS_API_KEY="${METRICS_API_KEY:-}"
STRICT_EXTERNAL_CHECKS="${STRICT_EXTERNAL_CHECKS:-true}"

mkdir -p "$(dirname "${REPORT_PATH}")"

step_result() {
  local step_name="$1"
  local log_path="$2"
  local status="$3"
  local total_lines

  total_lines="$(wc -l < "${log_path}" | tr -d ' ')"

  {
    echo "## ${step_name}: ${status}"
    echo
    echo "\`\`\`text"
    sed -n '1,200p' "${log_path}"
    if [[ "${total_lines}" -gt 200 ]]; then
      echo "... [truncado: ${total_lines} líneas en total, mostrando primeras 200] ..."
    fi
    echo "\`\`\`"
    echo
  } >>"${REPORT_PATH}"
}

run_step() {
  local step_name="$1"
  shift
  local log_file
  log_file="$(mktemp)"

  if "$@" >"${log_file}" 2>&1; then
    step_result "${step_name}" "${log_file}" "PASS"
    rm -f "${log_file}"
    return 0
  fi

  step_result "${step_name}" "${log_file}" "FAIL"
  rm -f "${log_file}"
  return 1
}

{
  echo "# Synology Release Gate Report"
  echo
  echo "- Generated at (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
  echo "- API_BASE_URL: ${API_BASE_URL}"
  echo "- WEB_BASE_URL: ${WEB_BASE_URL}"
  echo "- ENV_FILE: ${ENV_FILE}"
  echo "- REQUIRE_SECRETS: ${REQUIRE_SECRETS}"
  echo "- STRICT_EXTERNAL_CHECKS: ${STRICT_EXTERNAL_CHECKS}"
  echo
} >"${REPORT_PATH}"

echo "🚦 Running Synology release gate"

overall_status="PASS"

if ! run_step "Preflight" env \
  COMPOSE_DIR="${COMPOSE_DIR}" \
  ENV_FILE="${ENV_FILE}" \
  REQUIRE_SECRETS="${REQUIRE_SECRETS}" \
  AUTO_CREATE_DATA_DIRS="${AUTO_CREATE_DATA_DIRS}" \
  SKIP_COMPOSE_VALIDATION="${SKIP_COMPOSE_VALIDATION}" \
  "${REPO_ROOT}/scripts/synology_preflight_check.sh"; then
  overall_status="FAIL"
  echo "⚠️  Preflight fallido — smoke omitido para evitar ruido diagnóstico." >>"${REPORT_PATH}"
else
  if ! run_step "Smoke" env \
    API_BASE_URL="${API_BASE_URL}" \
    WEB_BASE_URL="${WEB_BASE_URL}" \
    METRICS_API_KEY="${METRICS_API_KEY}" \
    STRICT_EXTERNAL_CHECKS="${STRICT_EXTERNAL_CHECKS}" \
    "${REPO_ROOT}/scripts/synology_smoke_test.sh"; then
    overall_status="FAIL"
  fi
fi

{
  echo "## Resultado global"
  echo
  echo "**${overall_status}**"
} >>"${REPORT_PATH}"

echo "📝 Report: ${REPORT_PATH}"

if [[ "${overall_status}" != "PASS" ]]; then
  echo "❌ Synology release gate failed"
  exit 1
fi

echo "✅ Synology release gate passed"
