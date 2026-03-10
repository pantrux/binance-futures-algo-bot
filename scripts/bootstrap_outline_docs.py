from pathlib import Path
import requests

OUTLINE_URL = "http://192.168.0.8:3005/api"
OUTLINE_TOKEN = ""
COLLECTION_ID = "24c679b7-7739-4f6b-b0f2-71c02f20bfcb"
BASE_DIR = Path(__file__).resolve().parents[1] / "docs"

FILES = [
    BASE_DIR / "plans" / "implementation-roadmap.md",
    BASE_DIR / "adr" / "ADR-001-stack-base.md",
    BASE_DIR / "adr" / "ADR-002-risk-engine.md",
    BASE_DIR / "adr" / "ADR-003-outline-as-source-of-truth.md",
    BASE_DIR / "diagrams" / "architecture.md",
    BASE_DIR / "diagrams" / "risk-flow.md",
]


def upload_document(path: Path) -> None:
    title = path.stem.replace("-", " ").replace("ADR ", "ADR-")
    text = path.read_text(encoding="utf-8")
    response = requests.post(
        f"{OUTLINE_URL}/documents.create",
        headers={"Authorization": f"Bearer {OUTLINE_TOKEN}"},
        json={"title": title, "text": text, "collectionId": COLLECTION_ID, "publish": True},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    print(f"✅ {path.name}: {payload.get('data', {}).get('url', 'creado')}")


if __name__ == "__main__":
    if not OUTLINE_TOKEN:
        raise SystemExit("Configura OUTLINE_TOKEN antes de ejecutar el bootstrap")
    for file in FILES:
        upload_document(file)
