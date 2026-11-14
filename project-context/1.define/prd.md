# Product Requirements Document (PRD) — Entrepreneur Peers, Circles & Events

## Context & Instructions
PRD v1 produced by `@product-mgr` `*create-prd`. It replaces the owner draft `PRD-v0.md` as the authoritative product contract for the capstone MVP; PRD-v0 stays as a source. Requirement IDs (MD-*, MN-*, MC-*, MP-*, FR-*, NFR-*, AC-*) refer to `system-description.md`, which holds the full testable constraints. This PRD does not select an application pattern or a set of runtime agents; that is the SAD Pattern Decision (`@system.arch`).
**Status:** PRD v1.1 (2026-11-14: adds onboarding and the AI profile assistant). An MVP contract for a capstone that uses synthetic data only. It does not approve a real-user launch.

## Input Requirements

**Deep Research Report / MRD**: `project-context/1.define/mrd.md` (discovery-stage; no external research; quantitative market fields unknown)
**System Description** (optional): `project-context/1.define/system-description.md`
**System Concept**: A responsive web app that helps entrepreneurs turn an in-person event into lasting peer connections and ongoing support circles. It has an opt-in directory, a discovery tool with AI-suggested matches, private connections with mutual consent, circles, and events that an admin approves before they go live. It starts with a faith-centred entrepreneur community in Hong Kong and is open to all entrepreneurs, with faith optional.
**Selected Runtime**: crewai

## PRD Structure — Generate All Sections Below

### 1. Executive Summary

**Problem Statement** (Research-backed when MRD exists):

* Entrepreneurs who meet at in-person gatherings often leave without a way to reconnect. Following up after an event is "not typical", although repeat events build familiarity (organiser report, MRD-v0 §2). People who want ongoing support have no clear way into a lasting peer group (MRD hypothesis H1, H3).
* Quantified impact: **not available**. The evidence is qualitative organiser reports; no funnel or survey data exists (mrd.md Dimension 1).
* Scope: Hong Kong entrepreneurs. The beachhead is an existing faith-centred (Christian) entrepreneur community, and the product expands to all entrepreneurs at three stages: seasoned, new, and thinking about starting.

**Solution Overview** (Evidence-based):

* Private reconnection scoped to an event, with nothing visible by default; AI-suggested peers and circles with stated reasons; a path from a one-off event into ongoing circles; events published only after an admin approves them.
* Differentiators (hypotheses, untested): mutual consent at every step instead of exposing attendee lists; the link from events to circles; a faith-friendly setting where faith is optional, never a gate.
* Expected outcome for the capstone: an end-to-end demonstration on synthetic data in which the privacy boundaries are proven by tests and the AI suggestions are proven by evals. No demand outcome is claimed.

**Strategic Rationale**:

* Reconnection with consent tackles the reported gap without asking people to leave WhatsApp or LinkedIn for their conversations.
* Business case: **N/A for the capstone**. Its value is learning and a reversible prototype (MRD-v0 §8); monetisation is unknown (OQ-M05).
* Positioning: start where the operator has trust and access (the HK faith-centred community), then widen. A competitor audit is not done (OQ-M01).

### 2. Market Context & User Analysis

**Target Market / Users** (From Research or System Description):

* **Participant — seasoned entrepreneur**: looking for peers to give and receive support; may facilitate circles.
* **Participant — new entrepreneur**: looking for peers at a similar stage and for ongoing encouragement.
* **Participant — thinking of starting**: exploring; wants low-pressure access to people further along.
  All participants can set an optional, self-described faith context and choose whether matching may use it.
* **Organiser**: a user the admin has granted the role. Drafts events, assigns co-hosts and confirms attendance.
* **Admin**: approves or rejects every event; curates the venue directory; receives reports; grants roles.
* **Circle facilitator**: manages a circle's details, admissions and member-list visibility. Creation rights are open (OQ-04).
* Segment size and growth: **unknown** (mrd.md). Geography: Hong Kong first; expansion is not yet defined (OQ-M03).

**User Needs Analysis**:

