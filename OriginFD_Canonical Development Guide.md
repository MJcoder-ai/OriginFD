# **OriginFD Canonical Development Guide** 

This is the **single source of truth** for how the OriginFD codebase is structured, how new features are added, and how the ODL-SD AI architecture and marketplace rules are enforced in code. It is opinionated and exhaustive so that humans and code-gen AIs produce **consistent** code with zero duplication.

**Context in one breath:**

* **Architecture spec:** ODL-SD v4.1 (document structure, lifecycle, JSON-Patch, data management).

* **AI system:** Planner/Router \+ Tool Registry \+ Policy Router (PSU budgets), RegionRouter, JSON-Patch contract.

* **RBAC & phase gates:** roles, rights, approvals, data classes.

* **Component libraries & CMS:** authoritative components \+ logistics, RFQ→PO→Ship→Install→RMA \+ media/QR.

* **Monetisation:** plans (Free/Pro/Enterprise), PSUs, marketplace fees, escrow triggers, provider-switch.

Deploy target: **Google Cloud Run** (GCP-first), repo: `github.com/MJcoder-ai/OriginFD.git`, domain: **originfd.com** (Cloud Run domain mapping).

---

# **0\) Monorepo layout (100% canonical tree)**

`originfd/`  
`├─ apps/`  
`│  ├─ web/                           # Next.js 14 (App Router), SSR, Edge-safe`  
`│  │  ├─ app/`  
`│  │  │  ├─ (marketing)/...`  
`│  │  │  ├─ (app)/dashboard/...`  
`│  │  │  ├─ api/bridge/[service]/route.ts      # thin BFF -> services/api`  
`│  │  │  └─ layout.tsx`  
`│  │  ├─ src/`  
`│  │  │  ├─ components/               # shadcn/ui + headless composites`  
`│  │  │  ├─ hooks/`  
`│  │  │  ├─ lib/odl/                  # TS types mirroring ODL-SD v4.1`  
`│  │  │  ├─ lib/rbac/                 # client-side guards (read-only)`  
`│  │  │  └─ styles/`  
`│  │  ├─ public/`  
`│  │  ├─ next.config.mjs`  
`│  │  └─ package.json`  
`│  ├─ mobile-tech/                    # React Native (Expo) – Field Tech app`  
`│  │  ├─ app/(tabs)/{work,scan,qc}/...`  
`│  │  ├─ src/features/workorders/`  
`│  │  ├─ src/lib/epcis.ts             # scan→EPCIS event upload (ship/install)`  
`│  │  └─ app.json`  
`│  ├─ mobile-customer/                # Customer app (status, quotes, ledger)`  
`│  │  └─ ...`  
`│  └─ mobile-logistics/               # Delivery & stock management`  
`│     └─ ...`  
`│`  
`├─ services/`  
`│  ├─ api/                            # FastAPI gateway (REST+Webhooks)`  
`│  │  ├─ main.py`  
`│  │  ├─ api/routers/{projects,docs,auth,marketplace}.py`  
`│  │  ├─ core/{config.py,security.py,db.py,rbac.py}`  
`│  │  ├─ domain_handlers/             # binds packages/domain logic to HTTP`  
`│  │  └─ alembic/                     # DB migrations`  
`│  ├─ orchestrator/                   # AI L1 Orchestrator (Planner/Router)`  
`│  │  ├─ main.py`  
`│  │  ├─ planner/{planner.py,critic.py,policy_router.py,region_router.py}`  
`│  │  ├─ tools/registry/              # JSON Schemas + adapters for tools`  
`│  │  ├─ memory/{cag_store.py,episodic.py,semantic.py}`  
`│  │  └─ workers/{celery.py,tasks.py}`  
`│  ├─ ingest/                         # Webhooks (payments, emails, 3rd parties)`  
`│  │  └─ main.py`  
`│  ├─ workers/                        # Celery/RQ worker pod (background jobs)`  
`│  │  ├─ celery_app.py`  
`│  │  ├─ tasks/{sim,doc_pack,epcis,emails}.py`  
`│  │  └─ schedules.py`  
`│  └─ exporter/                       # doc_pack, SLD exports, invoices, etc.`  
`│     └─ main.py`  
`│`  
`├─ domains/                           # PURE logic (no frameworks)`  
`│  ├─ pv/                             # PV sizing, strings, layouts`  
`│  ├─ bess/                           # BESS sizing, safety envelopes`  
`│  ├─ grid/                           # grid code checks, protection`  
`│  ├─ scada/                          # points, alarms, KPIs`  
`│  ├─ finance/                        # IRR/NPV/tariff models`  
`│  └─ commerce/                       # orders/escrow, handovers, payouts`  
`│`  
`├─ packages/`  
`│  ├─ py/                             # Python libs (poetry/uv)`  
`│  │  ├─ odl_sd_schema/               # pydantic models for ODL-SD v4.1`  
`│  │  ├─ odl_sd_rbac/                 # roles, phase gates, approver checks`  
`│  │  ├─ odl_sd_tools/                # tool I/O dataclasses & validation`  
`│  │  ├─ odl_sd_patch/                # JSON-Patch apply/validate/rollback`  
`│  │  ├─ graph_rag/                   # ODL-SD Graph-RAG projection`  
`│  │  ├─ ai_core/                     # ModelSelector, Guardrails, Tracing`  
`│  │  ├─ commerce_core/               # Plans/PSU metering, escrow logic`  
`│  │  └─ utils_common/`  
`│  └─ ts/                             # TypeScript shared packages (pnpm)`  
`│     ├─ ui/                          # shared React components (web/mobile)`  
`│     ├─ types-odl/                   # TS types generated from schemas`  
`│     └─ http-client/                 # typed client for services/api`  
`│`  
`├─ infra/`  
`│  ├─ gcp/terraform/                  # Cloud Run, Cloud SQL (Postgres), Pub/Sub,`  
`│  │  ├─ modules/{run,sql,artifact,secrets,workflows,memstore,lb,cdn}`  
`│  │  └─ envs/{dev,staging,prod}`  
`│  ├─ docker/                         # base images, multi-stage builds`  
`│  ├─ cloudbuild/                     # triggers for CI/CD deployments`  
`│  └─ k8s/                            # optional (GKE) manifests if needed later`  
`│`  
`├─ docs/`  
`│  ├─ adr/                            # architecture decision records`  
`│  ├─ api/openapi.yaml                # generated from FastAPI`  
`│  ├─ tools/schemas/                  # JSON Schemas (versioned, semver)`  
`│  ├─ governance/                     # RBAC tables, approver matrices`  
`│  └─ runbooks/                       # SLO/SLA, incident, red-team, DPA`  
`│`  
`├─ ops/`  
`│  ├─ workflows/                      # GitHub Actions, lint, test, deploy`  
`│  ├─ scripts/                        # one-shot ops tasks`  
`│  └─ observability/                  # dashboards, alerts, budgets`  
`│`  
`├─ examples/`  
`│  ├─ golden/odl_sd_docs/             # golden sample docs for tests & demos`  
`│  └─ patches/                        # safe patch examples & inverse patches`  
`│`  
`├─ .github/workflows/`  
`├─ pyproject.toml / poetry.lock (or uv.lock)`  
`├─ package.json / pnpm-workspace.yaml`  
`├─ turbo.json                         # monorepo tasks`  
`└─ README.md`

