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
RELEASE_REF ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)
PYTHON ?= python3

.PHONY: help synology-preflight synology-smoke synology-release-gate synology-release-summary synology-release-verify synology-release-checklist

help:
	@echo "Targets disponibles:"
	@echo "  make synology-preflight      # valida .env + compose config"
	@echo "  make synology-smoke          # smoke funcional API/Web"
	@echo "  make synology-release-gate   # preflight + smoke + reporte markdown"
	@echo "  make synology-release-summary # genera resumen JSON desde markdown"
	@echo "  make synology-release-verify # valida estructura del JSON del gate"
	@echo "  make synology-release-checklist # genera checklist Markdown de aprobación"

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
	$(PYTHON) scripts/synology_release_checklist.py \
		"$(CHECKLIST_PATH)"
