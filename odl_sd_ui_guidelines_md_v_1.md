# ODL_SD_UI_Guidelines.md v1.0 (Master)

**Status:** Canonical UI contract for ODL‑SD Web App • **Audience:** Frontend engineers, design systems, and development AIs • **Scope:** All surfaces (App/Workspace, Marketplace, Plans), all roles, all lifecycle phases, and all management consoles (AI/Agents/Models/Tools/Suppliers/Users/Tenants/Finance/ESG).
**Philosophy:** *Maximum MainPanel, minimum chrome.* The UI should feel invisible—neutral, fast, and predictable—while exposing deep power through context, traceability, and reversible actions.

---

## 0) Design Principles (Non‑negotiable)
1. **MainPanel first.** Header auto‑hides; StatusBar translucent; Co‑Pilot collapses. All layouts prefer content over chrome.
2. **Single source of truth.** Every view binds to the ODL‑SD JSON and its patches. Approvals show **human‑readable diffs** before merge.
3. **Progressive disclosure.** Default to clean summaries; reveal density on demand (expanders, tabs, drawers, modals).
4. **Role‑aware, phase‑aware.** Surfaces filter by capability and lifecycle gates; explain *why* something is locked.
5. **Agent transparency.** Co‑Pilot shows **Intent → Plan → Action & Evidence → Proposed Change (Diff) → Approval** with confidence chips.
6. **Mobile & offline.** Field apps run offline, queue work, and sync safely; nothing breaks on spotty networks.
7. **Accessibility before style.** WCAG 2.1 AA; keyboard‑first; reduced‑motion variants; internationalization and RTL support.

---

## 1) Tokens, Theme, Iconography, Motion

### 1.1 Neutral Palette (Monochrome)
- **Base neutrals (light):**
  `--n-0:#FFFFFF; --n-50:#F7F7F8; --n-100:#F3F4F6; --n-200:#E5E7EB; --n-300:#D1D5DB; --n-400:#9CA3AF; --n-500:#6B7280; --n-600:#4B5563; --n-700:#374151; --n-800:#1F2937; --n-900:#111827; --n-950:#0B0F16`
- **Roles (light):**
  `--bg:var(--n-50); --surface0:var(--n-0); --surface1:var(--n-100); --surface2:var(--n-200); --text:var(--n-900); --text-2:var(--n-600); --border:var(--n-200); --focus:rgba(55,65,81,.45)`
- **Roles (dark):**
  `--bg:var(--n-900); --surface0:var(--n-800); --surface1:#1A2230; --surface2:var(--n-700); --text:#F7F7F8; --text-2:#D1D5DB; --border:rgba(255,255,255,.12); --focus:rgba(209,213,219,.45)`
- **Status (desaturated):** info → `--n-600`; success → `--n-700`; warn → `--n-700`; error → `--n-800`.

### 1.2 Typography
- **Family:** Inter, IBM Plex Sans, system‑ui.
- **Sizes:** 12/18, 14/20, **16/24 (base)**, 18/28, 20/28, 24/32, 32/40, 40/48.
- **Weights:** 400/500/600.
- **Tracking:** tight −0.01em; normal 0; wide +0.02em.

### 1.3 Iconography (single‑colour outline)
- 24px grid, 1.5px stroke; inherits text colour; no multicolour glyphs.
- Common set: home, grid, layers, layout‑split, table, search, settings, plus, edit, trash, download, upload, share, diff, check, x, clock, bot, sparkles, workflow, tag, truck, package, map‑pin, handshake, shield, file‑check, signature, lock, unlock, history.

### 1.4 Motion (micro‑interactions only)
- **Durations:** 120/200/300ms. **Easing:** `cubic-bezier(.2,.8,.2,1)`; decelerate `cubic-bezier(0,0,.2,1)`.
- **Allowed transitions:** opacity, transform (translate/scale), height/width of drawers; **no parallax**.
- **Reduced motion:** disable transitions when `prefers-reduced-motion:reduce`.

---