**Why this shape?**

* Keeps **apps** (web+mobile) thin; all heavy logic lives in **domains/** and **packages/**.

* AI **orchestrator** mirrors the reference layers (Planner/Router, Policy Router, Scheduler, tools).

* ODL-SD stays the **single source of truth**; all mutations are **JSON-Patch** based, validated, auditable.

---

# **1\) Core conventions**

* **Python:** 3.12; **FastAPI \+ SQLAlchemy 2 \+ Alembic**; **Celery** (Redis/MemoryStore) or **RQ** on Redis for simpler queues.

* **TypeScript:** Node 20; **pnpm** workspaces; **Next.js 14**; **Expo** for mobile.

* **DB:** Postgres (Cloud SQL) with row-level multi-tenancy (+ JSONB for ODL-SD docs).

* **Cache:** Redis (GCP MemoryStore) for sessions, CAG, ratelimits.

* **Message/Eventing:** Pub/Sub; EPCIS-style events for logistics.

* **Cloud:** GCP Cloud Run, Artifact Registry, Cloud Build, Secret Manager, Cloud SQL, Memorystore, Pub/Sub, Cloud Tasks/Workflows.

---

# **2\) Backend strategy (services/)**

## **2.1 API Gateway (FastAPI)**

**`services/api/main.py`**

`from fastapi import FastAPI, Depends, HTTPException, Request`  
`from pydantic import BaseModel`  
`from core.config import Settings, get_settings`  
`from core.security import require_scope, user_from_jwt`  
`from core.db import SessionDep`  
`from core.rbac import guard_patch`  
`from odl_sd_patch import apply_patch, inverse_patch`  
`from odl_sd_schema import OdlDocument, validate_document`

`app = FastAPI(title="OriginFD API")`

`@app.on_event("startup")`  
`async def _startup():`  
    `# warm caches, load tool registry, etc.`  
    `...`

`class PatchRequest(BaseModel):`  
    `doc_id: str`  
    `doc_version: int`  
    `patch: list[dict]  # RFC6902`  
    `evidence: list[str] = []`

`@app.post("/odl/patch")`  
`async def patch_doc(body: PatchRequest,`  
                    `db: SessionDep,`  
                    `user=Depends(user_from_jwt),`  
                    `settings: Settings = Depends(get_settings)):`  
    `# enforce RBAC + phase gates before any write`  
    `guard_patch(user=user, doc_id=body.doc_id, patch=body.patch, db=db)   # RBAC & approvals`  
    `doc: OdlDocument = OdlDocument.load(db, body.doc_id)`  
    `if doc.version != body.doc_version:`  
        `raise HTTPException(409, "version_conflict")`  
    `new_doc = apply_patch(doc, body.patch, evidence=body.evidence)`  
    `validate_document(new_doc)  # schema v4.1 validation`  
    `new_doc.save(db, actor=user)`  
    `return {"ok": True, "doc_version": new_doc.version, "inverse": inverse_patch(body.patch)}`

* **JSON-Patch** is the only write path; tool outputs are authoritative.

* The **guard** enforces RBAC (rights codes R/W/P/A/X/S), phase gates, approver roles.

**`core/rbac.py` (excerpt)**

`from odl_sd_rbac import has_rights, requires_approver, phase_gate_locked`

`def guard_patch(user, doc_id, patch, db):`  
    `if phase_gate_locked(doc_id, patch, db):`  
        `raise PermissionError("phase_gate_locked")`  
    `# deny library/compliance writes unless role has P/A/W per table`  
    `if not has_rights(user, doc_id, patch):`  
        `raise PermissionError("insufficient_rights")`  
    `if requires_approver(patch) and not user.has_any(["expert","project_manager","asset_owner","super_user"]):`  
        `raise PermissionError("approver_required")`

RBAC/phase-gate semantics are implemented from the **User & Access Structure** (mandatory MFA roles, scope inheritance, approvals).

## **2.2 Orchestrator (AI L1)**

**Layout:** `services/orchestrator/{planner,tools,memory,workers}` implements: Planner→ToolCaller→Critic/Verifier, **Policy Router** (PSU budgets by plan), **RegionRouter** for residency, **Scheduler**.

**`planner/planner.py`**

`from ai_core.model_selector import select_model`  
`from tools.registry import load_tool, ToolError`  
`from policy_router import enforce_psu_budget`  
`from graph_rag import ground_query`

`async def plan_and_execute(task):`  
    `evidence = await ground_query(task)         # Ground-Before-Generate`  
    `enforce_psu_budget(task.org_id, estimate=task.estimate)`  
    `model = select_model(task.kind, region=task.region)  # RegionRouter aware`  
    `plan = await model.propose_plan(task, evidence=evidence)`  
    `for step in plan.steps:`  
        `tool = load_tool(step.tool)`  
        `out = await tool.run(step.inputs)       # deterministic tool call`  
        `step.attach_output(out)`  
    `# Critic/Verifier gate can veto; only then emit JSON-Patches`  
    `return plan.to_patches()`

* Grounding via **Graph-RAG** of ODL-SD; tools are typed & versioned; **CAG store** caches prompts, embeddings, tool outputs.

* Policy Router enforces **PSU** budgets from plan/tenant subscription.

## **2.3 Workers (Celery/RQ)**

**`services/workers/celery.py`**

`from celery import Celery`  
`celery = Celery(__name__, broker="redis://redis:6379/0", backend="redis://redis:6379/1")`  
`celery.conf.beat_schedule = {"daily-reflection": {"task":"tasks.reflection.run", "schedule": 60*60*24}}`

**`tasks/sim.py`** binds to tool schemas (energy/finance/QC), producing typed outputs that become patches or attachments.

---

# **3\) Frontend strategy (apps/)**

* **web (Next.js):** SSR \+ RSC, BFF routes proxy to `services/api` only; never call databases directly.

* **mobile apps:** three Expo apps target (technician, customer, logistics). The tech app enforces **capture policies** (POD, install, QC/thermal) and privacy (face/house-number blur).

**Technician scan → EPCIS event (example)**

`// apps/mobile-tech/src/lib/epcis.ts`  
`export async function postEpcisEvent(ev: EPCISEvent) {`  
  `return fetch("/api/bridge/ingest", { method:"POST", body: JSON.stringify(ev) });`  
`}`  
`// Events: pickup, departed, arrived, delivered, install, service, etc.  (EPCIS 2.0)`

The required logistics and media capture steps and EPCIS fields are defined in the **Component Management Supplement** (shipments, SSCC, events) and the **Media/Symbols & Imaging** framework.

---

# **4\) Multi-domain pure logic (domains/)**

Each subfolder is **pure** (framework-free) functions \+ pydantic models:

* **pv/**: stringing, voltage-drop, SLD hints (uses component ports).

* **bess/**: SoC windows, thermal envelopes, UL9540A clearances.

* **grid/**: ride-through curves, protection coordination (IEEE 1547/2800, NERC PRC).

* **scada/**: KPIs (PR, availability, CF), alarm triage rules.

* **finance/**: IRR/NPV/tariff & incentives; regional climate loss adjustments.

* **commerce/**: orders/escrow, service handovers, disputes; provider-switch flow.

All of these operate on the ODL-SD doc object model (v4.1).

---

# **5\) Shared packages (packages/)**

## **5.1 `odl_sd_schema/` (Python)**

* **Purpose:** strongly-typed ODL-SD v4.1 models (Pydantic), JSON-Schema validation, helpers.

* **Also includes:** data-management helpers (partitioning, external refs, streaming).

## **5.2 `odl_sd_rbac/`**

Implements rights codes, phase gates, approvals, scopes for roles like engineer/expert/PM/tech operator, etc.

## **5.3 `odl_sd_tools/`**

Typed I/O schemas for tools (`validate_odl_sd`, `simulate_energy`, `simulate_finance`, `qc_rules`, `bom_sourcing`, `payments.create_quote`, `image_analyzer`, `web_incentives`, `esg_simulator`) with **`additionalProperties: false`**.

**Example tool adapter**

`class SimulateEnergyIn(BaseModel): ...  # from schema`  
`class SimulateEnergyOut(BaseModel): ...`  
`async def simulate_energy(inp: SimulateEnergyIn) -> SimulateEnergyOut:`  
    `# pure compute; no free-text writes`  
    `return SimulateEnergyOut(...)`

## **5.4 `odl_sd_patch/`**

Single entry for **RFC-6902 JSON-Patch** apply/validate \+ exact inverse generation and optimistic concurrency.

## **5.5 `graph_rag/`**

Builds the **ODL-SD graph projection** (hierarchy, libraries, instances, connections, finance, ops, esg) for grounding.

## **5.6 `commerce_core/`**

Implements plans (Free/Pro/Enterprise), **PSU metering**, fees (components, handovers), coupons/refunds, escrow triggers (e.g., **QR scan on site → release**).

## **5.7 `types-odl/` (TS)**

Generated TS types (OpenAPI \+ JSON Schemas) so web/mobile share the same contracts.

---

# **6\) Data & components**

* **Libraries:** Use the **unified component library** and **universal additions**; map ports and attributes for PV/BESS/GRID/SCADA across scales.

* **CMS:** Embed `component_management` on components (RFQ, bids, PO, shipments, inventory, warranty, returns, compliance).

* **Media & QR:** enforce capture policies & privacy; bind vectors (IEC symbols, SLD/Wiring SVG) into docs.

---

# **7\) Infra (GCP-first)**

* **Cloud Run** services: `originfd-api`, `originfd-orchestrator`, `originfd-workers`, `originfd-ingest`, `originfd-web`.

* **DB:** Cloud SQL (Postgres) \+ SQLAlchemy migrations.

* **Cache/Queues:** Memorystore (Redis), Pub/Sub; optional Cloud Tasks for scheduled flows.

* **CI/CD:** Cloud Build triggers on `main` → build (Docker) → deploy to Cloud Run; Artifact Registry per service.

* **Secrets:** Secret Manager (DB creds, JWT, vendor API keys).

* **Domain:** Cloud Run domain mapping → `www.originfd.com`, LB/CDN as needed.

* **Observability:** Cloud Logging, Error Reporting; budgets on PSUs & egress.

Terraform lives in `infra/gcp/terraform`, split by **modules** and **envs**.

---

# **8\) Security strategy**

* **RBAC & approvals** enforced on every patch; phase gates lock sections (e.g., libraries in commissioning).

* **Data classification** and **least-privilege** scopes per role; mandatory MFA for sensitive roles.

* **JSON-Patch audit** (append-only); SIEM webhooks; session recording with consent.

* **SCADA/OT cybersecurity** patterns (zones, DPI firewalls, data diodes, NERC CIP/IEC 62443).

* **Privacy in media**: auto-blur faces/house numbers; store raw in restricted tier; signed-URL redacted exports.

---

# **9\) AI architecture & tools (how we implement the blueprint)**

* **Planner/Router → ToolCaller → Critic/Verifier**: produce patches only after tool-verified evidence (**ground-before-generate**).

* **Policy Router**: per-plan **PSU** budgets (Pro includes 100 PSU/user/mo; Boost Pack adds 250), enforced before expensive steps.

* **RegionRouter**: route models/storage by **residency** (US/EU/APAC).

* **Tool Registry**: typed I/O for design/finance/ESG/marketplace/vision tools; each tool has `{name, semver, inputs, outputs, side_effects, rbac_scope}`.

**Registering a tool (`services/orchestrator/tools/registry/*.py`)**

`TOOL = {`  
  `"name": "simulate_finance@1.0.0",`  
  `"inputs_schema": "schemas/simulate_finance.input.json",`  
  `"outputs_schema": "schemas/simulate_finance.output.json",`  
  `"side_effects": "none",`  
  `"rbac_scope": ["finance_editor","financial_analyst"]`  
`}`

---

# **10\) Marketplace, billing, and governance (code hooks)**

* **Plans & billing:** model `Subscription`, `AIUsageMeter` and **fair-use** PSU accounting; upgrades prorate; trial rules.

* **Transactions:** components marketplace fee (5% supplier-paid), handover success fee (3% managing-company-paid), refunds/chargebacks with audit evidence.

* **Escrow milestones** bound to **governance events** (e.g., QR scan on site, commissioning started).

* **Right-to-Switch** managing company while retaining warranty ledger & history.

---

# **11\) Critical code patterns (copy these)**

## **11.1 SQLAlchemy session & RLS**

`from sqlalchemy import create_engine`  
`from sqlalchemy.orm import sessionmaker`  
`engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)`  
`SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)`

`def db_session(tenant_id: str):`  
    `db = SessionLocal()`  
    `db.execute("SET app.current_tenant = :tid", {"tid": tenant_id})`  
    `try:`  
        `yield db`  
    `finally:`  
        `db.close()`

## **11.2 Celery task calling a tool**

`@celery.task(name="tasks.energy.run")`  
`def run_energy(doc_id: str, scope: str, period: dict):`  
    `from odl_sd_tools.energy import SimulateEnergyIn, SimulateEnergyOut`  
    `inp = SimulateEnergyIn(doc_id=doc_id, scope=scope, period=period, granularity="hourly")`  
    `out: SimulateEnergyOut = simulate_energy(inp)`  
    `return out.model_dump()`

## **11.3 Frontend patch helper (BFF)**

`export async function applyPatch(docId: string, version: number, patch: any[]) {`  
  `const res = await fetch("/api/bridge/api/odl/patch", {`  
    `method: "POST", headers: {"content-type":"application/json"},`  
    `body: JSON.stringify({doc_id: docId, doc_version: version, patch})`  
  `});`  
  `if (!res.ok) throw new Error(await res.text());`  
  `return res.json();`  
`}`

---

# **12\) Developer & code-gen AI rules (must follow)**

1. **Where to put code:**

   * UI: `apps/web/src/components/*` or `apps/mobile-*/src/*`.

   * HTTP only in `services/api/.../routers/*`.

   * Business logic **only** in `domains/*` or `packages/py/*`.

   * AI steps and schemas live in `services/orchestrator` and `packages/py/odl_sd_tools`.

2. **Never write directly** to ODL-SD docs; emit **JSON-Patches** only, validated & audited.

3. **RBAC check** every mutation; block when phase-gated.

4. **Use existing components** from library; if adding hardware, include `component_management` and required compliance & tracking.

5. **Logistics media:** follow capture policy types (POD, nameplate, thermal) and privacy rules.

6. **Billing & PSUs:** call `commerce_core.policy_router.enforce()` before heavy compute.

7. **Tool I/O:** Keep `additionalProperties:false`; bump **semver** on breaking changes.

8. **Docs first:** extend `docs/adr/*` and JSON Schemas before code.

9. **No duplication:** search repository first; extend existing module or open ADR if a new module is warranted.

10. **Commits/PRs:** scope by folder; include schema changes and migration; CI must pass (lint, type, unit, contract).

---

# **13\) Ready-to-run: local \+ CI**

* **Local:** `docker compose up` → `services/api`, `orchestrator`, `workers`, `web`.

* **Migrations:** `alembic upgrade head`.

* **Tests:** `pytest -q`, `pnpm -w test`.

* **CI:** GitHub Actions → Cloud Build → Cloud Run (staging) → promo to prod on tag.

---

# **14\) Appendix — sample JSONs & links you’ll see in code**

* **ODL-SD v4.1 document structure** and lifecycle sections used by validators and editors.

* **Data management** knobs (partitioning, external refs, streaming) used by `odl_sd_schema`.

* **Component examples** (PV modules, inverters, BESS racks, trackers), across **residential → hyperscale**.

* **Universal additions (1-100)** used in logistics/SCADA and mechanical BoS.

---

## **Final note**

This guide encodes the **architecture canon** (ODL-SD v4.1 \+ the AI Blueprint) into folder structure, code patterns, and enforcement points so that everything remains **contract-first** (schemas → tools → patches). When in doubt, align code to the referenced specs here (they are the law).   

