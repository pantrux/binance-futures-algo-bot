SHELL := /bin/bash

ENV_FILE ?= infra/docker/synology/.env
COMPOSE_DIR ?= infra/docker/synology
API_BASE_URL ?= http://127.0.0.1:8000
WEB_BASE_URL ?= http://127.0.0.1:3000
METRICS_API_KEY ?=
STRICT_EXTERNAL_CHECKS ?= true
REQUIRE_SECRETS ?= false
SKIP_COMPOSE_VALIDATION ?= false
AUTO_CREATE_DATA_DIRS ?= false
REPORT_PATH ?= artifacts/synology-release-gate.md
EXPECTED_STEPS ?= Preflight,Smoke
JSON_PATH ?= artifacts/synology-release-gate.json
CHECKLIST_PATH ?= artifacts/synology-release-checklist.md
PACKAGE_PATH ?= artifacts/synology-signoff-package.md
RETENTION_REPORT_PATH ?= artifacts-retention/synology-artifact-retention.json
ARTIFACTS_DIR ?= artifacts
KEEP_DAYS ?= 45
RETENTION_DRY_RUN ?= true
OPS_OBSERVABILITY_JSON_PATH ?= artifacts/synology-operational-observability.json
OPS_OBSERVABILITY_MD_PATH ?= artifacts/synology-operational-observability.md
OPS_WINDOW_HOURS ?= 168
OPS_MIN_SUCCESS_RATE ?= 0.90
OPS_MIN_RUNS ?= 1
OPS_REPO ?= pantrux/binance-futures-algo-bot
OPS_WORKFLOWS ?= Synology Release Gate,Synology Smoke Test,Synology Preflight,Synology Artifact Retention
OPS_DRIFT_WORKFLOWS ?= Synology Artifact Retention
OPS_HEALTH_API_URL ?=
OPS_HEALTH_WEB_URL ?=
RESILIENCE_BACKUP_OUTPUT_DIR ?= artifacts-resilience
RESILIENCE_BACKUP_PATHS ?= infra/docker/synology/docker-compose.yml,infra/docker/synology/.env.example,Makefile,docs/plans/synology-runbook.md
RESILIENCE_RTO_MINUTES ?= 60
RESILIENCE_RPO_MINUTES ?= 1440
RESILIENCE_VERIFY_RESTORE ?= true
RELEASE_REF ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)
SIGNOFF_OWNER ?= pending
SIGNOFF_NOTES ?=
PYTHON ?= python3

.PHONY: help synology-preflight synology-smoke synology-release-gate synology-release-summary synology-release-verify synology-release-checklist synology-signoff-package synology-signoff-all synology-artifact-retention synology-operational-observability synology-resilience-backup

help:
	@echo "Targets disponibles:"
	@echo "  make synology-preflight      # valida .env + compose config"
	@echo "  make synology-smoke          # smoke funcional API/Web"
	@echo "  make synology-release-gate   # preflight + smoke + reporte markdown"
	@echo "  make synology-release-summary # genera resumen JSON desde markdown"
	@echo "  make synology-release-verify # valida estructura del JSON del gate"
	@echo "  make synology-release-checklist # genera checklist Markdown de aprobación"
	@echo "  make synology-signoff-package # consolida evidencia final de sign-off"
	@echo "  make synology-signoff-all # ejecuta gate + summary + verify + checklist + package"
	@echo "  make synology-artifact-retention # aplica política de retención de artifacts (30/60/90 etc)"
	@echo "  make synology-operational-observability # calcula SLO/alertas del pipeline Synology"
	@echo "  make synology-resilience-backup # genera backup verificable de configuración crítica"

synology-preflight:
	ENV_FILE="$(ENV_FILE)" \
	COMPOSE_DIR="$(COMPOSE_DIR)" \
	REQUIRE_SECRETS="$(REQUIRE_SECRETS)" \
	SKIP_COMPOSE_VALIDATION="$(SKIP_COMPOSE_VALIDATION)" \
	AUTO_CREATE_DATA_DIRS="$(AUTO_CREATE_DATA_DIRS)" \
	./scripts/synology_preflight_check.sh

synology-smoke:
	API_BASE_URL="$(API_BASE_URL)" \
	WEB_BASE_URL="$(WEB_BASE_URL)" \
	METRICS_API_KEY="$(METRICS_API_KEY)" \
	STRICT_EXTERNAL_CHECKS="$(STRICT_EXTERNAL_CHECKS)" \
	./scripts/synology_smoke_test.sh