## 2) Global Layout, Chrome Minimization & Z‑Order

### 2.1 Grid & Areas (Desktop ≥1280px)
```
┌ header (auto‑hide) ┐
│                    │
├ toolbar ───────────┤
│ sidebar │ main │ co‑pilot │
│ (hover  │      │ (slide‑  │
│ expand) │      │  in)     │
├ status (translucent, overlays main at bottom) ┤
```
- **Columns:** sidebar 250→64 (collapsed), main `1fr`, co‑pilot 320 (resizable 280–520).
- **Rows:** header (48–64), toolbar (48–56), main `1fr`, status (36).
- **Gaps:** 4px.

### 2.2 Header Auto‑Hide
- Default hidden; shows **3×3 dots** (12×12) at top‑left as affordance.
- **Show header** on hover/FocusWithin over top 48px strip *or* click dots.
- **Hide** on mouseleave after 600ms; keyboard users toggle with `Alt+H`.
- While hidden, toolbar remains; header reflow must not jank main.

### 2.3 StatusBar (translucent)
- Sticks to bottom; `backdrop-filter:saturate(120%) blur(4px)`; opacity 0.9;
- Messages slide up (120ms) and auto‑dismiss unless sticky.

### 2.4 Sidebar (hover‑expand)
- **Collapsed state:** 64px rail with icons; label tooltips on focus/hover.
- **Hover over rail** opens fly‑out panel (250px) with nav + tree; stays open while cursor inside; closes 400ms after leave.
- **Pin** via context menu or `Alt+S`.
- **Project Explorer:** folder/tree for Portfolio ▶ Site ▶ Plant ▶ Block ▶ Array ▶ String ▶ Device; supports lazy load, rename, drag‑reorder, and favourites.

### 2.5 Co‑Pilot (right slide‑in)
- Default width 320px; resizable 280–520; collapsible to tab.
- Five panes (accordions): **Intent • Plan • Action & Evidence • Diff • Approvals/Collab**.
- **Chat input** can: (a) dock at Co‑Pilot bottom; or (b) **overlay** centered above StatusBar (80% width) when Co‑Pilot collapsed or when “Focus Mode” is on.
- Streamed tokens render incrementally; show typing indicator and tool chips.

### 2.6 MainPanel
- Primary surface; supports **SplitView** (70/30) with Inspector; remembers last split per view.
- Zoom controls bottom‑right; grid snap; rulers optional; multi‑layer overlays (Electrical/Mechanical/Physical/Compliance/Finance/ESG).

### 2.7 Z‑Index & Overlays
1. Status toasts
2. Modals/Drawers
3. Co‑Pilot (when open)
4. Header/Toolbar
5. Main/Sidebar

---

## 3) Navigation, Menus & Modes
- **Context Tabs (Header):** Workspace / Marketplace / Plans.
- **Primary Nav (Sidebar):** Dashboard, Tasks, Projects (tree), Components, Suppliers, Files, Tenants (Admin), AI Agents (Admin), Settings.
- **Contextual Toolbar:** view‑specific actions (New, Import, Auto‑Route, Validate, Generate SLD, Simulate, Doc Pack, Diff, Share), **Layer** segmented control, **SplitView**, **Theme**, **Autonomy** (Ask‑Each / Project / Session).
- **Command Bar (⌘/Ctrl+K):** navigations, actions, and help.
- **Focus Mode:** hides header & sidebar; Co‑Pilot collapses; chat input overlays MainPanel.

---

## 4) Signature Visualizations

### 4.1 Interactive Icicle Diagram (Project & Portfolio)
- **Purpose:** dense, beautiful overview of hierarchy and cost/validation.
- **Encoding:** rect size = CAPEX (or capacity), colour = validation (green/warn/error/grey).
- **Interaction:** zoom/pan; hover tooltip (name, type, key specs, cost share); click to **focus & filter** everything (Inspector, Co‑Pilot context, breadcrumbs).
- **Global:** portfolio view stacks projects as top‑level partitions.
- **Performance:** virtualize nodes > 2k; tile rendering on zoom.

