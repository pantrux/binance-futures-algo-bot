#!/usr/bin/env python3
"""Sync de documentación del proyecto hacia Outline sin duplicados.

Uso:
  OUTLINE_API_TOKEN=... python3 scripts/sync_outline_docs.py
  OUTLINE_API_TOKEN=... python3 scripts/sync_outline_docs.py --archive-unknown

Comportamiento adicional:
  - reescribe links locales/relativos a URLs navegables de Outline cuando el documento existe allí
  - usa fallback a la URL web del repo (`blob/<ref>`) para archivos versionados sin equivalente en Outline
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib import parse, request

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"

PREFIX = "Trading Bot Binance Futures"
DEFAULT_OUTLINE_URL = os.getenv("OUTLINE_API_URL", "http://192.168.0.8:3005/api")
DEFAULT_COLLECTION_ID = os.getenv("OUTLINE_COLLECTION_ID", "24c679b7-7739-4f6b-b0f2-71c02f20bfcb")
DEFAULT_GIT_REF = os.getenv("OUTLINE_GIT_REF", "main")
DEFAULT_REPO_WEB_BASE = os.getenv("OUTLINE_REPO_WEB_BASE", "")

ROOT_TITLE = f"{PREFIX} — Índice maestro"
HUB_TITLES = {
    "roadmaps": f"{PREFIX} — 01 Roadmaps y planes",
    "ops": f"{PREFIX} — 02 Operación y despliegue",
    "adrs": f"{PREFIX} — 03 ADRs",
    "diagrams": f"{PREFIX} — 04 Diagramas y flujos",
}

NON_ADR_TITLE_MAP = {
    "docs/plans/master-plan.md": f"{PREFIX} — Plan maestro",
    "docs/plans/implementation-roadmap.md": f"{PREFIX} — Roadmap de implementación",
    "docs/plans/phase5-operational-closure.md": f"{PREFIX} — Cierre operativo Fase 5",
    "docs/plans/market-ingestion-phase.md": f"{PREFIX} — Fase ingesta inicial de mercado",
    "docs/plans/market-ingestion-hardening-phase.md": f"{PREFIX} — Fase hardening de ingesta",
    "docs/plans/technical-indicators-phase.md": f"{PREFIX} — Fase indicadores técnicos base",
    "docs/plans/signal-features-phase.md": f"{PREFIX} — Fase señales y feature engineering inicial",
    "docs/plans/domain-expansion-phase.md": f"{PREFIX} — Fase expansión del dominio operativo",
    "docs/plans/data-model-and-testnet-phase.md": f"{PREFIX} — Fase persistencia y Binance Testnet",
    "docs/plans/synology-deployment.md": f"{PREFIX} — Plan de despliegue Synology",
    "docs/plans/synology-runbook.md": f"{PREFIX} — Runbook Synology",
    "docs/pr-plan/PR_ROADMAP.md": f"{PREFIX} — Roadmap formal de PRs",
    "docs/pr-plan/PR_TEMPLATE_CHECKLIST.md": f"{PREFIX} — Checklist estándar de PR",
    "docs/diagrams/architecture.md": f"{PREFIX} — Diagrama de arquitectura",
    "docs/diagrams/synology-topology.md": f"{PREFIX} — Topología Synology-first",
    "docs/diagrams/risk-flow.md": f"{PREFIX} — Flujo de riesgo",
    "docs/diagrams/market-ingestion-flow.md": f"{PREFIX} — Flujo de ingesta de mercado",
    "docs/diagrams/trade-plan-lifecycle.md": f"{PREFIX} — Ciclo de vida de un trade plan",
    "docs/diagrams/paper-trading-flow.md": f"{PREFIX} — Flujo de paper trading",
    "docs/diagrams/demo-loop-flow.md": f"{PREFIX} — Flujo demo loop",
}

MARKDOWN_LINK_RE = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:")


@dataclass
class TargetDoc:
    rel_path: str
    title: str
    category: str


class OutlineClient:
    def __init__(self, base_url: str, token: str, collection_id: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.collection_id = collection_id

    def call(self, endpoint: str, payload: dict) -> dict:
        req = request.Request(
            f"{self.base_url}/{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=40) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def list_collection_docs(self) -> List[dict]:
        docs: List[dict] = []
        offset = 0
        limit = 100
        while True:
            chunk = self.call(
                "documents.list",
                {"collectionId": self.collection_id, "limit": limit, "offset": offset},
            ).get("data", [])
            docs.extend(chunk)
            if len(chunk) < limit:
                break
            offset += limit
        return docs

    def info(self, doc_id: str) -> dict:
        return self.call("documents.info", {"id": doc_id}).get("data", {})

    def get_text(self, doc_id: str) -> str:
        return self.info(doc_id).get("text", "")

    def update(self, doc_id: str, title: str, text: str, parent_id: str | None = None) -> None:
        payload = {"id": doc_id, "title": title, "text": text, "publish": True}
        if parent_id is not None:
            payload["parentDocumentId"] = parent_id
        self.call("documents.update", payload)

    def create(self, title: str, text: str, parent_id: str | None = None) -> str:
        payload = {
            "title": title,
            "text": text,
            "publish": True,
            "collectionId": self.collection_id,
        }
        if parent_id is not None:
            payload["parentDocumentId"] = parent_id
        doc_id = self.call("documents.create", payload).get("data", {}).get("id")
        if not doc_id:
            raise RuntimeError(f"documents.create no devolvió id para '{title}'")
        return doc_id

    def archive(self, doc_id: str) -> None:
        self.call("documents.archive", {"id": doc_id})


def parse_iso(ts: str | None) -> datetime:
    if not ts:
        return datetime.min.replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def derive_adr_title(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    first = lines[0].lstrip("# ").strip() if lines else path.stem
    if not first:
        first = path.stem
    return f"{PREFIX} — {first}"


def collect_targets() -> List[TargetDoc]:
    targets: List[TargetDoc] = []

    for rel_path, title in NON_ADR_TITLE_MAP.items():
        category = "roadmaps"
        if rel_path.startswith("docs/diagrams/"):
            category = "diagrams"
        if rel_path in {"docs/plans/synology-deployment.md", "docs/plans/synology-runbook.md"}:
            category = "ops"
        targets.append(TargetDoc(rel_path=rel_path, title=title, category=category))

    for adr_file in sorted((DOCS_ROOT / "adr").glob("ADR-*.md")):
        rel = str(adr_file.relative_to(REPO_ROOT))
        targets.append(TargetDoc(rel_path=rel, title=derive_adr_title(adr_file), category="adrs"))

    return targets


def detect_repo_web_base() -> str:
    if DEFAULT_REPO_WEB_BASE:
        return DEFAULT_REPO_WEB_BASE.rstrip("/")

    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception as exc:  # pragma: no cover - fallback defensivo
        raise RuntimeError("No se pudo detectar remote.origin.url para generar links web") from exc

    if remote.startswith("git@github.com:"):
        repo_path = remote.split(":", 1)[1]
    elif remote.startswith("https://github.com/"):
        repo_path = remote.split("https://github.com/", 1)[1]
    elif remote.startswith("http://github.com/"):
        repo_path = remote.split("http://github.com/", 1)[1]
    else:
        raise RuntimeError(f"Remote no soportado para links web: {remote}")

    if repo_path.endswith(".git"):
        repo_path = repo_path[:-4]

    return f"https://github.com/{repo_path}/blob/{DEFAULT_GIT_REF}"


def resolve_repo_relative_path(source_path: Path, href: str) -> tuple[str | None, str]:
    target, sep, anchor = href.partition("#")
    suffix = f"#{anchor}" if sep else ""

    if not target or target.startswith("#"):
        return None, suffix
    if target.startswith(EXTERNAL_SCHEMES):
        return None, suffix

    if target.startswith("file://"):
        parsed = parse.urlparse(target)
        candidate = Path(parse.unquote(parsed.path))
    elif target.startswith("/"):
        candidate = Path(target)
    elif target.startswith("docs/") or target.startswith("scripts/") or target.startswith("README"):
        candidate = REPO_ROOT / target
    else:
        candidate = source_path.parent / target

    try:
        rel_path = candidate.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return None, suffix

    return rel_path, suffix


def rewrite_local_links(text: str, source_path: Path, outline_urls: Dict[str, str], repo_web_base: str) -> str:
    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        href = match.group(2).strip()
        rel_path, anchor = resolve_repo_relative_path(source_path, href)
        if not rel_path:
            return match.group(0)

        if rel_path in outline_urls:
            return f"{label}({outline_urls[rel_path]}{anchor})"

        return f"{label}({repo_web_base}/{rel_path}{anchor})"

    return MARKDOWN_LINK_RE.sub(replace, text)


def ensure_single_doc(client: OutlineClient, docs: List[dict], title: str, text: str, parent_id: str | None = None) -> str:
    same = [d for d in docs if d.get("title") == title and d.get("archivedAt") is None]
    if same:
        canonical = sorted(same, key=lambda d: parse_iso(d.get("createdAt")))[0]
        client.update(canonical["id"], title, text, parent_id=parent_id)
        for extra in same:
            if extra["id"] != canonical["id"]:
                client.archive(extra["id"])
        return canonical["id"]

    new_id = client.create(title, text, parent_id=parent_id)
    docs.append({"id": new_id, "title": title, "archivedAt": None, "createdAt": None, "updatedAt": None})
    return new_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline-url", default=DEFAULT_OUTLINE_URL)
    parser.add_argument("--collection-id", default=DEFAULT_COLLECTION_ID)
    parser.add_argument("--token", default=os.getenv("OUTLINE_API_TOKEN", ""))
    parser.add_argument("--archive-unknown", action="store_true")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Falta token: define OUTLINE_API_TOKEN o usa --token")

    client = OutlineClient(args.outline_url, args.token, args.collection_id)
    targets = collect_targets()
    repo_web_base = detect_repo_web_base()

    # Paso 1: dedupe exacto previo por título en todo el prefijo del proyecto
    all_docs = client.list_collection_docs()
    active_project = [
        d for d in all_docs if (d.get("title", "").startswith(PREFIX) and d.get("archivedAt") is None)
    ]
    grouped = defaultdict(list)
    for d in active_project:
        grouped[d["title"]].append(d)

    deduped = 0
    for title, items in grouped.items():
        if len(items) <= 1:
            continue
        canonical = sorted(items, key=lambda d: parse_iso(d.get("createdAt")))[0]
        newest = max(items, key=lambda d: parse_iso(d.get("updatedAt")))
        latest_text = client.get_text(newest["id"])
        client.update(canonical["id"], title, latest_text)
        for extra in items:
            if extra["id"] != canonical["id"]:
                client.archive(extra["id"])
                deduped += 1

    all_docs = client.list_collection_docs()

    # Paso 2: crear índice + hubs
    root_id = ensure_single_doc(client, all_docs, ROOT_TITLE, "# Índice maestro\n")

    hub_ids: Dict[str, str] = {}
    for key, title in HUB_TITLES.items():
        hub_ids[key] = ensure_single_doc(client, all_docs, title, f"# {title.split(' — ', 1)[1]}\n", parent_id=root_id)

    # Paso 3: upsert inicial de targets para garantizar existencia/URL
    synced = 0
    desired_titles = {ROOT_TITLE, *HUB_TITLES.values()}

    for t in targets:
        path = REPO_ROOT / t.rel_path
        if not path.exists():
            print(f"[WARN] Archivo no encontrado, se omite: {t.rel_path}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        desired_titles.add(t.title)
        ensure_single_doc(client, all_docs, t.title, text, parent_id=hub_ids[t.category])
        synced += 1

    # Paso 4: segunda pasada para reescribir links locales a Outline/GitHub
    all_docs = client.list_collection_docs()
    outline_urls_by_title = {
        d.get("title"): d.get("url", "")
        for d in all_docs
        if d.get("archivedAt") is None and d.get("title")
    }
    outline_urls_by_rel = {
        t.rel_path: outline_urls_by_title.get(t.title, "")
        for t in targets
        if outline_urls_by_title.get(t.title)
    }

    for t in targets:
        path = REPO_ROOT / t.rel_path
        if not path.exists():
            continue
        raw_text = path.read_text(encoding="utf-8")
        rewritten = rewrite_local_links(raw_text, path, outline_urls_by_rel, repo_web_base)
        ensure_single_doc(client, all_docs, t.title, rewritten, parent_id=hub_ids[t.category])

    # Paso 5: opción de limpiar documentos legacy no mapeados
    archived_unknown = 0
    if args.archive_unknown:
        for d in client.list_collection_docs():
            title = d.get("title", "")
            if not title.startswith(PREFIX):
                continue
            if d.get("archivedAt") is not None:
                continue
            if title not in desired_titles:
                client.archive(d["id"])
                archived_unknown += 1

    # Paso 6: regenerar índices de hubs y root
    docs = [
        d
        for d in client.list_collection_docs()
        if d.get("title", "").startswith(PREFIX) and d.get("archivedAt") is None
    ]
    by_parent = defaultdict(list)
    by_id = {d["id"]: d for d in docs}
    for d in docs:
        by_parent[d.get("parentDocumentId")].append(d)

    def lines(parent_id: str) -> str:
        items = sorted(
            [d for d in by_parent[parent_id] if d["id"] != parent_id], key=lambda x: x["title"]
        )
        if not items:
            return "- (sin documentos)"
        return "\n".join(f"- [{d['title']}]({d.get('url', '')})" for d in items)

    def hub_url(key: str) -> str:
        hub = by_id.get(hub_ids[key])
        return hub.get("url", "") if hub else ""

    client.update(hub_ids["roadmaps"], HUB_TITLES["roadmaps"], "# Roadmaps y planes\n\n" + lines(hub_ids["roadmaps"]))
    client.update(hub_ids["ops"], HUB_TITLES["ops"], "# Operación y despliegue\n\n" + lines(hub_ids["ops"]))
    client.update(hub_ids["adrs"], HUB_TITLES["adrs"], "# ADRs\n\n" + lines(hub_ids["adrs"]))
    client.update(hub_ids["diagrams"], HUB_TITLES["diagrams"], "# Diagramas y flujos\n\n" + lines(hub_ids["diagrams"]))

    root_text = "\n".join(
        [
            "# Índice maestro",
            "",
            "Documentación oficial activa, ordenada por categoría:",
            "",
            f"- [{HUB_TITLES['roadmaps']}]({hub_url('roadmaps')})",
            f"- [{HUB_TITLES['ops']}]({hub_url('ops')})",
            f"- [{HUB_TITLES['adrs']}]({hub_url('adrs')})",
            f"- [{HUB_TITLES['diagrams']}]({hub_url('diagrams')})",
        ]
    )
    client.update(root_id, ROOT_TITLE, root_text)

    print(f"docs_synced={synced}")
    print(f"duplicates_archived={deduped}")
    print(f"unknown_archived={archived_unknown}")
    print(f"root={root_id}")


if __name__ == "__main__":
    main()
