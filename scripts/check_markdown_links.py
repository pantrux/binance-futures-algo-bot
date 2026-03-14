#!/usr/bin/env python3
"""Valida links Markdown locales para evitar referencias rotas antes del sync a Outline.

Chequea `README.md` y `docs/**/*.md`.
Ignora links externos, anchors internos y contenido dentro de fenced code blocks.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sync_outline_docs import (
    BACKTICK_RUN_RE,
    FENCE_RE,
    is_markdown_escaped,
    parse_markdown_link_at,
    resolve_repo_relative_path,
    split_markdown_link_target,
)

DEFAULT_TARGETS = (REPO_ROOT / "README.md", REPO_ROOT / "docs")


@dataclass
class LinkIssue:
    source_path: Path
    line_number: int
    href: str
    reason: str


@dataclass
class LinkCheckResult:
    files_checked: int
    links_checked: int
    issues: List[LinkIssue]


@dataclass
class LinkOccurrence:
    href: str
    line_number: int



def iter_markdown_files(targets: Iterable[Path]) -> Iterable[Path]:
    for target in targets:
        if target.is_file() and target.suffix == ".md":
            yield target
            continue
        if target.is_dir():
            yield from sorted(path for path in target.rglob("*.md") if path.is_file())



def collect_links_from_line(line: str, line_number: int) -> List[LinkOccurrence]:
    links: List[LinkOccurrence] = []
    cursor = 0
    while cursor < len(line):
        if is_markdown_escaped(line, cursor) and line.startswith("![", cursor):
            cursor += 2
            continue
        if is_markdown_escaped(line, cursor) and line[cursor] == "[":
            cursor += 1
            continue

        link = None
        if line.startswith("![", cursor) or line[cursor] == "[":
            link = parse_markdown_link_at(line, cursor)
        if link:
            _, end, _, _, raw_target = link
            href, _ = split_markdown_link_target(raw_target)
            if href and not href.startswith("#"):
                links.append(LinkOccurrence(href=href, line_number=line_number))
            cursor = end
            continue

        opener = BACKTICK_RUN_RE.search(line, cursor)
        if opener and opener.start() == cursor:
            run = opener.group(0)
            closer_end = None
            for candidate in BACKTICK_RUN_RE.finditer(line, opener.end()):
                if candidate.group(0) == run:
                    closer_end = candidate.end()
                    break
            if closer_end is None:
                break
            cursor = closer_end
            continue

        next_positions = [len(line)]
        if opener:
            next_positions.append(opener.start())
        next_link_positions = [
            pos for pos in (line.find("![", cursor + 1), line.find("[", cursor + 1)) if pos != -1
        ]
        next_positions.extend(next_link_positions)
        next_stop = min(next_positions)
        if next_stop == len(line):
            break
        cursor = next_stop

    return links



def collect_links_from_text(text: str) -> List[LinkOccurrence]:
    in_fenced_code = False
    fence_char = ""
    fence_len = 0
    links: List[LinkOccurrence] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        fence_match = FENCE_RE.match(stripped)
        if fence_match:
            fence = fence_match.group(1)
            if not in_fenced_code:
                in_fenced_code = True
                fence_char = fence[0]
                fence_len = len(fence)
            elif fence[0] == fence_char and len(fence) >= fence_len:
                in_fenced_code = False
                fence_char = ""
                fence_len = 0
            continue
        if in_fenced_code:
            continue
        links.extend(collect_links_from_line(line, line_number))

    return links



def validate_markdown_file(path: Path) -> tuple[int, List[LinkIssue]]:
    text = path.read_text(encoding="utf-8")
    issues: List[LinkIssue] = []
    links_checked = 0

    for occurrence in collect_links_from_text(text):
        href = occurrence.href
        if href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
            continue

        rel_path, _ = resolve_repo_relative_path(path, href)
        links_checked += 1
        if not rel_path:
            issues.append(LinkIssue(path, occurrence.line_number, href, "no se pudo resolver dentro del repo"))
            continue

        resolved_path = REPO_ROOT / rel_path
        if not resolved_path.exists():
            issues.append(LinkIssue(path, occurrence.line_number, href, f"destino inexistente: {rel_path}"))

    return links_checked, issues



def run(targets: Iterable[Path]) -> LinkCheckResult:
    files_checked = 0
    links_checked = 0
    issues: List[LinkIssue] = []

    for path in iter_markdown_files(targets):
        files_checked += 1
        file_links_checked, file_issues = validate_markdown_file(path)
        links_checked += file_links_checked
        issues.extend(file_issues)

    return LinkCheckResult(files_checked=files_checked, links_checked=links_checked, issues=issues)



def main() -> int:
    targets = [Path(arg).resolve() for arg in sys.argv[1:]] if len(sys.argv) > 1 else list(DEFAULT_TARGETS)
    result = run(targets)

    print(f"files_checked={result.files_checked}")
    print(f"links_checked={result.links_checked}")
    print(f"issues_found={len(result.issues)}")

    if result.issues:
        for issue in result.issues:
            rel_source = issue.source_path.relative_to(REPO_ROOT).as_posix()
            print(f"{rel_source}:{issue.line_number}: {issue.reason} -> {issue.href}")
        return 1

    print("status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
