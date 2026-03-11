#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="${COMPOSE_DIR:-${REPO_ROOT}/infra/docker/synology}"
ENV_FILE="${ENV_FILE:-${COMPOSE_DIR}/.env}"
REQUIRE_SECRETS="${REQUIRE_SECRETS:-false}"
AUTO_CREATE_DATA_DIRS="${AUTO_CREATE_DATA_DIRS:-false}"
SKIP_COMPOSE_VALIDATION="${SKIP_COMPOSE_VALIDATION:-false}"

# Variables de control del script (CLI/entorno de invocación). No deben ser sobreescritas por `source ${ENV_FILE}`.
CONTROL_COMPOSE_DIR="${COMPOSE_DIR}"
CONTROL_ENV_FILE="${ENV_FILE}"
CONTROL_REQUIRE_SECRETS="${REQUIRE_SECRETS}"
CONTROL_AUTO_CREATE_DATA_DIRS="${AUTO_CREATE_DATA_DIRS}"
CONTROL_SKIP_COMPOSE_VALIDATION="${SKIP_COMPOSE_VALIDATION}"

COMPOSE_CMD=()
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
fi

fail() {
  echo "❌ $1" >&2
  exit 1
}

warn() {
  echo "⚠️  $1" >&2
}

require_var() {
  local key="$1"
  local value="${!key:-}"
  if [[ -z "${value}" ]]; then
    fail "Falta variable requerida: ${key}"
  fi
}

load_env() {
  [[ -f "${ENV_FILE}" ]] || fail "No existe ENV_FILE: ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
}

echo "🚦 Synology preflight"
echo "COMPOSE_DIR=${COMPOSE_DIR}"
echo "ENV_FILE=${ENV_FILE}"

auto_dirs() {
  local auto_create_dirs_flag="$1"
  local data_root="${DATA_ROOT:-}"
  [[ -n "${data_root}" ]] || return 0
  if [[ "${auto_create_dirs_flag}" == "true" ]]; then
    mkdir -p "${data_root}/postgres" "${data_root}/redis"
    echo "✅ Directorios de datos asegurados en ${data_root}"
  fi
}

load_env

# Reaplicar variables de control para evitar que valores del `.env` alteren el comportamiento operativo del preflight.
COMPOSE_DIR="${CONTROL_COMPOSE_DIR}"
ENV_FILE="${CONTROL_ENV_FILE}"
REQUIRE_SECRETS="${CONTROL_REQUIRE_SECRETS}"
AUTO_CREATE_DATA_DIRS="${CONTROL_AUTO_CREATE_DATA_DIRS}"
SKIP_COMPOSE_VALIDATION="${CONTROL_SKIP_COMPOSE_VALIDATION}"

require_secrets_normalized="$(printf '%s' "${REQUIRE_SECRETS}" | tr '[:upper:]' '[:lower:]')"
skip_compose_validation_normalized="$(printf '%s' "${SKIP_COMPOSE_VALIDATION}" | tr '[:upper:]' '[:lower:]')"
auto_create_data_dirs_normalized="$(printf '%s' "${AUTO_CREATE_DATA_DIRS}" | tr '[:upper:]' '[:lower:]')"

echo "REQUIRE_SECRETS=${require_secrets_normalized} (raw=${REQUIRE_SECRETS})"
echo "SKIP_COMPOSE_VALIDATION=${skip_compose_validation_normalized} (raw=${SKIP_COMPOSE_VALIDATION})"
echo "AUTO_CREATE_DATA_DIRS=${auto_create_data_dirs_normalized} (raw=${AUTO_CREATE_DATA_DIRS})"

# Variables mínimas para levantar compose
for key in DATA_ROOT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD API_PORT WEB_PORT PAPER_TRADING API_BASE_URL; do
  require_var "${key}"
done

paper_trading_normalized="$(printf '%s' "${PAPER_TRADING}" | tr '[:upper:]' '[:lower:]')"
if [[ "${paper_trading_normalized}" != "true" ]]; then
  fail "PAPER_TRADING=${PAPER_TRADING}. Live trading no está autorizado en este gate. Establece PAPER_TRADING=true."
fi

if [[ -n "${OUTLINE_API_URL:-}" && -z "${OUTLINE_API_TOKEN:-}" && "${require_secrets_normalized}" != "true" ]]; then
  warn "OUTLINE_API_URL está definido pero OUTLINE_API_TOKEN está vacío."
fi

if [[ "${require_secrets_normalized}" == "true" ]]; then
  require_var BINANCE_API_KEY
  require_var BINANCE_API_SECRET
  require_var OUTLINE_API_TOKEN
fi

# Validación de compose
if [[ "${skip_compose_validation_normalized}" == "true" ]]; then
  warn "Se omite validación de compose por SKIP_COMPOSE_VALIDATION=true"
elif [[ ${#COMPOSE_CMD[@]} -eq 0 ]]; then
  fail "No se encontró docker compose (docker compose / docker-compose)"
else
  [[ -d "${COMPOSE_DIR}" ]] || fail "No existe COMPOSE_DIR: ${COMPOSE_DIR}"
  pushd "${COMPOSE_DIR}" >/dev/null
  "${COMPOSE_CMD[@]}" --env-file "${ENV_FILE}" config -q
  popd >/dev/null
fi

auto_dirs "${auto_create_data_dirs_normalized}"

echo "✅ Preflight Synology OK"
