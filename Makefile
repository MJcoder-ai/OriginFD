.PHONY: api-seed-all api-seed-project api-test-core api-openapi api-prestart

# Seed catalog into ALL projects
api-seed-all:
	python -m services.api.seeders --all

# Seed catalog for a single project: make api-seed-project ID=<uuid>
api-seed-project:
	@if [ -z "$(ID)" ]; then echo "Usage: make api-seed-project ID=<uuid>"; exit 1; fi
	python -m services.api.seeders --project-id $(ID)

# Run core API tests (nocov config to avoid repo addopts)
api-test-core:
	python -m pytest -c tests/pytest.nocov.ini \
	  tests/api/lifecycle/test_catalog_shape.py \
	  tests/api/lifecycle/test_seeder.py \
	  tests/api/lifecycle/test_lifecycle_view.py \
	  tests/api/projects/test_lifecycle_contract.py \
	  tests/api/projects/test_lifecycle_edge_gates.py -q

# Dump OpenAPI (helpful for FE & docs)
api-openapi:
	python -c "from services.api.main import app; import json, sys; json.dump(app.openapi(), sys.stdout)"

# One-shot prestart hook (migrate + seed all)
api-prestart:
	python -m alembic upgrade head || true
	python -m services.api.seeders --all || true
