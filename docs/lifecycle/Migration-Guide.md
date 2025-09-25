# Lifecycle Migration Guide

## Overview

The lifecycle service now persists gate states and approvals to the database via the
`lifecycle_phases`, `lifecycle_gates`, and `lifecycle_gate_approvals` tables. Legacy
snapshots (for example, JSON blobs cached on project documents or audit entries)
should be backfilled so that the new API surface serves consistent data to the UI and
reports.

## Backfill Script

`scripts/migrate_lifecycle_audit_to_orm.py` performs a one-off migration that maps any
legacy snapshot payloads into the normalized schema. Key details:

- Uses SQLAlchemy sessions supplied by `core.database.get_session_local()`.
- Normalises legacy gate statuses to the enum vocabulary:
  - `APPROVE` ? `APPROVED`
  - `REJECT` ? `REJECTED`
  - All other values are coerced into `NOT_STARTED`, `IN_PROGRESS`, or `BLOCKED`.
- Ensures only one `LifecycleGate` row exists per `(project_id, phase_code, gate_code)`.
- Synthesises a `LifecycleGateApproval` record when a migrated gate is terminal (`APPROVED`
  or `REJECTED`) and no matching approval already exists.

### Usage

```bash
# Dry run: prints JSON summary and rolls back changes
python scripts/migrate_lifecycle_audit_to_orm.py --dry-run

# Execute the migration (commit on success)
python scripts/migrate_lifecycle_audit_to_orm.py
```

The script prints a JSON payload with the number of projects processed and the
`inserted` / `updated` / `skipped` / `approvals` counters. Example:

```json
{
  "projects": 12,
  "inserted": 24,
  "updated": 6,
  "skipped": 42,
  "approvals": 18,
  "dry_run": false
}
```

### Customising snapshot discovery

The stubbed `iter_legacy_snapshots(session)` currently yields nothing. Wire it up to
your environment by querying the legacy storage location and yielding `(Project, snapshot_dict)`
for each record. The snapshot payload should align with the `LifecyclePhaseView` structure
(i.e. a dict containing a `"phases"` list with `phase_code`, `entry_gate_code`, `exit_gate_code`,
`gates`, etc.).

### Validation and rollback

1. Always run against a database snapshot or restore point first.
2. Inspect the JSON summary to confirm expected insert/update counts before committing.
3. If a rollback is required for a specific project, delete dependent rows in reverse order:
   ```sql
   DELETE FROM lifecycle_gate_approvals WHERE gate_id IN (
     SELECT id FROM lifecycle_gates WHERE project_id = :project_id
   );
   DELETE FROM lifecycle_gates WHERE project_id = :project_id;
   ```
   The catalog seeder will recreate empty gates on next access.

## Safety Checklist

- [ ] Execute `--dry-run` in a staging or backup environment and review output.
- [ ] Capture a database backup or snapshot prior to the live migration.
- [ ] Monitor logs for `Lifecycle backfill failed` entries; the script rolls back on exceptions.
- [ ] After migration, spot-check a handful of projects via `/projects/{id}/lifecycle` to verify gate
      statuses and approval history.

Following these steps keeps the database-backed lifecycle aligned with historical project
state while enabling the new UI and API flows.
