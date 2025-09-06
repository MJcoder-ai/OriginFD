# ODL‑SD AI Architecture – Enterprise Blueprint v1.1 (Unified Master)

> **Status:** Canonical master. This document supersedes prior canvases (v1.0 and v1.1 draft). It merges the full **enterprise AI architecture** and the **Tool I/O JSON Schemas** into a single, authoritative source for strategy, design, development, governance, and operations.

---

## 0) Executive Summary
**Business outcomes (targets):**
- **↓ Cost & Latency:** CAG hit rate ≥ 70%; p95 latency ≤ 2 s for grounded answers; avg query cost < $0.01.
- **↑ Throughput & Accuracy:** grounded‑answer rate ≥ 95%; hallucination < 5% (tool‑verified); proposal cycle time −50%.
- **↑ Revenue:** 30% of AI‑assisted designs convert to orders; +15% upsell/attach (BESS, service packs); CAC payback ≤ 3 months via AI lead gen.
- **↑ Adoption & Trust:** AI NPS ≥ 8/10; 99% uptime for simulations; transparent Planner Trace UI.

**Key risks & mitigations:**
- *Hallucination / unsafe actions* → Ground‑before‑Generate, deterministic tools, Critic/Verifier gate, RBAC phase gates, JSON‑Patch dry‑run.
- *Cache staleness* → DriftDetector + web validation; TTLs + event‑invalidations; versioned tools & cache keys.
- *Privacy/compliance* → Region routing, role‑scoped content, media privacy filters, PII scrubber in memory writes.
- *Runaway costs* → Policy router per plan (PSU budgets), model swaps (quality/cost curves), CAG‑first.

---

## 1) Core Principles (contract‑first)
1. **ODL‑SD Single Source of Truth.** One JSON per project (versioned). All AI I/O validated against schemas; **mutations via JSON‑Patch** only.
2. **Guarded Autonomy.** Agents plan→act within RBAC; approver gates; critical merges require signatures and audit reasons.
3. **Ground‑Before‑Generate (multimodal).** Evidence from ODL‑SD **Graph‑RAG**, hybrid text retrieval, and visual tools (datasheets/photos/videos) precedes generation.
4. **Deterministic Tools > Free Text.** Models plan and select tools; tools compute/verify/comply; models explain diffs and choices.
5. **CAG‑First Efficiency.** Cache prompts, embeddings, tool outputs, sims with event‑driven invalidation and drift checks.
6. **Lifecycle Coverage.** Concept → Design → Procurement → Construction → Commissioning → Operations → Maintenance/Warranty → Upgrades → Finance/Commercial → Decommissioning/ESG.
7. **Proactive & Revenue‑Driven.** Scheduler for autonomous jobs (lead gen, dynamic pricing, cohort analyses) tied to monetisation KPIs.
8. **Observability by Design.** Traces, evaluations, costs; user‑visible Planner Trace panel for transparency.

---

## 2) Reference Architecture (layers)
**L0 Channels.** Chat/Voice/UI; Webhooks & APIs; WhatsApp/Email/Sheets/Docs/VoIP connectors.

**L1 Orchestrator.** Planner/Router → Tool Caller → Critic/Verifier → **Policy Router** (plan limits, PSU) → **Scheduler** (cron & event jobs) → **Reflection loop** (online low‑risk + offline batch).
- **ModelSelector.** Routes by task (reasoning vs extraction vs vision) and region (data residency/cost).
- **RegionRouter.** US/EU/APAC splitting for models and storage.
- **Handover protocol.** Shared scratchpad + plan cards between agents (Design → Sales → Sourcing → Ops).

**L2 Reasoning & Memory.** Scratchpad; episodic memory (sessions/events); semantic memory (curated notes); **distilled best‑practices** corpus with PII scrubber.

**L3 Grounding.** Hybrid Retriever (vector + lexical + structured) + **Graph‑RAG projection of ODL‑SD** (hierarchy, libraries, instances, connections, finance, ops, esg). Event‑triggered reprojection after patches.

**L4 Caching.** **CAG** store for prompts, embeddings, tool outputs, sims; **CacheValidator/DriftDetector** refreshing incentives/prices.

**L5 Tools & Connectors.** Registry of typed, versioned tools (design validation, wiring, finance, sourcing/RFQ, marketplace/escrow, ESG, OCR, image QA, incentives/standards, lead gen, email/send, Sheets sync, VoIP).

**L6 Data & Governance.** ODL‑SD store (JSONB + object storage); sharded/regional graphs; event log; audit; SIEM hooks; RBAC & phase gates; SLA monitors.

**External xAI subtree.** x‑semantic lead search, market news, supplier trend mining; gated via Policy Router & rate limits.

---