### 4.2 Canvas / SLD / Wiring
- **Nodes:** components with ports; ghost wires; auto‑layout (ELK/dagre).
- **Context menu:** Open Details, Show Connections, Run Check, Highlight Path.
- **Layers:** toggles per discipline; violations overlay (badges + list in Inspector).
- **Doc outputs:** SLD SVG export; Wiring guide with port callouts.

---

## 5) Co‑Pilot (Agentic UX)
- **INTENT**: user request; quick clarifiers; mode selector.
- **PLAN**: ordered chips (tool + params), cost/latency bars, cache badge.
- **ACTION & EVIDENCE**: result cards, links to reports and media.
- **DIFF**: JSON‑Patch viewer (humanized; grouped by section); KPIs deltas.
- **APPROVALS & COLLAB**: Approve/Reject/Edit; autonomy radio; @mentions; Invite Agent (DesignEngineer, SourcingGrowth, OpsSustainability, etc.).
- **Confidence chips**: High/Med/Low; explainability link opens Planner Trace.
- **Chat input placement rules:**
  - Docked bottom of Co‑Pilot when open.
  - Overlay (centered above StatusBar) when Co‑Pilot collapsed or Focus Mode on.
  - Mobile: bottom sheet with safe‑area insets.

---

## 6) Management Consoles

### 6.1 AI Architecture & Agents (drag‑drop)
- **Graph editor:** Agents (nodes), Tools (nodes), Connectors (edges).
- **Node inspector:** name, version, scopes, guard budgets, region routing, autonomy.
- **Playground:** run plans against sandbox doc; see **Planner Trace** (timeline, tool spans, costs, cache hits).
- **Deploy:** version pinning; canary/A‑B; rollback; export/import JSON config.
- **Access:** RBAC per agent/tool; audit all edits.

### 6.2 AI Model Management (local & external)
- Registry of models (LLM/Vision/Embeddings); provider keys; region; cost; latency; eval scores.
- **Switching rules:** ModelSelector matrix per task; fallbacks; timeouts.
- **CAG store:** cache hit ratios; drift alerts; invalidation events.

### 6.3 Tool Creation & Management
- Define tool schema (input/output, side_effects, rbac_scope); semver; status (stable/beta).
- **Test bench:** run with sample inputs; view output JSON + rendered cards; attach evidence links.
- **Docs:** markdown with examples; **OpenAPI**/SDK generation.

### 6.4 Components Library UIs
- **Datasheet parse** split view: PDF left, form right; polling; confidence banners.
- **Compare** (multi‑select): highlight differences; pin attributes; export CSV.
- **Symbols & ports:** IEC symbol map; port typing; SLD symbol palette.
- **Media**: hero/detail/wiring/thermal/service photos; privacy masks; doc bindings; DPP/QR.

### 6.5 Supplier Management UIs
- Directory & onboarding; ESG badges; compliance docs.
- **RFQ→Bids→Award→PO** pipeline (Kanban + Compare modal).
- Shipments timeline (**EPCIS** events, SSCC); inventory (lot/serial); returns & RMAs; warranty claims; analytics.

### 6.6 User & Tenant Management
- **Roles & rights** editor; **Permission Visualizer** (by hierarchy node, with inheritance trail).
- Tenants: branding, SSO, data residency, SIEM webhooks; usage/PSU budgets; audit.

### 6.7 Pricing & Financial UIs
- Scenario Foundry (what‑if; IRR/LCOE/NPV deltas); Monte Carlo viewer; tariff & incentives fetch; FX hedge.
- Quotes/Invoices; checkout; **Transparency Dashboard** (fees, PSU, savings, carbon); marketplace take‑rates.

### 6.8 Marketplace UIs
- **Templates:** browse, preview, purchase/resell (clear splits).
- **Components:** spec search, cert filters, availability, add to RFQ.
- **Services:** skills/location/rating; request service; escrow milestones.