* Pain points (hypotheses): missed contact exchange; wanting familiar, ongoing support; wanting connections that fit shared challenges and practical preferences.
* Journey: admin approves event → register → attend (organiser confirms) → opt in → see event peers and AI suggestions → request → mutual accept → mutual contact share → optional follow-up report → discover and join a circle.
* Adoption barriers: privacy concern, low perceived need, reluctance to adopt another app, unwanted approaches. Enablers: an existing trusted community and repeat events.

**Competitive Landscape** (optional when MRD skipped):

* Alternatives in use today: WhatsApp private messages, LinkedIn or contact exchange, organiser records and manual counts, recurring coffee meetups.
* Inspiration only, not audited: Luma, Meetup, Timeleft, Lectures After Dark.
* Pricing benchmarks: N/A for the capstone.

### 3. Technical Requirements & Architecture

**Discovery constraints** (from system description when present):

* **Must do** (all tagged requirement except MD-017, which is an assumption): profile with stage (MD-001); opt-in directory (MD-002); event-scoped reconnection (MD-003); filter discovery (MD-004); AI suggestions where the user decides (MD-005); private requests (MD-006); mutual, revocable contact sharing (MD-007); block and report (MD-008); circles with an admission policy (MD-009); optional faith-tagged circles (MD-010); admin event gate (MD-011); registration, confirmation and attendance kept separate (MD-012); co-hosts (MD-013); curated venue directory (MD-014); follow-up self-report (MD-015); funnel metrics in separate units (MD-016); synthetic seed data (MD-017, assumption).
* **Must not** (all requirement): no automatic directory entry (MN-001); no automatic contact disclosure (MN-002); the AI has no write actions (MN-003); no faith inference, and faith used only with the user's opt-in (MN-004); no unapproved event visible (MN-005); association grants no access to private pair data (MN-006); registration is not attendance and not membership (MN-007); no real users or outreach (MN-008); no booking or payments (MN-009); no invented venues (MN-010); server-side authorization (MN-011); no sensitive disclosures required (MN-012); the profile assistant never saves by itself (MN-013), never infers faith or sensitive attributes or invents facts (MN-014); raw free text stays private and never reaches the suggestion model (MN-015); onboarding never gates consent features (MN-016).
* **Must cost** (assumptions except MC-005): AI runs on demand only (MC-001); bounded model use, with one kickoff per request, `max_iter` ≤ 12 and ≤ 50 candidates (MC-002); p95 ≤ 15 s proposed (MC-003); spend and rpm cap set before evals (MC-004); degraded mode keeps discovery usable (MC-005, requirement); one profile-assistant call per "summarise" action, proposed ≤ US$0.01, within the US$20 total (MC-006). Spend cap confirmed 2026-11-14: US$20 total, ≤ US$0.05 per suggestion request.
* **Must prove** (requirement except MP-006): access boundaries pass tests (MP-001); admin gate works and leaves a record (MP-002); AI eval passes (MP-003); end-to-end journey (MP-004); funnel metrics correct (MP-005); no demand claim (MP-006, assumption); profile assistant faithful and safe (MP-007).
* Feasibility notes for the architect: most behaviour is deterministic, access-controlled CRUD. The only model-backed capability is suggestion ranking and explanation (FR-005). The evaluation and controls should centre on data visibility and authorization. Whether suggestions need more than one agent is the architect's decision.

**Runtime constraints** (aligned with Selected Runtime):

* The AI component reads only a pre-filtered set of eligible candidates (opted in, not self, not blocked, capped). It has no tools that write to the database or call outside services (MN-003). Faith fields are excluded from model input unless the user has opted them into matching (MN-004).
* Data minimisation: model input carries only the profile fields matching needs; contact fields are never in model input. Prompt traces are logged under `project-context/2.build/logs`, using synthetic data only.
* CrewAI adapter controls to apply after the pattern is chosen: agents and tasks in YAML under `config/`; sequential process; `allow_delegation=false`; `max_iter` ≤ 12; `max_retry_limit` ≥ 2; crew-level `max_rpm`; `max_execution_time` matched to MC-003; memory=False; low temperature; a `Task.guardrail` that checks that every suggestion is eligible and its reason is grounded before results are returned.

**Integration Requirements**:

* External APIs and services: **none in the MVP** apart from the LLM provider used by the runtime. No calendar, messaging, payment, booking, Luma or Meetup integration.
* Storage: a persistent store with relational integrity across users, profiles, consents, requests, contact shares, blocks, reports, circles, memberships, events, hosts, registrations, attendance, venues, approvals, follow-ups and suggestion logs. The draft PRD suggested a relational model; the final choice is the SAD's.
* Authentication: a synthetic login (pick a seeded persona) that sets a server-side session. The actor always comes from the session, never from client input (MN-011, NFR-001). Production authentication is deferred.
* Performance: suggestions p95 ≤ 15 s (confirmed 2026-11-14); non-AI pages respond interactively on the synthetic dataset. Scalability is not a capstone driver.

**Infrastructure Specifications**:

* Hosting: the smallest target that fits the MVP (a single service or a compose stack), chosen in the SAD and deploy.md.
* Compute: modest; dominated by LLM calls, which are capped (MC-002, MC-004).
* Network and security: secrets only in environment variables (`.env.example` names); no public exposure of real data, since there is none.
* Monitoring: funnel metrics (MD-016); AI prompt traces, latency, cost per request and guardrail outcomes (NFR-006).

### 4. Functional Requirements

**Core Features** (Priority P0):