## 3) JSON‑Patch Mutation Contract (safe‑write rules)
**Atomicity & scale.**
- Max **100 ops per patch**; batch larger ops. Server applies as **single transaction**; rollback on failure.
- Patches carry `intent`, `tool_version`, `dry_run`, and `evidence[]` (URIs to datasheets, photos, test reports).

**Rollback.** `generate_inverse_patch` tool returns an exact inverse for any committed patch.

**Proof.** Media‑driven changes include evidence URIs + capture context (geo/timestamp/device), auto‑redacted.

**Optimistic concurrency.** `doc_version` check; auto‑rebase or request user intervention on conflict.

---

## 4) Tool Registry (core + growth)
**Design & Compliance.** `schema_validate`, `auto_layout`, `auto_route`, `wire_check`, `short_circuit`, `protection_coordination`, `code_check` (NEC/IEC/IEEE), `sld_generate`, `doc_pack`.

**Finance.** `baseline_finance`, `sensitivity`, `monte_carlo`, `tariff_model`, `incentive_fetch`, `price_index`, `fx_hedge`.

**Sourcing & Logistics.** `rfq_issue`, `bid_score`, `award_po`, `waybill_label`, `epcis_event`, `inventory_update`, `warranty_claim`, `rma_process`.

**Multimodal.** `parse_datasheet_pdf`, `image_qc`, `nameplate_ocr`, `thermal_anomaly_detect`, `symbol_extractor`, `map_roof_segmenter`.

**Growth/Revenue.** `upsell_recommender` (design deltas → IRR lift), `dynamic_pricing_sim`, `x_lead_gen` (semantic leads), `cohort_insights`, `referral_scoring`.

**Safety & Ops.** `fault_tree`, `alarm_triage`, `crew_schedule`, `workorder_generate`, `site_checklist`, `commissioning_runner`.

**Governance.** `change_request_open`, `publish_design`, `merge_change`, `export_package`; Right‑to‑Switch; escrow triggers.

**Versioning.** Every tool has `{name, semver, inputs, outputs, side_effects, rbac_scope}`; version bumps auto‑invalidate caches and enable A/B guards.

---

## 5) Agents (minimal, revenue‑aligned)
- **DesignEngineerAgent** — validates/mutates ODL‑SD; proposes patches; suggests cost/IRR improvements.
- **SalesAdvisorAgent** — quotes/ROI, incentives, proposals; coordinates with upsell recommender.
- **SourcingGrowthAgent** — BOM→RFQ/bids/alternates; shipping & EPCIS; inventory.
- **OpsSustainabilityAgent** — commissioning, monitoring, warranty, ESG reports/credits.
- **MarketingCRMAgent (core)** — autonomous daily lead scan, nurture sequences, referral prompts (consent‑gated).
- **RevenueOptimizerAgent (core)** — dynamic pricing tiers, Boost Pack nudges, marketplace strategy; cohort observation.
- **ReflectionAgent** — weekly batch + low‑risk online learning; distills playbooks; updates retrieval corpus and prompts (no direct design writes).

**Scheduler.** Declarative cron/events per agent (e.g., daily `x_lead_gen`; on `rfq_awarded` plan logistics).

---

## 6) Security, RBAC & Governance (enterprise)
- Roles & scopes across phases: design/procurement/build/commission/operate/maintain/decommission.
- Data classification: public/internal/restricted/confidential; least‑privilege; MFA for sensitive roles.
- SIEM webhooks; append‑only audit; session recording with consent; media governance & redaction.

---

## 7) Observability, Evals & SLAs
- **Traces:** per tool call (timing, cost, cache hit/miss, redaction hash, validators).
- **Evals:** grounded‑answer checks, wiring limits satisfied, finance deltas vs baseline, hallucination counters.
- **AI SLAs:** latency, uptime, time‑to‑first‑plan, PSU budgets; regional latency targets; error budgets per tool.
- **Guard budgets:** per‑org PSU, per‑agent compute, per‑day xAI calls; adaptive backoff with UI nudges.

---

## 8) Planner Trace UI (what users see)
- **Plan cards:** decomposition with *why*; each step shows (tool, inputs, outputs, scope, cost estimate).
- **Critic panel:** blockers & fixes, severity triage.
- **Executor timeline:** tool status ticks; cache hits; rollbacks.
- **Explain & Audit:** JSON‑Patch diff view; evidence links; deterministic “Reproduce” button.

---

## 9) Channels & Connectors
Inbound: Chat (web), WhatsApp, Email, Google Forms/Sheets, CSV, VoIP IVR.  
Outbound: Emails/WhatsApp, Sheets sync, CRM updates, webhooks to ERP/PSCAD/IFC.  
Maps & Canvas: roof segmentation, geo‑anchors, **auto‑layout** & **auto‑route** with DRC.