### 6.9 Multi‑domain & Multi‑tenant Windows
- Domain switcher (PV/BESS/GRID/SCADA); tenant switcher (org logo).
- Multi‑window workspaces (optional): detach Inspector/Co‑Pilot into floating panels; snap to edges; restore layouts.

---

## 7) Interactions, Transitions & Micro‑states

### 7.1 Header Auto‑Hide
- **Hidden:** only 3×3 dots visible.
- **Reveal:** fade/slide from top (200ms) on hover/focus/click.
- **Hide:** 600ms delay after mouseleave; persistent while menus open.

### 7.2 Sidebar Hover‑Expand
- Rail → fly‑out (width transition 200ms); keep open while pointer inside; close 400ms after leave.
- Keyboard: `Tab` into rail opens; `Esc` closes.

### 7.3 Co‑Pilot Slide & Resize
- Slide from right (200ms); resizer shows live width; collapse to tab with icon; restore on click.

### 7.4 StatusBar
- Translucent; toast messages slide/fade; single line of highest‑priority message; `aria-live=polite`.

### 7.5 Diff & Approvals
- Open diff in panel/drawer; inline row animations for changed fields; Approve triggers confetti (1 particle stripe in monochrome) only for milestone merges (optional).

### 7.6 Loading & Skeletons
- Skeleton blocks for tables/cards/inspectors; shimmer subtle; fallback text for AI: “Thinking…”.

### 7.7 Errors & Alerts
- Inline banners (monochrome tints); actionable CTA; toast for background failures; link to logs.

---

## 8) Accessibility
- Landmarks: `<header> <nav> <main> <aside> <footer>`; skip‑to‑main link.
- Focus rings (`:focus-visible`) everywhere; traps in modals; restore focus on close.
- **ARIA:** Co‑Pilot uses `aria-live` for streamed content; status uses `role=status` + `aria-live=polite`.
- High contrast variant toggles stronger borders and text; reduced motion disables transitions.
- i18n: all strings in resource files; units reflect locale; RTL mirrors layout; date/number formats localised.

---

## 9) Responsive & Mobile
- **Breakpoints:**
  Mobile <768 • Tablet 768–1279 • Desktop ≥1280 • Wide ≥1600.
- Tablet: Co‑Pilot overlays; Sidebar collapses; Toolbar condenses to overflow (⋯).
- Mobile: stacked layout; Sidebar becomes bottom tab bar (Tasks, Projects, Scan, Profile); tables → cards; chat input as bottom sheet.

---

## 10) Offline & Sync (Field)
- PWA with Workbox; IndexedDB (Dexie) for offline work packages and media queue.
- Visual sync debt meter per work package; retries with exponential backoff; conflict prompts with diff.

---

## 11) Performance Budgets
- TTFB < 800ms; LCP < 2.5s; FID < 100ms; CLS < 0.1.
- Virtualize long lists; code‑split heavy canvases; lazy‑load media; prefetch next routes; throttle reflows.

---

## 12) Security & Privacy
- CSP strict; Trusted Types; DOMPurify for any HTML; sandboxed iframes.
- **Media privacy:** auto‑detect faces/plates; store raw in restricted tier; generate redacted renditions; log access.

---

## 13) State, Events & Telemetry
- **State model:** UI prefs (sidebar, theme, focus mode), selection, Co‑Pilot panes state, diff selection, overlay chat mode, reducedMotion.
- **Events:** App event bus for nav, tool calls, patch previews, approvals, toast.
- **Telemetry:** OpenTelemetry spans for tool calls and AI steps; correlate with Planner Trace IDs.

---

## 14) Testing & QA
- **Unit:** view models & formatters.
- **Component:** Storybook (a11y via axe) for Sidebar, Toolbar, Icicle, Diff, Co‑Pilot, Tables, Cards.
- **E2E:** Playwright for header auto‑hide, sidebar hover‑expand, overlay chat input, diff/approve flows, offline task run.
- **Visual:** per‑breakpoint snapshots; dark/light; focus/hover states.
- **Contract:** schemas for tool I/O; JSON Patch acceptance tests.

