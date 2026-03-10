import sys
from pathlib import Path

# pytest (importlib mode) no garantiza que el root del repo esté en sys.path.
# Para que imports tipo `apps.api...` funcionen de forma consistente:
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