---

## 10) Monetisation AI — hybrid separation with tight integration
- Monetisation subsystem runs **MarketingCRMAgent** + **RevenueOptimizerAgent**; owns payments/escrow; isolated scopes (PCI/PII).
- Operational AI publishes anonymised events (lead quality, conversion, PSU usage) enabling revenue optimisation without cross‑contamination.

---

## 11) Implementation Roadmap (100 days)
**Phase 0 (Weeks 1–2): Foundations & risk checks.**  
Schemas, Patch pipeline, RBAC, audit, SIEM, Tool Registry (7 core), privacy/residency audit, golden samples.

**Phase 1 (Weeks 3–6): MVP grounding & agents.**  
Graph‑RAG projection; DesignEngineerAgent + SalesAdvisorAgent; CAG store; Planner Trace v1.

**Phase 2 (Weeks 7–10): Sourcing & Ops.**  
RFQ→PO→EPCIS; OpsSustainabilityAgent; media governance; autoroute/auto‑layout beta.

**Phase 3 (Weeks 11–14): Growth.**  
MarketingCRMAgent + RevenueOptimizerAgent; Scheduler; xAI lead gen; A/B model swaps; NPS loops.

**Phase 4 (Weeks 15–16): Hardening.**  
Observability dashboards; AI SLAs; red‑team; cost/latency tuning; cohort reporting.

---

## 12) Lifecycle Playbooks — 10 Examples at Each Stage (A→J)
> Format: **Trigger → AI Plan (agent/tools) → ODL‑SD Patch/Output → KPI/Outcome**

### A) Intake & Concept (ideation, scoping)
1) Size 5 kW PV for CA, 70% bill offset → Planner→DesignEngineer (tariff_model, baseline_finance) → add `requirements` + draft `instances` → draft in 90 s.
2) Upload utility bill PDF → parse_datasheet_pdf (tables) → `finance.inputs.tariff` update → baseline error < 2%.
3) Homeowner sketches roof → map_roof_segmenter → `physical.surfaces[]` + constraints → viable area + tilt.
4) Ask: Grid‑tie + backup? → SalesAdvisor (scenario_compare) → propose hybrid + gateway → +12% IRR.
5) Limit budget to $20k → Planner optimises panels/inverter → BOM/finance patch → meets budget.
6) Minimise embodied carbon → esg_optimizer → low‑CO₂ modules → ESG badge on proposal.
7) Off‑grid 2 days autonomy → storage_sizer → BESS/racking spec → autonomy proven.
8) Multi‑unit complex → portfolio template → clones per unit with overrides.
9) Import HelioScope layout → external_models mapping → merged `instances`/`connections`.
10) Fire lanes for permitting → code_check → keep‑outs in `physical.zones` → compliant layout.

### B) System Design & Layout (electrical/mechanical)
1) Auto‑stringing → auto_route + wire_check → `connections[]` DC strings, Vdrop ≤ 2%.
2) Single‑Line Diagram synth → sld_generate → attach SVG to docs.
3) Rapid‑shutdown → code_check → insert MLPE devices.
4) Conduit fill → wire_check → add pull boxes & lengths.
5) Fault current & breaker sizing → short_circuit / protection_coordination → protective device updates.
6) Tracker row spacing → shading/backtracking sim → `structures`/`physical` updates.
7) Thermal hotspot prediction → thermal model → derate zone; re‑route strings.
8) Voltage ride‑through settings → grid_code profile → `instances[].settings`.
9) Nameplate OCR → serial attach to instances.
10) Pro user manual edits → AI re‑balances strings while preserving constraints.

### C) Compliance & Codes
1) IEEE 1547 / Rule 21 checks → code_check → `compliance.evidence` + settings table.
2) NEC 690 derate → temp factors → conductor sizes patched.
3) UL 9540A clearances → layout warnings → keep‑out zones.
4) Grounding/Bonding calc → earth target → BOM & trench routes.
5) Fire setback visual → heat map overlays on Canvas.
6) Permit package → doc_pack → stamped drawings & schedules.
7) Utility interconnection forms → merge from ODL‑SD → prefilled submission.
8) DPP readiness → traceability fields + QR links.
9) Accessibility labels/alt‑text → generated & bound.
10) Governance gate → publish_design → signed baseline hash.

### D) Procurement & Suppliers
1) BOM→RFQ with alternates → rfq_issue.
2) Bid scoring (price/lead/ESG) → bid_score → award_po; escrow milestones.
3) Stock‑out → alternates via port‑compat graph → swap inverter; finance re‑run.
4) Duties/VAT calc → price_index + tax tool → update `finance.capex`.
5) Supplier onboarding → compliance docs hashed; roles granted.
6) PO generation (UBL) → award_po → signed order; waybill expected.
7) Digital labels (SSCC/QR) → waybill_label.
8) Multi‑currency hedge → fx_hedge → escrow rules set.
9) Returns RMA on line items → rma_process.
10) Marketplace template sale → revenue share + payout schedule.