---

## 15) Code Patterns (reference)

### 15.1 Auto‑Hide Header & Hover Strip
```tsx
const [headerOpen,setHeaderOpen]=useState(false);
return (
  <div className="relative">
    <div className="absolute inset-x-0 top-0 h-12"
         onMouseEnter={()=>setHeaderOpen(true)}
         onFocus={()=>setHeaderOpen(true)}
         onMouseLeave={()=>setHeaderOpen(false)} />
    <header className={`fixed top-0 inset-x-0 transition-transform duration-200 ${headerOpen?'translate-y-0':'-translate-y-full'}`}>
      {/* header content */}
    </header>
    <button aria-label="Show header" className="absolute left-3 top-3 w-4 h-4 grid grid-cols-3 gap-[1px] opacity-80">
      {Array.from({length:9}).map((_,i)=>(<span key={i} className="bg-gray-400/80 w-1 h-1 rounded"/>))}
    </button>
  </div>
)
```

### 15.2 Sidebar Hover‑Expand
```tsx
const [open,setOpen]=useState(false);
<aside onMouseEnter={()=>setOpen(true)} onMouseLeave={()=>setOpen(false)}
  className={`transition-[width] duration-200 ${open?'w-[250px]':'w-[64px]'}`}>...</aside>
```

### 15.3 Co‑Pilot Slide & Overlay Chat Input
```tsx
const [copilotOpen,setCopilotOpen]=useState(true);
const [overlayChat,setOverlayChat]=useState(false);
<aside className={`fixed right-0 top-0 h-full bg-white dark:bg-[var(--surface0)] transition-transform ${copilotOpen?'translate-x-0':'translate-x-full'}`} style={{width:copilotWidth}} />
{overlayChat && (
  <form className="fixed left-1/2 -translate-x-1/2 bottom-12 w-[min(900px,80vw)] rounded-xl shadow bg-white/95 backdrop-blur p-3">
    <textarea className="w-full resize-none" rows={2} placeholder="Ask Co‑Pilot…" />
  </form>
)}
```

### 15.4 Translucent Status Bar
```tsx
<footer role="status" className="fixed bottom-0 inset-x-0 backdrop-blur bg-white/90 dark:bg-[var(--surface0)]/80 border-t border-[var(--border)] px-3 py-2">
  {/* highest priority message */}
</footer>
```

---

## 16) Delivery Phases (incremental)
- **Phase 0 (Weeks 1–2):** Shell (Header auto‑hide, Sidebar hover‑expand, Toolbar, Main, Co‑Pilot slide/resizer, StatusBar translucent).
- **Phase 1 (Weeks 3–5):** Projects tree, Icicle Diagram, Canvas/SLD with layers, Inspector; Diff viewer & Approvals.
- **Phase 2 (Weeks 6–8):** Components Library (parse/compare/symbols), Supplier RFQ→PO→EPCIS timeline, Inventory, Returns/RMA/Warranty.
- **Phase 3 (Weeks 9–11):** AI Consoles (Agents/Models/Tools), Planner Trace, Guard Budgets, Sandboxes.
- **Phase 4 (Weeks 12–14):** Finance/Scenario/Monte‑Carlo, Transparency Dashboard, Marketplace (Templates/Components/Services).
- **Phase 5 (Weeks 15–16):** Mobile/Offline PWA, performance hardening, a11y audit, theming and white‑label.

---

## 17) Glossary (UI terms)
- **MainPanel:** primary content area; must always maximize space.
- **Inspector:** right or split pane with details/tables.
- **Co‑Pilot:** agentic sidebar; five‑pane model; chat input docked/overlay.
- **Focus Mode:** minimal chrome; overlay chat input.
- **Permission Visualizer:** tree‑based viewer mapping roles → rights on a selected node with inheritance.

---

**This document is the single source of truth for ODL‑SD UI. All development (human or AI) must follow these contracts for structure, behavior, accessibility, and performance.**

