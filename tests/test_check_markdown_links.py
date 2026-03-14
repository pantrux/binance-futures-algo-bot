from pathlib import Path

from scripts.check_markdown_links import collect_links_from_text, validate_markdown_file


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "markdown-links"


def test_collect_links_from_text_ignores_fenced_code_and_escaped_links() -> None:
    text = """Ver [roadmap](./roadmap.md)\n\n```md\n[falso](./broken.md)\n```\n\nEscapado: \\[literal](./skip.md)\n"""

    links = collect_links_from_text(text)

    assert [(link.href, link.line_number) for link in links] == [("./roadmap.md", 1)]



def test_validate_markdown_file_reports_missing_local_targets() -> None:
    source = FIXTURE_ROOT / "broken.md"

    links_checked, issues = validate_markdown_file(source)

    assert links_checked == 2
    assert len(issues) == 1
    assert issues[0].href == "./missing.md"
    assert "destino inexistente" in issues[0].reason



def test_validate_markdown_file_accepts_existing_targets() -> None:
    source = FIXTURE_ROOT / "valid.md"

    links_checked, issues = validate_markdown_file(source)

    assert links_checked == 2
    assert issues == []



def test_validate_markdown_file_counts_unresolvable_targets() -> None:
    source = FIXTURE_ROOT / "unresolvable.md"

    links_checked, issues = validate_markdown_file(source)

    assert links_checked == 1
    assert len(issues) == 1
    assert issues[0].href == "../../../../outside.md"
    assert issues[0].reason == "no se pudo resolver dentro del repo"
