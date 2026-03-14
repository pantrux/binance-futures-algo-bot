from pathlib import Path

from scripts.sync_outline_docs import (
    is_markdown_escaped,
    parent_document_needs_update,
    rewrite_local_links,
)


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


def test_rewrite_local_links_rewrites_after_even_number_of_backslashes() -> None:
    text = "Escapado literal: \\\\[roadmap](./implementation-roadmap.md)"

    rewritten = rewrite_local_links(text, DOC_PATH, OUTLINE_URLS, REPO_WEB_BASE)

    assert rewritten == "Escapado literal: \\\\[roadmap](https://outline.example.com/doc/implementation-roadmap)"


def test_is_markdown_escaped_counts_consecutive_backslashes() -> None:
    assert is_markdown_escaped("\\[roadmap]", 1) is True
    assert is_markdown_escaped("\\\\[roadmap]", 2) is False


def test_parent_document_needs_update_only_when_field_is_present() -> None:
    assert parent_document_needs_update({}, "hub-1") is False
    assert parent_document_needs_update({"parentDocumentId": "hub-1"}, "hub-1") is False
    assert parent_document_needs_update({"parentDocumentId": "hub-old"}, "hub-1") is True
