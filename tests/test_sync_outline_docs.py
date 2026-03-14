from pathlib import Path

from scripts.sync_outline_docs import rewrite_local_links


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "plans" / "master-plan.md"
OUTLINE_URLS = {
    "docs/plans/implementation-roadmap.md": "https://outline.example.com/doc/implementation-roadmap",
    "docs/diagrams/architecture.md": "https://outline.example.com/doc/architecture",
}
REPO_WEB_BASE = "https://github.com/pantrux/binance-futures-algo-bot/blob/main"


def test_rewrite_local_links_preserves_escaped_markdown_links() -> None:
    text = r"Literal: \[roadmap](./implementation-roadmap.md)"

    rewritten = rewrite_local_links(text, DOC_PATH, OUTLINE_URLS, REPO_WEB_BASE)

    assert rewritten == text


def test_rewrite_local_links_preserves_escaped_markdown_images() -> None:
    text = r"Literal image: \![arquitectura](../diagrams/architecture.md)"

    rewritten = rewrite_local_links(text, DOC_PATH, OUTLINE_URLS, REPO_WEB_BASE)

    assert rewritten == text


def test_rewrite_local_links_still_rewrites_real_markdown_links() -> None:
    text = "Ver roadmap: [roadmap](./implementation-roadmap.md)"

    rewritten = rewrite_local_links(text, DOC_PATH, OUTLINE_URLS, REPO_WEB_BASE)

    assert rewritten == "Ver roadmap: [roadmap](https://outline.example.com/doc/implementation-roadmap)"