synology-release-gate:
	ENV_FILE="$(ENV_FILE)" \
	COMPOSE_DIR="$(COMPOSE_DIR)" \
	REQUIRE_SECRETS="$(REQUIRE_SECRETS)" \
	SKIP_COMPOSE_VALIDATION="$(SKIP_COMPOSE_VALIDATION)" \
	AUTO_CREATE_DATA_DIRS="$(AUTO_CREATE_DATA_DIRS)" \
	API_BASE_URL="$(API_BASE_URL)" \
	WEB_BASE_URL="$(WEB_BASE_URL)" \
	METRICS_API_KEY="$(METRICS_API_KEY)" \
	STRICT_EXTERNAL_CHECKS="$(STRICT_EXTERNAL_CHECKS)" \
	REPORT_PATH="$(REPORT_PATH)" \
	./scripts/synology_release_gate.sh

synology-release-summary:
	$(PYTHON) scripts/synology_release_gate_summary.py \
		"$(REPORT_PATH)" \
		"$(JSON_PATH)"

synology-release-verify:
	$(PYTHON) scripts/synology_release_gate_verify.py \
		"$(JSON_PATH)" \
		"$(EXPECTED_STEPS)"

synology-release-checklist:
	API_BASE_URL="$(API_BASE_URL)" \
	WEB_BASE_URL="$(WEB_BASE_URL)" \
	ENV_FILE="$(ENV_FILE)" \
	STRICT_EXTERNAL_CHECKS="$(STRICT_EXTERNAL_CHECKS)" \
	REQUIRE_SECRETS="$(REQUIRE_SECRETS)" \
	RELEASE_REF="$(RELEASE_REF)" \
	SIGNOFF_OWNER="$(SIGNOFF_OWNER)" \
	SIGNOFF_NOTES="$(SIGNOFF_NOTES)" \
	$(PYTHON) scripts/synology_release_checklist.py \
		"$(CHECKLIST_PATH)"

synology-signoff-package:
	$(PYTHON) scripts/synology_signoff_package.py \
		"$(REPORT_PATH)" \
		"$(JSON_PATH)" \
		"$(CHECKLIST_PATH)" \
		"$(PACKAGE_PATH)"

synology-signoff-all: synology-release-gate synology-release-summary synology-release-verify synology-release-checklist synology-signoff-package
	@echo "✅ Sign-off pipeline completado"

synology-artifact-retention:
	@set -euo pipefail; \
	DRY_RUN_NORMALIZED="$$(echo "$(RETENTION_DRY_RUN)" | tr '[:upper:]' '[:lower:]')"; \
	if [[ "$$DRY_RUN_NORMALIZED" != "true" && "$$DRY_RUN_NORMALIZED" != "false" ]]; then \
		echo "❌ RETENTION_DRY_RUN debe ser 'true' o 'false' (recibido: '$(RETENTION_DRY_RUN)')"; \
		exit 1; \
	fi; \
	EXTRA_FLAG=""; \
	if [[ "$$DRY_RUN_NORMALIZED" == "true" ]]; then EXTRA_FLAG="--dry-run"; fi; \
	$(PYTHON) scripts/synology_artifact_retention.py \
		--artifacts-dir "$(ARTIFACTS_DIR)" \
		--keep-days "$(KEEP_DAYS)" \
		--report-path "$(RETENTION_REPORT_PATH)" \
		$$EXTRA_FLAG

synology-operational-observability:
	@set -euo pipefail; \
	ARGS=( \
		--repo "$(OPS_REPO)" \
		--workflows "$(OPS_WORKFLOWS)" \
		--drift-workflows "$(OPS_DRIFT_WORKFLOWS)" \
		--window-hours "$(OPS_WINDOW_HOURS)" \
		--min-success-rate "$(OPS_MIN_SUCCESS_RATE)" \
		--min-runs "$(OPS_MIN_RUNS)" \
		--output-json "$(OPS_OBSERVABILITY_JSON_PATH)" \
		--output-md "$(OPS_OBSERVABILITY_MD_PATH)" \
	); \
	if [[ -n "$(OPS_HEALTH_API_URL)" ]]; then ARGS+=(--health-check "api=$(OPS_HEALTH_API_URL)"); fi; \
	if [[ -n "$(OPS_HEALTH_WEB_URL)" ]]; then ARGS+=(--health-check "web=$(OPS_HEALTH_WEB_URL)"); fi; \
	$(PYTHON) scripts/synology_operational_observability.py "$${ARGS[@]}"

synology-resilience-backup:
	@set -euo pipefail; \
	VERIFY_FLAG=""; \
	VERIFY_NORMALIZED="$$(echo "$(RESILIENCE_VERIFY_RESTORE)" | tr '[:upper:]' '[:lower:]')"; \
	if [[ "$$VERIFY_NORMALIZED" == "true" ]]; then VERIFY_FLAG="--verify-restore"; fi; \
	$(PYTHON) scripts/synology_resilience_backup.py \
		--repo-root "." \
		--paths "$(RESILIENCE_BACKUP_PATHS)" \
		--output-dir "$(RESILIENCE_BACKUP_OUTPUT_DIR)" \
		--rto-minutes "$(RESILIENCE_RTO_MINUTES)" \
		--rpo-minutes "$(RESILIENCE_RPO_MINUTES)" \
		$$VERIFY_FLAG
