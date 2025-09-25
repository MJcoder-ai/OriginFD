$ErrorActionPreference = "Stop"
if (-not $env:PYTHON) { $env:PYTHON = "python" }
& $env:PYTHON - <<'PYCODE'
from tools.paths import ensure_repo_on_path; ensure_repo_on_path()
from services.api.prestart import main
main()
print("prestart done")
PYCODE
