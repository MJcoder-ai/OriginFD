if (-not $env:PYTHON) { $env:PYTHON = "python" }
& $env:PYTHON -m pytest -c tests/pytest.nocov.ini \
  tests/api/lifecycle/test_catalog_shape.py \
  tests/api/lifecycle/test_seeder.py \
  tests/api/lifecycle/test_lifecycle_view.py \
  tests/api/projects/test_lifecycle_contract.py \
  tests/api/projects/test_lifecycle_edge_gates.py -q
