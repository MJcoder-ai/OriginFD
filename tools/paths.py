from __future__ import annotations

import sys
from pathlib import Path


def ensure_repo_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    candidates = [root, root / "services" / "api"]
    for candidate in candidates:
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