### E) Construction & Logistics
1) Pick/pack list → inventory reservations by serial/lot.
2) EPCIS events → last‑known location dashboard.
3) Delivery deviation photo → image_qc; supplier notified.
4) Crew route plan → crew_schedule; SMS/WhatsApp dispatch.
5) Site access QR + safety briefing → workorder_generate with checklists.
6) Conduit trench profile → automatic BOM per run.
7) Rail torque evidence → photo OCR; attach to commissioning.
8) String pull test capture → values stored per string.
9) Dynamic stow in high winds → tracker control plan.
10) Daily progress summary → photos + counts → PM report.

### F) Commissioning & Testing
1) IV curves (C&I/utility) → ingest & compare.
2) Insulation & polarity checks → thresholds verified; blockers.
3) PCS grid support tests → scripted; results logged.
4) Relay secondary injection → plan; evidence attached.
5) Protection coordination matrix → verified thresholds; doc export.
6) Performance test (ASTM E2848) → 7‑day run; uncertainty calc.
7) Firmware version snapshot → `instances[].firmware` lock.
8) Punchlist from photos → tasks; severity & due.
9) Sign‑off → governance signatures; escrow release.
10) Handover portal → read‑only baseline, warranty ledger.

### G) Operations & Monitoring
1) Anomaly on string currents → root‑cause; work order.
2) Soiling index → cleaning schedule optimisation.
3) PR & availability KPIs → monthly exec report.
4) Alarm flood triage → dedupe & rank.
5) Curtailment analytics → finance impact; PPA compliance.
6) Degradation regression → warranty watchlist.
7) Weather forecast → stow policies & BESS arbitrage schedule.
8) Spare parts prediction → reorder plan; spares RFQs.
9) Cyber posture (SCADA) → patch window booking; rollback.
10) ESG dashboards → avoided CO₂e & biodiversity metrics.

### H) Warranty & Service
1) Claim pack assembly → manufacturer portal payload.
2) RMA SSCC labels → tracking to vendor.
3) After‑fix verification photos → wiring overlays; close ticket.
4) Extended warranty upsell at risk points → offers.
5) Root‑cause library update → Reflection distills guides.
6) VoIP scripted triage → consistent handling.
7) SMS status bot → claim milestones.
8) Third‑party service tender → marketplace; 3% fee.
9) SLA breach detection → auto credits.
10) Portfolio heatmap → CAPA plan.

### I) Repowering & Upgrades
1) BESS augmentation Y7 → capacity gap → options, ROI.
2) Inverter derating trend → replacement plan; finance sensitivity.
3) Hail‑prone rows → stronger glass; risk model.
4) Tracker firmware → staged rollout; rollback.
5) EV chargers added → load flow + protection recheck.
6) PPC/EMS features → grid services revenue sim.
7) SLD regeneration post changes → doc_pack diff.
8) Re‑stringing after shading shift → autoroute; new gauge.
9) Tariff change → reoptimise arbitrage; policy update.
10) Upsell campaign → proposals at scale; conversion tracked.

### J) Decommissioning & Circularity
1) EoL plan → removal schedules; recycling partners; economics.
2) Asset resale vs scrap → price forecasts; residuals.
3) Transformer oil handling → DGA & disposal docs.
4) Grounding grid extraction → safety steps; permits.
5) Module recycling logistics → SSCC chain; certificates.
6) Land restoration scope → seed mixes; erosion control.
7) Bond/escrow release → evidence milestones.
8) Warranty transfer/closeout → ledger updates.
9) Lessons learned → Reflection updates standards.
10) Sustainability report → lifecycle avoided CO₂e, circular metrics.

---

## 13) Advanced Topics & Changelog
- **ReflectionAgent:** mines audit logs + graph to improve prompts/playbooks; proposes rule updates (human‑approved).
- **ModelSelector:** cost/quality routing; A/B swaps (small orchestration model vs large planner; vision for QC).
- **RegionRouter:** tenant residency and local incentive sources; regional SLA targets.
- **Consentful Outreach:** marketing tools require consent; rate‑limited; transparent logs.
- **Auto‑layout/Auto‑route:** graph shortest‑paths with electrical constraints; interactive on Canvas; undo via Patch history.

**v1.1 changes (vs v1.0):** proactive autonomy; multimodal grounding; ModelSelector/RegionRouter; Reflection loops; cache drift detection; JSON‑Patch batching & rollback; hybrid monetisation separation; Planner Trace UI.

