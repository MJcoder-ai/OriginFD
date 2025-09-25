# Frontend Lifecycle Contract

## View Models

### GateView

- `key`: stable identifier for the gate (useful for rendering lists).
- `name`: display label for the gate ("Entry" or "Exit" for the DB-backed model).
- `gate_code`: lifecycle code returned by the API; send this back in approval payloads.
- `status`: gate state (`NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `APPROVED`, `REJECTED`).

### LifecyclePhaseView

- `phase_code`: zero-based numeric code (0�11) for the lifecycle phase.
- `phase_key`: string identifier (e.g. `phase.discovery`).
- `title`: human readable title for the phase.
- `order`: numeric sort key; render phases in ascending order.
- `entry_gate_code` / `exit_gate_code`: gate codes for the start and exit checks.
- `required_entry_roles` / `required_exit_roles`: lifecycle role keys required to approve each gate.
- `odl_sd_sections`: list of ODL/SD reference sections to link (`/docs/odl/<section>`).
- `name`: legacy name (fallback for older payloads).
- `status`: legacy phase status string (do not derive gate state from this field).
- `gates`: array of exactly two `GateView` records (entry first, exit second).

## Approval Payload

Send approvals with the following shape:

```
{
  "phase_code": number,
  "gate_code": string,
  "decision": "APPROVE" | "REJECT",
  "role_key": string,
  "comment"?: string
}
```

Example:

```
{
  "phase_code": 3,
  "gate_code": "G3E",
  "decision": "APPROVE",
  "role_key": "role.project_manager",
  "comment": "Design checklist complete"
}
```

On success the API returns the refreshed `LifecyclePhaseView[]` payload which should replace local state.

## Status Vocabulary

- `APPROVE` decisions update the target gate status to `APPROVED`.
- `REJECT` decisions update the target gate status to `REJECTED`.
- Backend may also return `NOT_STARTED`, `IN_PROGRESS`, or `BLOCKED` for gates that are pending.

## Backward Compatibility Notes

- Older API responses may surface only `name`, `status`, and generic gate details. The client should continue to render those values when `gates` are missing or incomplete.
- The `status` field on the phase is retained for display but should not be used to infer gate outcomes.
- When `NEXT_PUBLIC_LIFECYCLE_V2` is disabled the UI falls back to a summary card view while still consuming the v2 payload shape.
