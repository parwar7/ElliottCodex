from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
RUNTIME_ROOT = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROTECTED_ROOT = Path(r"C:\ElliottCodex\Brain_LOCKED")