---

## 14) Appendix A — Patch Patterns (snippets)
- **Add component instance**
```json
[{"op":"add","path":"/design/components/-","value":{"id":"inv_002","type":"inverter","model":"X123","ports":{"dc":["dc1","dc2"],"ac":["ac1"]}}}]
```
- **Connect string to inverter port**
```json
[{"op":"add","path":"/connections/-","value":{"from":"string_A","to":"inv_002/dc1","type":"dc"}}]
```
- **Finance assumption update**
```json
[{"op":"replace","path":"/finance/opex/maintenance_per_kw","value":12.5}]
```
- **Warranty ticket create**
```json
[{"op":"add","path":"/warranty/tickets/-","value":{"id":"wt_101","component":"inv_002","issue":"GFCI fault","evidence":["img://..."],"status":"new"}}]
```
- **Rollback inverse** → call `generate_inverse_patch` on the last commit and re‑apply.

---

## 15) Appendix B — Tool I/O Schemas (Draft 2020‑12)
> Strict schemas for Day‑1 tools. `additionalProperties: false` everywhere. Include in Tool Registry with **semver**; version bumps auto‑invalidate caches.

### 1) `validate_odl_sd`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.validate_odl_sd.input",
  "title": "validate_odl_sd.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string", "pattern": "^[a-zA-Z0-9_\\-:.]+$" },
    "target_version": { "type": "integer", "minimum": 0 },
    "schema_version": { "type": "string", "pattern": "^4\\.(1|2|x)$" },
    "checks": {
      "type": "array",
      "items": { "type": "string", "enum": [
        "structure", "types", "domain", "ports", "connections", "finance_links", "compliance"
      ] },
      "uniqueItems": true
    },
    "fast": { "type": "boolean", "default": true }
  },
  "required": ["doc_id", "schema_version"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.validate_odl_sd.output",
  "title": "validate_odl_sd.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "schema_version": { "type": "string" },
    "valid": { "type": "boolean" },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "path": { "type": "string" },
          "code": { "type": "string" },
          "severity": { "type": "string", "enum": ["error", "warning", "info"] },
          "message": { "type": "string" },
          "hint": { "type": "string" }
        },
        "required": ["path", "code", "severity", "message"]
      }
    },
    "summary": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "errors": { "type": "integer", "minimum": 0 },
        "warnings": { "type": "integer", "minimum": 0 }
      },
      "required": ["errors", "warnings"]
    }
  },
  "required": ["doc_id", "doc_version", "schema_version", "valid", "issues", "summary"]
}
```

### 2) `simulate_energy`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.simulate_energy.input",
  "title": "simulate_energy.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "scope": { "type": "string", "enum": ["portfolio", "site", "subsystem", "array"] },
    "site_id": { "type": "string" },
    "subsystem_ids": { "type": "array", "items": {"type": "string"}, "uniqueItems": true },
    "period": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "start": { "type": "string", "format": "date" },
        "end": { "type": "string", "format": "date" }
      },
      "required": ["start", "end"]
    },
    "granularity": { "type": "string", "enum": ["monthly", "hourly", "subhourly"] },
    "weather": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "source": { "type": "string", "enum": ["TMY", "NSRDB", "ERA5", "Measured", "Custom"] },
        "dataset_id": { "type": "string" },
        "lat": { "type": "number", "minimum": -90, "maximum": 90 },
        "lon": { "type": "number", "minimum": -180, "maximum": 180 }
      }
    },
    "assumptions": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "soiling": { "type": "number", "minimum": 0, "maximum": 0.2, "default": 0.02 },
        "availability": { "type": "number", "minimum": 0.8, "maximum": 1.0, "default": 0.99 },
        "temp_model": { "type": "string", "enum": ["NOCT", "SANDIA", "Faiman"] }
      }
    },
    "returns": { "type": "array", "items": {"type": "string", "enum": ["summary", "losses", "timeseries", "pr", "capacity_factor"]}, "uniqueItems": true }
  },
  "required": ["doc_id", "scope", "period", "granularity"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.simulate_energy.output",
  "title": "simulate_energy.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "scope": { "type": "string" },
    "assumptions_resolved": { "type": "object" },
    "summary": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "annual_yield_kwh": { "type": "number", "minimum": 0 },
        "pr": { "type": "number", "minimum": 0, "maximum": 1 },
        "capacity_factor": { "type": "number", "minimum": 0, "maximum": 1 }
      },
      "required": ["annual_yield_kwh"]
    },
    "losses_breakdown": { "type": "object" },
    "timeseries": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "ts": { "type": "string", "format": "date-time" },
          "p_ac_kw": { "type": "number" },
          "p_dc_kw": { "type": "number" },
          "e_kwh": { "type": "number" }
        },
        "required": ["ts", "p_ac_kw"]
      }
    },
    "warnings": { "type": "array", "items": {"type": "string"} }
  },
  "required": ["doc_id", "doc_version", "summary"]
}
```

