# Lifecycle Testing Matrix

The table below captures the 12 lifecycle phases, their entry/exit gates, and the
required role keys as defined in the catalog-backed lifecycle (`services/api/domain/lifecycle_catalog.py`).
All gates map `APPROVE` decisions to the persisted status `APPROVED` and `REJECT`
decisions to `REJECTED`.

| Phase (code)                    | Entry Gate (required roles)                       | Exit Gate (required roles)                        | `APPROVE` ? | `REJECT` ? | Notes                                                                            |
| ------------------------------- | ------------------------------------------------- | ------------------------------------------------- | ----------- | ---------- | -------------------------------------------------------------------------------- |
| Discovery & Qualification (0)   | G0 � `role.project_manager`, `role.exec.sponsor`  | G1 � `role.project_manager`, `role.engineer.lead` | `APPROVED`  | `REJECTED` | Edge-case gate: G0 �Qualified� approval is covered by API E2E tests.             |
| Concept & Feasibility (1)       | G1 � `role.project_manager`, `role.engineer.lead` | G2 � `role.engineer.lead`, `role.finops`          | `APPROVED`  | `REJECTED` | �                                                                                |
| Requirements & Scope (2)        | G2 � `role.project_manager`, `role.engineer.lead` | G3 � `role.project_manager`, `role.compliance`    | `APPROVED`  | `REJECTED` | �                                                                                |
| Preliminary Design (3)          | G3 � `role.engineer.lead`, `role.project_manager` | G4 � `role.engineer.lead`, `role.qa`              | `APPROVED`  | `REJECTED` | �                                                                                |
| Detailed Design (4)             | G4 � `role.engineer.lead`, `role.qa`              | G5 � `role.engineer.lead`, `role.compliance`      | `APPROVED`  | `REJECTED` | �                                                                                |
| Procurement Planning (5)        | G5 � `role.project_manager`, `role.finops`        | G6 � `role.procurement`, `role.finops`            | `APPROVED`  | `REJECTED` | �                                                                                |
| Supplier Selection & POs (6)    | G6 � `role.procurement`, `role.finops`            | G7 � `role.procurement`, `role.project_manager`   | `APPROVED`  | `REJECTED` | �                                                                                |
| Construction & Installation (7) | G7 � `role.construction`, `role.project_manager`  | G8 � `role.construction`, `role.qa`               | `APPROVED`  | `REJECTED` | �                                                                                |
| QA/QC & Pre-Commission (8)      | G8 � `role.qa`, `role.construction`               | G9 � `role.qa`, `role.compliance`                 | `APPROVED`  | `REJECTED` | �                                                                                |
| Commissioning & Handover (9)    | G9 � `role.qa`, `role.compliance`                 | G10 � `role.handover`, `role.operations`          | `APPROVED`  | `REJECTED` | Edge-case gate: G9 �Handover� exit path validated via idempotent approval tests. |
| Operations & Optimization (10)  | G10 � `role.operations`, `role.project_manager`   | G11 � `role.operations`, `role.exec.sponsor`      | `APPROVED`  | `REJECTED` | Edge-case gate: G10 �Closed� exit rejection path covered by API E2E tests.       |
| Closeout (11)                   | G11 � `role.operations`, `role.project_manager`   | G12 � `role.exec.sponsor`, `role.project_manager` | `APPROVED`  | `REJECTED` | �                                                                                |

**Status legend:**

- `APPROVE` decisions persist the gate as `APPROVED` and append a `LifecycleGateApproval` record.
- `REJECT` decisions persist the gate as `REJECTED` with an accompanying approval record.
- Any other legacy status encountered during migration is normalised to one of the
  five gate states (`NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `APPROVED`, `REJECTED`).
