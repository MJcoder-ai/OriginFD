# Lifecycle Quickstart

## Seed the catalog

```bash
make api-seed-all
# or just one
make api-seed-project ID=<project-uuid>
```

## Get lifecycle (12 phases)

```bash
curl -s http://localhost:8000/projects/<PROJECT_ID>/lifecycle | jq .
```

## Approve a gate

```bash
curl -s -X POST http://localhost:8000/projects/<PROJECT_ID>/lifecycle/gate-approval \
  -H 'Content-Type: application/json' \
  -d '{
    "phase_code": 0,
    "gate_code": "G0",
    "decision": "APPROVE",
    "role_key": "role.project_manager",
    "comment": "baseline complete"
  }' | jq .
```

## Feature flag (agents)

```bash
export AGENTS_ENABLED=1  # emit agent hooks on approvals
```

## Run core tests

```bash
make api-test-core
```

\n## Windows (PowerShell)\n`powershell\npowershell -ExecutionPolicy Bypass -File scripts/api-prestart.ps1\npowershell -ExecutionPolicy Bypass -File scripts/api-seed-all.ps1\npowershell -ExecutionPolicy Bypass -File scripts/api-test-core.ps1\n`\n