* **Profile and stage** (FR-001, FR-021): *As a participant, I can create a minimal profile with my entrepreneur stage and optional details, so that others can find me if I choose.* Acceptance: the stage is required and limited to three values; no sensitive fields exist (MN-012); faith is optional and has its own matching opt-in.
* **Opt-in directory** (FR-002): *As a participant, I can choose to be listed in the directory.* Acceptance: AC-001.
* **Event reconnection** (FR-003): *As an attendee of an ended event, I can opt in to see other opted-in attendees of that event.* Acceptance: AC-002.
* **Discovery filters** (FR-004): *As a participant, I can filter people and circles by stage, interests and challenges, area and meeting preference.* Acceptance: results honour opt-in and blocks (AC-001, AC-005).
* **AI match suggestions** (FR-005): *As a participant, I can ask for suggested peers and circles and see why each was suggested, then decide what to do.* Acceptance: AC-007, AC-008, AC-009, and the eval gate AC-015.
* **Connection requests** (FR-006): *As a participant, I can send, withdraw, accept or decline private requests.* Acceptance: AC-003; duplicate and reverse requests are deduplicated and never auto-accepted.
* **Contact sharing** (FR-007): *As a connected pair, we each choose whether to share contacts, and either of us can revoke.* Acceptance: AC-004.
* **Block and report** (FR-008): *As a participant, I can block someone or report them to the admin.* Acceptance: AC-005; a report is visible in the admin view.
* **Circles** (FR-009): *As a participant, I can find circles, join them or request to join according to policy, and leave at any time.* Acceptance: AC-011, AC-010.
* **Event submission and admin approval** (FR-012, FR-013, FR-014): *As an organiser, I submit a draft event; as the admin, I approve or reject it; only approved events are visible.* Acceptance: AC-006.
* **Registration and attendance** (FR-015): *As a participant, I can register and withdraw; as an organiser, I confirm who attended.* Acceptance: AC-002, MN-007.
* **Synthetic seed data and persona login** (FR-021): the seed covers every stage, an approved and a pending event, a faith-tagged and a general circle, and blocked and declined cases. Acceptance: AC-014 runs on it.
* **Onboarding** (FR-022): *As a new participant, I get a short guided start (name and stage → what I'm looking for → interests and challenges → discovery choice) and can skip anything optional.* Acceptance: AC-016.
* **AI profile assistant** (FR-023): *As a participant, I can describe myself in my own words and get a structured draft (tags and a one-line summary) that I edit, accept or discard.* Acceptance: AC-017, AC-018; eval MP-007.
* **Field visibility** (FR-024): *As a participant, I choose per field whether it is shown on my profile or used for matching only.* *Matching only* fields are seen by the suggestion model, the admin, and facilitators of a circle I belong to or have applied to; every staff view is logged, and this is explained when I make the choice. Acceptance: AC-019, AC-020. Permitted matching fields are listed in MD-021 (OQ-03 resolved); staff access is defined in MD-022 (OQ-11 resolved).

**Enhanced Features** (Priority P1, in MVP scope as Should):

* Circle facilitator management (FR-010); faith-context circle tag and filter (FR-011); co-host assignment (FR-016); optional link from an event to a circle (FR-017); curated venue directory with "Unknown" fields (FR-018, AC-012); follow-up self-report (FR-019, AC-013); funnel metrics view labelled synthetic (FR-020).

**Future Features** (Priority P2):

* A real-user pilot, with production authentication, consent wording, retention and deletion, and a defined process for responding to reports (PRD-v0 S01, S09, S10).
* Venue booking requests, reservations, payments, refunds; user-submitted venues.
* Built-in chat; email, SMS or WhatsApp notifications; promotional communications.
* Luma, Meetup and social connectors (subject to verified APIs).
* Recurring events and circles; waitlists and capacity allocation.
* Business coaching and mentorship; richer formats (dinners, lectures, blind networking).
* Native mobile apps.

### 5. Non-Functional Requirements

**Performance Requirements**:

* AI suggestions: p95 ≤ 15 s with a visible loading state (MC-003).
* Non-AI interactions: interactive on the synthetic dataset; no formal throughput target.
* Availability: demo-grade; no uptime target for the capstone.

**Security & Compliance**:

* Server-side authorization on every read and write, with the actor taken from the session (NFR-001, MN-011).
* Field-level response filtering: contact data and private pair data are never sent to clients without authorization (NFR-002).
* Faith is voluntary, self-described, never inferred or verified (MN-004). Locations are coarse only (MN-012).
* Admin decisions and reports are logged with actor and timestamp (NFR-008).
* Compliance: N/A for synthetic data. Personal-data obligations are a gate before a real-user pilot (system-description §2).

**Scalability & Reliability**:

* Scaling is deferred; the candidate cap and on-demand calls bound the AI load.
* If a suggestion fails, times out or exceeds the budget, the user gets a clear message and filter discovery keeps working (MC-005, AC-009).

### 6. User Experience Design

**Interface Requirements**:

* A responsive web app for phone and desktop widths, meeting WCAG 2.1 AA as a baseline (NFR-007).
* Main areas: Directory, Discover (filters plus "Suggest"), Connections (requests, contacts), Circles, Events, and an Admin area (event approval queue, reports, venues, roles).
* Visual direction and components belong to `@ux.designer` (`ux.md`).

**Human–system interaction**:

* Every consequential action (request, accept, share contact, join, publish) is an explicit human action. The AI only suggests.
* Every flow has empty, loading and error states. Declines stay private according to policy (OQ-06).
* Explainability: each suggestion shows the shared fields it relied on. AI suggestions are clearly labelled, and synthetic data and self-reports are labelled (NFR-009).

### 7. Success Metrics & KPIs

**Business / Operational Metrics**:

* Capstone: the end-to-end journey (MP-004) passes and the funnel metrics (MD-016) compute correctly on seed data. No demand or growth targets are set (MRD-v0 §8, MP-006).
* Funnel units for a future pilot: opportunities offered, opt-ins, requests, acceptances, and pairs reporting a first and second catch-up. Each is reported with its counts and denominators; thresholds are open.

**Technical Metrics**:

* 100% of privacy and access tests pass (MP-001, MP-002).
* AI eval (MP-003): 100% of suggestions eligible; 100% of reasons grounded; 0 faith reasons without opt-in; relevance against the gold set ≥ 80% agreement with the hand-labelled synthetic gold set (OQ-02 resolved).
* Cost: per-request and total spend within the cap (MC-004); suggestion latency p95 within target (MC-003).

**User Experience Metrics**:

* Task completion in the scripted journey, with no dead ends; empty and error states present for every flow. Real satisfaction measurement is deferred to a pilot.

### 8. Implementation Strategy

**Development Phases**:

* Phase 1 (Define): system-description ✓, MRD ✓, PRD (this document) → user stories → SAD with its five decisions (`@system.arch`) → `ux.md` (`@ux.designer`).
* Phase 2 (Build): Setup → backend (domain, authorization, crew) → frontend → integration → QA → evals → security assessment.
* Phase 3 (Deliver): deploy configs, CI, runbook, user guide. No live deploy without operator authorization.

**Resource Requirements**: one operator-learner with AAMAD personas. Spend cap: US$20 total, ≤ US$0.05 per suggestion request. The deadline is open (OQ-08).

**Risk Mitigation**: privacy boundaries are built and tested first; the AI is added on top of a working filter baseline; the eval gate comes before release. The manual demand experiment runs separately and is not done by agents (mrd.md recommendations).

### 9. Launch & Go-to-Market Strategy

* Capstone: a demo only, on synthetic data. No public launch.
* After the capstone, conditional on evidence: run the owner-led manual reconnection experiment at an HK gathering (MRD-v0 §5); if it shows voluntary opt-in and mutual value, consider a real-user pilot with the HK faith-centred community once the P2 safeguards are in place; then open to all entrepreneurs (trigger is OQ-M03).

## Quality Assurance Checklist

- [x] Requirements traceable to MRD, system description, or recorded Assumptions
- [x] Technical specifications feasible with the selected runtime adapter
- [x] Success metrics aligned with stated objectives
- [x] MVP vs Future Work boundaries explicit
- [x] Market sections marked N/A when MRD was intentionally skipped (MRD not skipped; unknown market data is marked unknown)

## Sources

- `project-context/1.define/system-description.md` (2026-11-10): all MD, MN, MC, MP, FR, NFR and AC IDs.
- `project-context/1.define/mrd.md` (2026-11-10): beachhead, hypotheses, risks, recommendations.
- `project-context/1.define/PRD-v0.md` (owner draft, 2026-11-08): roles, journeys, safeguards S01–S10, funnel contract, scenarios T01–T12, roadmap.
- `project-context/1.define/MRD-v0.md` (owner draft, 2026-11-08).
- Operator direction, 2026-11-10: brief, elicitation answers, and the beachhead decision.
- `.claude/rules/adapter-crewai.md`; `aamad.config.yml`.

## Assumptions

- The onboarding and profile-assistant answers given by the operator on 2026-11-14 are recorded in system-description.md (MD-018 to MD-021) and supersede the US-002 "form only" profile entry.

- PRD-v0 is superseded on these points: audience (all entrepreneurs, faith optional), the admin event gate (added), venue booking (deferred), AI suggestions (now in the MVP, where PRD-v0 put AI after a baseline), and data (synthetic only).
- The filter-discovery baseline in FR-004 satisfies PRD-v0's "non-AI baseline first" intent; FR-005 is built on top of it.
- Organiser-confirmed attendance makes someone eligible to reconnect for the synthetic MVP; it must be revisited before a pilot.
- Circle creation is limited to the admin and facilitators the admin appoints, pending OQ-04.
- The MC-002 and MC-003 values are proposed defaults.

## Open Questions

- OQ-04 Circle creation rights, default admission policy, capacity, facilitator powers.
- OQ-05 Whether events are public without login or invite-only.
- OQ-06 Request expiry and retry, and what the sender sees after a decline.
- OQ-07 Circle success criterion.
- OQ-08 Capstone deadline and demo format.
- OQ-10 Admin actions available on a report.
- OQ-M01 External market and competitor research.
- OQ-M03 The trigger for moving from the beachhead to all entrepreneurs.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-prd` — output: `project-context/1.define/prd.md` — runtime resolved: `crewai` (env `AAMAD_TARGET_RUNTIME`, matches `aamad.config.yml`) — mode: greenfield — no application pattern or agent roster prescribed — Prompt Trace omitted: this is a Define-phase artifact.
- 2026-11-14 — persona: `product-mgr` — action: `*create-prd` (v1.1 update) — added FR-022 to FR-024 (onboarding, AI profile assistant, field visibility); resolved OQ-01, OQ-02 and OQ-03; added OQ-11 — runtime resolved: `crewai`.
- 2026-11-14 — persona: `product-mgr` — action: `*create-prd` (v1.1 update) — OQ-11 resolved: staff access to *matching only* fields for the admin and own-circle facilitators, with logging and disclosure (MD-022, AC-020).