### 3) `simulate_finance`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.simulate_finance.input",
  "title": "simulate_finance.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "scenario_name": { "type": "string", "minLength": 1 },
    "site_id": { "type": "string" },
    "analysis_period_years": { "type": "integer", "minimum": 1, "maximum": 35, "default": 20 },
    "discount_rate": { "type": "number", "minimum": -0.2, "maximum": 0.5 },
    "debt_ratio": { "type": "number", "minimum": 0, "maximum": 1 },
    "tax_rate": { "type": "number", "minimum": 0, "maximum": 1 },
    "capex_override": { "type": "number", "minimum": 0 },
    "opex_override": { "type": "number", "minimum": 0 },
    "tariff": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "tariff_id": { "type": "string" },
        "rate_cents_kwh": { "type": "number", "minimum": 0 },
        "demand_charge_usd_kw": { "type": "number", "minimum": 0 }
      }
    },
    "incentives_auto_fetch": { "type": "boolean", "default": true },
    "outputs": { "type": "array", "items": {"type": "string", "enum": ["irr","npv","payback","cashflows","sensitivity"]}, "uniqueItems": true }
  },
  "required": ["doc_id", "scenario_name", "analysis_period_years"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.simulate_finance.output",
  "title": "simulate_finance.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "scenario_name": { "type": "string" },
    "irr": { "type": "number" },
    "npv_usd": { "type": "number" },
    "payback_years": { "type": "number" },
    "cashflows": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "year": { "type": "integer" },
          "revenue_usd": { "type": "number" },
          "opex_usd": { "type": "number" },
          "capex_usd": { "type": "number" },
          "net_usd": { "type": "number" }
        },
        "required": ["year","net_usd"]
      }
    },
    "assumptions_resolved": { "type": "object" },
    "warnings": { "type": "array", "items": {"type": "string"} }
  },
  "required": ["doc_id", "doc_version", "scenario_name", "irr", "npv_usd", "payback_years"]
}
```

### 4) `bom_sourcing`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.bom_sourcing.input",
  "title": "bom_sourcing.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "bom_ref": { "type": "string", "description": "JSON Pointer to BOM, e.g., /bom/current" },
    "region": { "type": "string" },
    "country": { "type": "string" },
    "currency": { "type": "string", "pattern": "^[A-Z]{3}$" },
    "delivery_by": { "type": "string", "format": "date" },
    "preferences": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "esg_min_score": { "type": "number", "minimum": 0, "maximum": 100 },
        "preferred_brands": { "type": "array", "items": {"type": "string"}, "uniqueItems": true },
        "exclude_brands": { "type": "array", "items": {"type": "string"}, "uniqueItems": true },
        "max_lead_time_days": { "type": "integer", "minimum": 0 }
      }
    },
    "rfq_mode": { "type": "string", "enum": ["price_only","landed_cost","availability_only","balanced"] },
    "max_suppliers": { "type": "integer", "minimum": 1, "maximum": 50, "default": 10 },
    "solicit_channels": { "type": "array", "items": {"type":"string","enum":["marketplace","approved_vendors","external_search"]}, "uniqueItems": true }
  },
  "required": ["doc_id", "bom_ref", "currency"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.bom_sourcing.output",
  "title": "bom_sourcing.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "quotes": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "quote_id": { "type": "string" },
          "supplier_id": { "type": "string" },
          "currency": { "type": "string" },
          "valid_until": { "type": "string", "format": "date-time" },
          "incoterms": { "type": "string" },
          "esg_score": { "type": "number", "minimum": 0, "maximum": 100 },
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "item_ref": { "type": "string" },
                "unit_price": { "type": "number", "minimum": 0 },
                "moq": { "type": "integer", "minimum": 1 },
                "lead_time_days": { "type": "integer", "minimum": 0 },
                "availability": { "type": "integer", "minimum": 0 }
              },
              "required": ["item_ref","unit_price"]
            }
          },
          "shipping_cost": { "type": "number", "minimum": 0 },
          "duties": { "type": "number", "minimum": 0 },
          "taxes": { "type": "number", "minimum": 0 }
        },
        "required": ["quote_id","supplier_id","currency","items"]
      }
    },
    "alternates": { "type": "array", "items": {"type": "object"} },
    "recommended_award": { "type": "string" },
    "procurement_patch": { "type": "array", "items": { "type": "object" } },
    "warnings": { "type": "array", "items": {"type": "string"} }
  },
  "required": ["doc_id", "doc_version", "quotes"]
}
```

