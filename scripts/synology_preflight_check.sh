#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="${COMPOSE_DIR:-${REPO_ROOT}/infra/docker/synology}"
ENV_FILE="${ENV_FILE:-${COMPOSE_DIR}/.env}"
REQUIRE_SECRETS="${REQUIRE_SECRETS:-false}"
AUTO_CREATE_DATA_DIRS="${AUTO_CREATE_DATA_DIRS:-false}"
SKIP_COMPOSE_VALIDATION="${SKIP_COMPOSE_VALIDATION:-false}"

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
echo "REQUIRE_SECRETS=${REQUIRE_SECRETS}"
echo "SKIP_COMPOSE_VALIDATION=${SKIP_COMPOSE_VALIDATION}"

auto_dirs() {
  local data_root="${DATA_ROOT:-}"
  [[ -n "${data_root}" ]] || return 0
  if [[ "${AUTO_CREATE_DATA_DIRS}" == "true" ]]; then
    mkdir -p "${data_root}/postgres" "${data_root}/redis"
    echo "✅ Directorios de datos asegurados en ${data_root}"
  fi
}

load_env

# Variables mínimas para levantar compose
for key in DATA_ROOT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD API_PORT WEB_PORT PAPER_TRADING API_BASE_URL; do
  require_var "${key}"
done

if [[ "${PAPER_TRADING}" != "true" ]]; then
  warn "PAPER_TRADING=${PAPER_TRADING}. Recuerda que live trading no está autorizado en este gate."
fi

if [[ -n "${OUTLINE_API_URL:-}" && -z "${OUTLINE_API_TOKEN:-}" ]]; then
  warn "OUTLINE_API_URL está definido pero OUTLINE_API_TOKEN está vacío."
fi

if [[ "${REQUIRE_SECRETS}" == "true" ]]; then
  require_var BINANCE_API_KEY
  require_var BINANCE_API_SECRET
  require_var OUTLINE_API_TOKEN
fi

auto_dirs

# Validación de compose
if [[ "${SKIP_COMPOSE_VALIDATION}" == "true" ]]; then
  warn "Se omite validación de compose por SKIP_COMPOSE_VALIDATION=true"
elif [[ ${#COMPOSE_CMD[@]} -eq 0 ]]; then
  fail "No se encontró docker compose (docker compose / docker-compose)"
else
  pushd "${COMPOSE_DIR}" >/dev/null
  "${COMPOSE_CMD[@]}" --env-file "${ENV_FILE}" config -q
  popd >/dev/null
fi

echo "✅ Preflight Synology OK"
