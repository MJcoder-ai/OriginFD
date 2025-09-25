if (-not $env:PYTHON) { $env:PYTHON = "python" }
& $env:PYTHON - <<'PYCODE'
from tools.paths import ensure_repo_on_path; ensure_repo_on_path()
import sys
from services.api.seeders.__main__ import main
sys.argv = ["seed", "--all"]
main()
PYCODE