### 5) `payments.create_quote`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.payments.create_quote.input",
  "title": "payments.create_quote.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "quote_id": { "type": "string" },
    "currency": { "type": "string", "pattern": "^[A-Z]{3}$" },
    "items": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "ref": { "type": "string" },
          "description": { "type": "string" },
          "quantity": { "type": "number", "minimum": 0 },
          "unit_price": { "type": "number", "minimum": 0 },
          "tax_rate": { "type": "number", "minimum": 0, "maximum": 1 }
        },
        "required": ["description","quantity","unit_price"]
      }
    },
    "terms": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "valid_days": { "type": "integer", "minimum": 1, "maximum": 90 },
        "payment_terms": { "type": "string", "enum": ["prepaid","net30","milestones"] },
        "deposit_percent": { "type": "number", "minimum": 0, "maximum": 1 },
        "escrow": { "type": "boolean", "default": false }
      }
    },
    "notify": {
      "type": "array",
      "items": { "type": "string", "enum": ["email","whatsapp"] },
      "uniqueItems": true
    },
    "recipients": { "type": "array", "items": {"type":"string", "format":"email"}, "uniqueItems": true }
  },
  "required": ["doc_id", "currency", "items"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.payments.create_quote.output",
  "title": "payments.create_quote.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "quote_id": { "type": "string" },
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "ezpay_url": { "type": "string", "format": "uri" },
    "pdf_url": { "type": "string", "format": "uri" },
    "totals": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "subtotal": { "type": "number" },
        "tax": { "type": "number" },
        "total": { "type": "number" }
      },
      "required": ["total"]
    },
    "status": { "type": "string", "enum": ["draft","sent","accepted","expired"] }
  },
  "required": ["quote_id", "doc_id", "doc_version", "ezpay_url", "totals", "status"]
}
```

### 6) `datasheet_parser`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.datasheet_parser.input",
  "title": "datasheet_parser.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source": {
      "oneOf": [
        {"type":"object","properties":{"file_url":{"type":"string","format":"uri"}},"required":["file_url"],"additionalProperties":false},
        {"type":"object","properties":{"image_url":{"type":"string","format":"uri"}},"required":["image_url"],"additionalProperties":false}
      ]
    },
    "parsing_profile": { "type": "string", "enum": ["pv_module","inverter","battery","combiner","cable","other"] },
    "vendor": { "type": "string" },
    "ocr_langs": { "type": "array", "items": {"type":"string"}, "uniqueItems": true },
    "extract_fields": { "type": "array", "items": {"type":"string"}, "uniqueItems": true },
    "normalize_units": { "type": "boolean", "default": true }
  },
  "required": ["source", "parsing_profile"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.datasheet_parser.output",
  "title": "datasheet_parser.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "component_template": { "type": "object" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "fields_raw": { "type": "array", "items": { "type": "object" } },
    "source_hash": { "type": "string" },
    "warnings": { "type": "array", "items": {"type":"string"} }
  },
  "required": ["component_template", "confidence", "source_hash"]
}
```

### 7) `image_analyzer`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.image_analyzer.input",
  "title": "image_analyzer.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "image_url": { "type": "string", "format": "uri" },
    "tasks": { "type": "array", "items": {"type":"string","enum":["qc_blur","qc_exposure","detect_labels","detect_components","ocr_nameplate","thermal_hotspots","safety_violations"]}, "minItems": 1, "uniqueItems": true },
    "context": { "type": "object" },
    "privacy": { "type": "object", "properties": {"face_blur":{"type":"boolean"}, "geo_strip":{"type":"boolean"}}, "additionalProperties": false }
  },
  "required": ["image_url", "tasks"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.image_analyzer.output",
  "title": "image_analyzer.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "findings": { "type": "array", "items": { "type": "object" } },
    "derived": { "type": "object" },
    "issues": { "type": "array", "items": {"type":"object"} },
    "evidence_overlays_url": { "type": "string", "format": "uri" },
    "redactions_applied": { "type": "array", "items": {"type":"string"} }
  },
  "required": ["findings"]
}
```

### 8) `qc_rules`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.qc_rules.input",
  "title": "qc_rules.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "scope_path": { "type": "string", "pattern": "^/" },
    "rules": { "type": "array", "items": {"type":"string","enum":["dc_voltage_limits","ac_conductor_sizing","voltage_drop","string_mismatch","rapid_shutdown","grounding","breaker_sizing"]}, "minItems": 1, "uniqueItems": true },
    "standards_context": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "region": { "type": "string" },
        "codes": { "type": "array", "items": {"type":"string"}, "uniqueItems": true },
        "temperature_c": { "type": "number" },
        "altitude_m": { "type": "number" }
      }
    },
    "simulation_refs": { "type": "object" }
  },
  "required": ["doc_id", "scope_path", "rules"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.qc_rules.output",
  "title": "qc_rules.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "pass": { "type": "boolean" },
    "violations": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "rule_id": { "type": "string" },
          "path": { "type": "string" },
          "measured": { "type": "number" },
          "limit": { "type": "number" },
          "severity": { "type": "string", "enum": ["blocker","error","warning"] },
          "message": { "type": "string" }
        },
        "required": ["rule_id","path","severity","message"]
      }
    },
    "suggestions": { "type": "array", "items": { "type": "object" } },
    "report_url": { "type": "string", "format": "uri" }
  },
  "required": ["doc_id", "doc_version", "pass", "violations"]
}
```

### 9) `web_incentives`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.web_incentives.input",
  "title": "web_incentives.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "region": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "country": { "type": "string" },
        "state": { "type": "string" },
        "utility": { "type": "string" }
      },
      "required": ["country"]
    },
    "tech": { "type": "string", "enum": ["pv","bess","pv+bess","evc"] },
    "customer_type": { "type": "string", "enum": ["residential","commercial","utility"] },
    "system_size_kw": { "type": "number", "minimum": 0 },
    "program_types": { "type": "array", "items": {"type":"string","enum":["rebate","tax_credit","feed_in","net_metering","SREC"]}, "uniqueItems": true },
    "as_of": { "type": "string", "format": "date" }
  },
  "required": ["region", "tech", "customer_type"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.web_incentives.output",
  "title": "web_incentives.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "incentives": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "program_id": { "type": "string" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "amount_type": { "type": "string", "enum": ["flat","per_kw","percent"] },
          "amount_value": { "type": "number" },
          "cap": { "type": "number" },
          "stackable": { "type": "boolean" },
          "links": { "type": "array", "items": {"type":"string","format":"uri"} },
          "expires_on": { "type": "string", "format": "date" }
        },
        "required": ["program_id","name","amount_type","amount_value"]
      }
    },
    "compliance_requirements": { "type": "array", "items": {"type":"string"} },
    "last_checked": { "type": "string", "format": "date-time" },
    "sources": { "type": "array", "items": {"type":"string","format":"uri"} }
  },
  "required": ["incentives", "last_checked"]
}
```

### 10) `esg_simulator`
**Input**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.esg_simulator.input",
  "title": "esg_simulator.input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "scope": { "type": "string", "enum": ["site","portfolio"] },
    "methodology": { "type": "string", "enum": ["GHG_PowerSector","custom"] },
    "grid_emission_factor": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "source": { "type": "string", "enum": ["iem","epa","defra","custom"] },
        "kg_co2e_per_kwh": { "type": "number", "minimum": 0 }
      },
      "required": ["source"]
    },
    "embodied_carbon_modules": { "type": "number", "minimum": 0 },
    "recycling_scenario": { "type": "string", "enum": ["none","partial","full"] },
    "period": { "type": "object", "properties": {"start":{"type":"string","format":"date"}, "end":{"type":"string","format":"date"}}, "required":["start","end"], "additionalProperties": false },
    "outputs": { "type": "array", "items": {"type":"string","enum":["annual_avoided_co2e","lifecycle_avoided","credits_estimate","report_pdf"]}, "uniqueItems": true }
  },
  "required": ["doc_id", "scope", "methodology", "period"]
}
```
**Output**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "schema:tool.esg_simulator.output",
  "title": "esg_simulator.output",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "doc_id": { "type": "string" },
    "doc_version": { "type": "integer" },
    "annual_avoided_co2e_tons": { "type": "number" },
    "lifecycle_avoided_co2e_tons": { "type": "number" },
    "credits_estimate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "quantity": { "type": "number" },
        "price_low_usd": { "type": "number" },
        "price_high_usd": { "type": "number" }
      }
    },
    "assumptions_resolved": { "type": "object" },
    "report_url": { "type": "string", "format": "uri" }
  },
  "required": ["doc_id", "doc_version"]
}
```

---

## 16) Decisions Log (keep current)
- **Tools are authoritative.** LLM output cannot override tool results.
- **Patches only.** No free‑form writes to ODL‑SD; all changes are diffable and auditable.
- **Reflection offline‑first.** Online learning allowed only for low‑risk hints; design writes remain human‑approved.
- **Consentful outreach.** Marketing/lead gen requires explicit consent; rate‑limited and logged.
- **Region routing enforced.** Data residency and SLA targets per tenant/region.
- **Quarterly fine‑tuning window.** Domain models tuned on anonymised ODL‑SD telemetry, with privacy review.

---

**End of Unified Master Blueprint** — Treat this as the canonical document for AI architecture, development, governance, and tool contracts. Update via PR‑style edits with versioned changelog entries above.

