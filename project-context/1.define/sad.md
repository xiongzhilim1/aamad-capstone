# System Architecture Document (SAD) — Entrepreneur Peers, Circles & Events

## Context & Instructions
Greenfield SAD produced by `@system.arch`, built step by step with the operator. **Status: working draft, steps 1–3 of 4 complete** (`*decompose-work`, `*select-pattern`, `*define-controls`), updated 2026-11-14 for the AI profile assistant (PRD v1.1). Sections marked *Pending* are filled by later steps: `*select-pattern` → `*define-controls` → `*create-sad` + `*define-eval-criteria`.
This is the blueprint for Build-phase personas. Work ownership and the pattern decision come before any runtime roles; the app is not assumed to be a multi-agent crew or a chat interface.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md`
**MRD** (optional): `project-context/1.define/mrd.md`
**System Description** (when present): `project-context/1.define/system-description.md`
**User Stories** (when present): `project-context/1.define/user-stories/` (US-001 to US-024)
**MVP Scope**: the synthetic-data capstone. Must stories US-001 to US-015 make up the core journey; Should stories US-016 to US-022 follow if time allows.
**Selected Runtime**: crewai

## System Architecture Specification — Generate All Sections

### Work Ownership

Lens: a model's output is **probabilistic**, it has a **knowledge cutoff**, its **working memory is limited**, and it is only partly **steerable**. A step goes to the model only when variation in its output is tolerable, the step needs no live facts beyond what we pass in, the input fits a bounded context, and the output can be checked. Every rule, permission and live record stays in app code (the "existing system" for a greenfield build is the app's own backend and database).

| Step | Owner (model / existing system / human / collaborative) | Reversibility | Stakes | Accountable party | Rationale |
|------|----------------------------------------------------------|---------------|--------|-------------------|-----------|
| W01 Log in as a synthetic persona (US-001) | existing system | Reversible | Medium: the identity behind every authorization check | Builder (backend) | Deterministic session issuance; the actor must come from the server (MN-011) |
| W02 Create or edit profile, set faith matching opt-in (US-002) | human | Reversible | Medium: self-disclosure | Participant | Only the person can describe themselves; the system validates the stage value and blocks sensitive fields (MN-012) |
| W03 Set directory or event-reconnection consent (US-003, US-004) | human | Reversible | High: controls who can see me | Participant | Consent cannot be inferred or delegated (MN-001) |
| W04 Enforce visibility (directory, filters, reconnection lists) | existing system | Reversible | High: a privacy leak cannot be undone | Builder (backend) | Pure rules over live consent, block and attendance records; must be exact, not probabilistic |
| W05 Filter-based discovery (US-005) | existing system | Reversible | Low | Builder | Deterministic query; it is also the fallback when AI is unavailable (MC-005) |
| W06 Choose which candidates the AI may see | existing system | Reversible | High: decides what data reaches the model | Builder (backend) | Eligibility (opted in, not self, not blocked, capped at 50, minimised fields, faith only with the user's opt-in) is a rule, not a judgement, and the model must never be its own gatekeeper (MN-004, MC-002) |
| W07 Rank candidates and write a reason for each (US-006) | **collaborative**: the model drafts, the participant decides | Reversible: only a list on screen | Low to medium: bad suggestions waste time; a misleading reason could erode trust | Participant (decides); builder (eval gate) | The only step that needs judgement over fuzzy text (interests, challenges); variation is tolerable because a human decides and an eval measures quality (MP-003) |
| W08 Check each suggestion is grounded and eligible before display | existing system | Reversible | Medium | Builder | A deterministic check that each cited field really exists on both profiles and each id is in the W06 set; it catches model errors (AC-007, AC-008) |
| W09 Send or withdraw a connection request (US-007) | human | Reversible (withdraw) | Medium: unwanted approaches | Sender | A social act; the AI has no write path (MN-003) |
| W10 Accept or decline a request (US-008) | human | Partly reversible (block later) | Medium | Recipient only | Consent belongs to the recipient (AC-003) |
| W11 Grant or revoke contact sharing (US-009) | human, both parties | **Irreversible once seen**: copied contacts cannot be recalled | High | Each participant | Highest-stakes consent in the product; both sides must grant it explicitly (MN-002) |
| W12 Block or report (US-010) | human; the admin reviews reports | Block is reversible; a report is a record | High: safety | Participant; admin | Safety decisions stay human; enforcement of a block is deterministic (W04) |
| W13 Draft and submit an event (US-012) | human (organiser) | Reversible until published | Medium | Organiser | Content and curation stay human-led (PRD-v0 §2) |
| W14 Approve or reject an event (US-013) | human (admin) | Reversible (unpublish), but exposure while live cannot be undone | High: public publication | Admin | The operator's human gate (MD-011); the AI never approves (MN-003) |
| W15 Enforce the publication gate (listing, detail, link, API) | existing system | n/a | High | Builder (backend) | No event is published without an approval record (AC-006) |
| W16 Register or withdraw; confirm attendance (US-014, US-015) | human (participant; organiser or co-host) | Reversible, and corrections are recorded | Medium: attendance gates reconnection | Participant; organiser | Attendance is a fact only a person present can assert; registration is never attendance (MN-007) |
| W17 Join or leave a circle; approve join requests (US-011, US-016) | human (participant; facilitator) | Reversible | Medium | Participant; facilitator | Policy is enforced by the system, decisions are made by humans |
| W18 Curate venues; tag faith-context circles (US-017, US-020) | human (admin or facilitator) | Reversible | Low | Admin | Unknown fields must stay "Unknown"; a model would invent values (MN-010) |
| W19 Follow-up self-report (US-021) | human | Reversible (edit); idempotent | Low | Pair members | It is a self-report by definition |
| W20 Compute funnel metrics (US-022) | existing system | Reversible | Medium: misleading numbers | Builder | Counting must be exact and auditable (MP-005); never model-generated |
| W21 Turn free text into drafted profile tags and a one-line summary (US-024) | **collaborative**: the model drafts, the participant edits, accepts or discards | Reversible: nothing is saved until accepted | Medium: a wrong or inferred tag (for example faith) misrepresents a person | Participant (accepts); builder (eval gate MP-007) | Summarising fuzzy free text is model work; variation is tolerable because the author reviews every field before it is saved (MN-013) |
| W22 Check the draft before display: tags trace to source words, no faith or sensitive tags, schema-valid | existing system | Reversible | Medium | Builder | Deterministic check, the same idea as W08 (MN-014) |
| W23 Save accepted fields with per-field visibility; delete raw text; enforce *matching only* | existing system | Raw-text deletion is irreversible by design | High: hidden fields must stay hidden | Builder (backend) | Visibility is a rule, so it lives in code (MD-020, MN-015) |

![Who owns each step on the suggestion path](../diagrams/system-arch/work-ownership.svg)

The editable source of this figure is `project-context/diagrams/system-arch/work-ownership.html`.

**Feasibility verdict**: `feasible with constraints`
**Load-bearing constraint**: the model owns exactly two steps, both drafts that a person reviews: W07 (rank and explain suggestions) and W21 (draft profile fields from the author's own free text). W07 receives only the candidate set the server has already filtered and minimised (W06). W21 sees only the author's own text, and its output is saved only when the author accepts it. Neither has a write path to any record. Every access, consent, publication and counting decision is deterministic code or a human decision. If this constraint is relaxed, for example by letting the model choose who is eligible, the privacy guarantees in MP-001 can no longer be proven by tests.

### Pattern Decision

The decision covers the two model-owned steps, W07 (suggestions) and W21 (profile assistant, added 2026-11-14). Everything else is ordinary application code and has no pattern to choose. W21 is assessed after the W07 table.

| Factor | Augmented call | Workflow | Agent |
|--------|----------------|----------|-------|
| Predictability | The path is fixed: filter → one call → check | Same path, with more model steps to vary | The model chooses its next step, which is unnecessary when the path is already known |
| Error cost | Low: a bad list is caught by W08 or ignored by the user | Low | Higher: tool calls can reach live data |
| Observability | One prompt, one response, one trace | Several traces per request | Variable-length traces |
| Latency (p95 ≤ 15 s, MC-003) | One round trip | Two or more round trips | Unbounded without caps |
| Cost (≤ US$0.05 per request, ≤ US$20 total) | One call | About 2× per request (evaluator-optimizer) | Several calls per request |

- **Primary shape**: `augmented call`
- **Workflow sub-shape** (when applicable): n/a
- **Deciding factor**: **predictability.** The path can be written out in full in advance: code filters the candidates (W06), one model call ranks them and writes reasons (W07), and code checks the result (W08). Because the path is fixed, an agent is ruled out on the first factor; agents are legal only when the path cannot be enumerated. Among the shapes that remain, a workflow adds a second model step whose only job would be to judge the first. W08 already does that deterministically, at no model cost, and more reliably. So a workflow adds cost and latency and nothing else.
- **"Augmented" means** the call receives everything it needs in its prompt: the viewer's minimised profile, at most 50 eligible people and at most 20 visible circles, all chosen by code. It returns structured output, a list of `{candidate_id, kind, reason, cited_fields[]}`, which is validated against a schema. It has no tools and no retrieval.
- **Peers and circles in one call**: both lists go into a single call, which fits the per-request cost cap. Splitting them into two parallel calls would make this a parallelization workflow and double the cost.
- **Retry**: one retry, only when the output fails schema validation. On a second failure, or on timeout or budget breach, the request falls back to filter discovery (MC-005).
- **Rejected alternatives and reversal cost**:
  - *Workflow, evaluator-optimizer* (a second model call that critiques and revises the first): rejected because it about doubles cost and latency, and the deterministic W08 check covers the failures that matter (eligibility, grounding, faith leakage). **Reversal cost: low.** It would mean adding one task to the crew config, with no data-model change. Reconsider if evals show reasons are grounded but unhelpful.
  - *Agent with tools* (the model queries profiles itself): rejected because it would let the model act as its own gatekeeper for who is eligible. That breaks the load-bearing constraint from Work Ownership, and the privacy tests (MP-001) could no longer prove the boundary. **Reversal cost: high.** The access-control and eval design would need to be redone.
  - *Embedding similarity with no LLM*: considered and kept only as a possible future cost optimisation. It cannot produce the human-readable reason that MD-005 requires.
- **Progression used**: prompt only → no tools and no retrieval → no evaluator-optimizer, because the deterministic check (W08) takes that role → fine-tuning not considered.
- **Runtime fit (crewai)**: the call is hosted as a CrewAI crew with **one agent, one task and no tools**, run sequentially with `allow_delegation=false`, `output_pydantic` for the schema, a `Task.guardrail` that runs the W08 checks, `max_iter` of 1–2 (a single call plus at most one schema retry), memory=False and low temperature. This keeps the adapter conventions (agents and tasks in YAML, externalised config) without implying a multi-agent design. Swapping CrewAI for a direct SDK call later would be a small change limited to one module.

**W21 profile assistant: also an `augmented call`.** The path is fixed: the author submits text, one call drafts `{interests[], challenges[], looking_for[], industry?, summary}` against the tag vocabulary, the W22 code check runs, and the author reviews. *Deciding factor: predictability*, the same as W07. It is a textbook extraction task with a human reviewer, so an agent or workflow adds nothing. It is hosted as a second one-agent, one-task, tool-free crew (`profile_assistant`), separate from the suggestion crew, so that each has its own prompt, eval (MP-007) and trace. Merging the two into one crew would make them a workflow and couple two failure modes. *Reversal cost: low.*

Agent-only fields (tool allowlist, turn budget, stop conditions): **n/a**, because the pattern is not agent. The equivalent bounds for this call are: no tools, at most 2 model invocations per request, and stop on valid output, a second schema failure, a timeout, or budget breach.

### Reference Architecture

![Suggestion request: one augmented call inside the server boundary](../diagrams/system-arch/reference-architecture.svg)

The editable source of this figure is `project-context/diagrams/system-arch/reference-architecture.html`.

- **Selected reference architecture**: **document pipeline**, which means structured extraction with an exception path. It is the closest proven shape: code assembles a bounded input, a single model call turns it into structured records (ranked suggestions with cited fields), the output is validated against a schema and checked for grounding, and anything failing goes to an exception path (dropped suggestions, or fallback to filter discovery).
- **Known failure this design prevents**: *no exception path.* Prevented by the W08 guardrail, which drops ungrounded or ineligible items, and by MC-005: filter discovery still works when the call fails, times out or exceeds budget.
- **Also explicitly avoided**: *retrieval used as a substitute for live state.* Consent, blocks and attendance change at any moment, so candidates come from a live database query at request time, never from a precomputed vector index of profiles. An index could serve a profile after its owner opted out.
- **W21 profile assistant** fits the document-pipeline shape even more directly: free text → structured fields → validation → human review as the exception path. The same known failure, *no exception path*, is prevented by W22 and by manual tag entry as the fallback (MC-006).
- **Second pattern**: none. Both model steps share one pattern and one reference architecture.

### Model and Context Strategy

- **Default model tier**: balanced. **Proposed: Claude Sonnet 5.5 (`claude-sonnet-5-5`) at `effort: low` for both crews, pending operator confirmation (OQ-A02).** Sizing per suggestion request, estimated (to be confirmed with token counting in Build): about 8.5K input tokens (system prompt about 1K, viewer about 0.2K, 50 people × about 120 tokens, 20 circles × about 60 tokens) and about 2.5K output tokens including thinking (top 10 suggestions, reasons ≤ 25 words each).

  | Model | Price in / out per 1M tokens | Est. cost per suggestion request | Fits ≤ US$0.05? |
  |-------|------------------------------|----------------------------------|-----------------|
  | Claude Haiku 5.5 (`claude-haiku-5-5`) | $0.10 / $0.50 | ≈ $0.002 | Yes, with wide margin; quality must be proven by MP-003 |
  | Claude Sonnet 5.5 (`claude-sonnet-5-5`) | $2.00 / $10.00 | ≈ $0.042 | Yes, but tight; output length must be bounded |
  | Claude Opus 5.5 (`claude-opus-5-5`) | $4.00 / $20.00 | ≈ $0.084 | **No**; would need the candidate cap cut to about 20, or a higher cap |

  Profile assistant (W21), estimated about 1K in and about 1.5K out: Sonnet 5.5 ≈ $0.017, Haiku 5.5 ≈ $0.001. The MC-006 proposal of ≤ US$0.01 holds only on Haiku 5.5, or on Sonnet 5.5 with output kept below about 0.8K tokens. Prices are list prices from the `claude-api` skill reference (cached 2026-10-06) and must be re-checked before Build.
- **Context strategy**: progressive. Each call gets only what its step needs, assembled by code at request time. There is no conversation history, no memory and no retrieval index.
- **Swap-as-release rule**: every change of model, effort level or prompt version is a release. It must re-run the relevant eval (MP-003 or MP-007) and meet these rollback criteria, written before the swap: roll back if relevance falls below 80% of gold-set agreement, if any eligibility, grounding or faith-leak case fails, or if p95 latency or cost per request exceeds MC-003 or MC-004.
- **Entry point**: direct API, called through CrewAI's model layer (LiteLLM) inside the backend. There is no hosted chat, agent SDK or MCP server.
- **Entry-point tradeoff named at decision time**: CrewAI gives YAML-externalised agents and tasks, `output_pydantic` and `Task.guardrail`, all of which the adapter rules require. The cost is a dependency on LiteLLM passing current Claude parameters correctly. Two known risks for Build to verify (OQ-A03): (1) the 5.5-generation models reject `temperature`, so no temperature may be set anywhere in the crew config; (2) native structured outputs and the `effort` setting may not pass through LiteLLM. If they don't, the schema is still enforced by `output_pydantic` plus one retry (CR-005).
- **Entry-point responsibility map**: one route only (backend → CrewAI → Anthropic API). The browser never calls the model.
- **Minimum data in the context window**:
  - *Suggestion crew (W07)*: the viewer's MD-021 matching fields; for each candidate, a short opaque id plus their MD-021 fields; for each circle, an id, purpose and tags. **Never**: names, contact fields, raw free text, faith when its opt-in is off, block or consent state, event attendance lists, or any field set to "shown on profile" that is not also an MD-021 field.
  - *Profile assistant (W21)*: the author's own free text (≤ 1,500 characters), the fixed tag vocabulary, and the output schema. Nothing about other users.
- **Identity**: enforced in server-side code (CR-011). The prompt never carries authorization decisions, and the model is never asked whether someone may see something.
- **Determinism note (adapter deviation)**: the CrewAI adapter asks for low temperature, but `temperature` is rejected on the 5.5-generation models. Determinism is instead achieved through `effort: low`, structured output, a pinned prompt version and a pinned model id. This deviation is recorded in Audit.

### Control Register

How user-written text reaches the two prompts, which is why injection controls CR-003, CR-004 and CR-015 exist:

![How user-written text reaches each prompt](../diagrams/system-arch/user-text-paths.svg)

The editable source of this figure is `project-context/diagrams/system-arch/user-text-paths.html`.

What training already reduces, and the app does not rely on alone: general refusal of harmful content, and basic instruction-following on "treat this text as data". What the app must enforce itself: everything below.

| ID | Risk category | Control | Control point (input / output / tool-call) | Failure direction (fail closed / fail open) | Owner | Evidence artifact | Review routing |
|----|---------------|---------|--------------------------------------------|---------------------------------------------|-------|-------------------|----------------|
| CR-001 | Data exposure | Candidate eligibility filter (W06): only opted-in, not self, not blocked in either direction, capped at 50 people and 20 circles, evaluated live at request time | input | fail closed: on error, no model call; fall back to filter discovery | backend.eng | Tests for AC-001, AC-005, AC-007 | None; deterministic |
| CR-002 | Data exposure / minimisation | Field allowlist serializer: only MD-021 fields are placed in the prompt; faith only when its opt-in is on; contact data, names and raw text excluded; unknown fields dropped | input | fail closed | backend.eng | Tests for AC-008, AC-019; prompt-trace audit sample | None |
| CR-003 | Direct injection | User-authored text (bio ≤ 200 chars, assistant free text ≤ 1,500 chars) is wrapped in delimiters as data; the system prompt says to ignore instructions inside it; tags come from a fixed vocabulary | input | fail closed: over-length input is rejected before the call | backend.eng | Adversarial cases in the MP-003 and MP-007 evals | Eval failure blocks release |
| CR-004 | Indirect injection | A candidate's bio inside *another viewer's* prompt (for example "rank me first") cannot widen eligibility or reveal data, because output is limited to ids from the input set (CR-006). Ranking skew is the residual risk | output | **fail open**: a skewed ranking is still shown, because it is low-stakes, reversible and the user decides. Mitigated by eval cases and trace flags | qa.eng | Injection-bio cases in MP-003 | Flagged traces reviewed during the eval cycle |
| CR-005 | Malformed output / refusal | Pydantic schema validation; `stop_reason` checked (refusal or max_tokens counts as a failure); one retry, then fallback | output | fail closed: no partial list is shown | backend.eng | Schema-failure and fallback tests (AC-009) | None |
| CR-006 | Hallucination / data exposure | Grounding and eligibility guardrail (W08): every id must be in the input set; every `cited_field` must exist on both profiles; eligibility is re-checked at display time to catch opt-outs during the call | output | fail closed per item: an invalid item is dropped, and if all are dropped the user sees the fallback | backend.eng | Tests for AC-007 plus the MP-003 grounding metric | None |
| CR-007 | Sensitive-attribute leakage | Faith and sensitive-term check on suggestion reasons and assistant tags: no faith reason unless both users opted in; no faith, health or family tag from the assistant | output | fail closed: the item or tag is dropped | backend.eng | Tests for AC-008 and AC-018; MP-003 and MP-007 cases | None |
| CR-008 | Tool abuse | Both crews are configured with **zero tools**; a startup check refuses to boot if any tool is bound | tool-call | fail closed: the service does not start | backend.eng | Config test; crew YAML review | None |
| CR-009 | Unauthorised side effect | Model output is never written to profile, request, membership or event tables. Assistant drafts live only in the user's session until they accept; suggestions are not persisted except in trace logs | tool-call (side effect) | fail closed | backend.eng | Tests for MN-003, MN-013, AC-017 | The user reviews every draft |
| CR-010 | Token-budget exhaustion / cost | Input caps (CR-001, CR-003); `max_tokens` cap per call; per-user limit (proposed: 10 suggest and 10 summarise actions per hour); a global spend counter switches AI off at US$20 | input | fail closed: AI off, fallback on, a clear message to the user | backend.eng / devops.eng | Spend log; rate-limit test | Operator alerted when the breaker trips |
| CR-011 | Identity spoofing | The actor comes from the server session; client-supplied ids are ignored; the prompt never makes authorization decisions | input | fail closed | backend.eng | Test for MN-011 (forged actor id) | None |
| CR-012 | Fairness injection points | *Prompt framing*: no ranking by stage seniority, industry prestige or faith; *examples*: balanced across stages and industries; *corpus*: the synthetic gold set covers all three stages and is modelled on public patterns (OQ-A01); *routing*: not applicable, one route | input / output | n/a; measured, not gated per request | qa.eng | MP-003 results broken down by stage and by faith opt-in | An eval disparity above threshold blocks release (threshold in `*define-eval-criteria`) |
| CR-013 | Decision log | Every model call logs trace id, prompt version, model id, effort, input candidate ids (not content), output ids, dropped items with reasons, tokens, cost and latency | output | **fail open**: a logging failure does not block the user, but it raises an alert | backend.eng | `project-context/2.build/logs` traces | Used to reconstruct any suggestion |
| CR-015 | Data exposure via reason text | A candidate's *matching only* fields may influence ranking but must never appear in the reason shown to the viewer. The prompt splits each candidate into `citable` (shown-on-profile) and `rank_only` (matching-only) groups; the validator requires `cited_fields` ⊆ citable fields on both profiles, and drops any reason containing a `rank_only` tag value | output | fail closed per item | backend.eng | Test for AC-019 extended to reason text; MP-003 leak cases (paraphrase leakage is a residual risk, eval-gated) | Eval failure blocks release |
| CR-016 | Staff access to *matching only* fields | A server-side scope check: the admin can see all; a facilitator only for members and pending applicants of their own circle; organisers and other participants never. Every staff view writes an access-log entry (viewer, subject, fields, time) | tool-call (data read) | fail closed: on scope or log failure the fields are not returned | backend.eng | Tests for AC-020, including a forged circle id and an organiser attempt | Admin can review the access log; unusual facilitator access is flagged |
| CR-014 | Unapproved publication (human gate) | An event moves to published only with an admin approval record; enforced in the API, not only the UI | tool-call (side effect) | fail closed | backend.eng | Test for AC-006 | **Every** event goes to the admin, who sees the full event and the organiser |

![Where each control is enforced on a model request](../diagrams/system-arch/control-layers.svg)

The editable source of this figure is `project-context/diagrams/system-arch/control-layers.html`.

Review routing summary: suggestions have no queue, because they are reversible and low-cost and the user is the reviewer. Every profile-assistant draft is reviewed by its author. Every event is reviewed by the admin, because publication is high-stakes. User reports go to the admin with the reporter's reason attached.

### Production Shape

- **Volume**: the *capstone* volume is a handful of synthetic users, and the main spend is evals. The estimate is about US$6–10 of the US$20 cap on Sonnet 5.5: roughly 30 gold cases × 5 iterations × 2 crews. The *expected* volume for a possible beachhead pilot (not approved) is about 100 participants × 2 suggestion requests a week ≈ 200 requests a week, or ≈ US$8.40 a week on Sonnet 5.5 and ≈ US$0.40 a week on Haiku 5.5. The spend breaker (CR-010) must be re-set before any pilot.
- **Latency**: the p95 target is ≤ 15 s (MC-003). The main driver is output length, so the design keeps output to 10 suggestions with reasons of ≤ 25 words at `effort: low`, and the UI shows a loading state. p95 must be measured in Build; if it misses the target, reduce the output length before changing the model.
- **Retries, fallback chain, circuit breaker**: the SDK or LiteLLM retries 429, 5xx and connection errors with backoff (at most 2 retries); one schema retry (CR-005); overall timeout of 20 s per request. Fallback chain: AI suggestions → filter discovery (suggestions) and AI draft → manual tag entry (assistant). Circuit breaker: 5 consecutive model failures within 5 minutes switch the AI off for 10 minutes. The spend breaker switches it off at US$20.
- **Failure mode specific to this architecture (document pipeline)**: *structurally valid but wrong output*, meaning invented ids, invented shared fields or stale eligibility. Mitigation: CR-006, including the display-time re-check for someone who opts out while the call is running.
- **Per-request traces versus aggregate dashboards**: per-request trace records (CR-013) answer "why did this person see this suggestion?". They are stored as JSON lines under `project-context/2.build/logs` for the capstone. A separate aggregate view answers "is the system healthy?": daily spend versus cap, p95 latency, fallback rate, schema-failure rate, dropped-item rate by reason, and assistant accept/edit/discard rates. The aggregate view is built from the traces and never shows profile content.

### 1. MVP Architecture Philosophy & Principles
*Pending — step 4 `*create-sad`.*

### 2. Application Runtime Specification
*Pending — step 4.*

### 3. Frontend Architecture Specification
*Pending — step 4.*

### 4. Backend Architecture Specification
*Pending — step 4.*

### 5. DevOps & Deployment Architecture
*Pending — step 4.*

### 6. Data Flow & Integration Architecture
*Pending — step 4.*

### 7. Performance & Scalability Specifications
*Pending — step 4.*

### 8. Security & Compliance Architecture
*Pending — step 4.*

### 9. Testing & Quality Assurance Specifications
*Pending — step 4 and `*define-eval-criteria`.*

### 10. MVP Launch & Feedback Strategy
*Pending — step 4.*

## Implementation Guidance for AI Development Agents
*Pending — step 4.*

## Architecture Validation Checklist
*Pending — step 4.*

## Sources

- `project-context/1.define/prd.md`, `system-description.md`, `mrd.md`, `user-stories/US-001` to `US-022` (2026-11-10).
- Operator decisions, 2026-11-14: OQ-01 spend cap of US$20 total and at most US$0.05 per suggestion request; OQ-02 eval relevance threshold of 80% agreement with a hand-labelled set of realistic synthetic profiles.

## Assumptions

- The OQ-01 and OQ-02 answers above are recorded here and will be applied in steps 3 and 4. `system-description.md` is a product-mgr artifact and is not edited by this persona; its OQ-01 and OQ-02 entries remain open there until `@product-mgr` syncs them.

## Open Questions

- ~~**OQ-A01** Gold-set provenance.~~ Resolved 2026-11-14 by the operator: synthetic profiles are modelled on public, aggregate patterns (roles, industries, stages, challenges among HK entrepreneurs) and are never copied or scraped from identifiable individuals (MN-008).
- Operator confirmed 2026-11-14 that W07 is the only model-owned step; event approval stays purely human.
- ~~**OQ-A02** Model choice.~~ Resolved 2026-11-14 by the operator: Claude Sonnet 5.5 for both crews; Claude Haiku 5.5 is run through the same evals as a challenger, and the operator switches if it passes. OpenRouter or other providers are deferred: a later swap is a config change under the swap-as-release rule, but the data-processing terms of any new provider must be reviewed first.
- **OQ-A03** Build must verify that CrewAI/LiteLLM can call the 5.5-generation models without sending `temperature`, and whether it passes structured outputs and `effort`; if not, rely on `output_pydantic` plus a retry.
- ~~**OQ-A04** Per-user rate limit.~~ Accepted 2026-11-14: 10 suggest and 10 summarise actions per hour. **Review trigger**: revisit if the rate-limit hit rate exceeds 5% of sessions in the aggregate view.
- ~~**OQ-11**~~ Resolved 2026-11-14: *matching only* fields are visible to the suggestion model, the admin, and own-circle facilitators (MD-022). This is enforced by CR-016. CR-002 and CR-015 are unchanged, because they govern the model and other participants.

## Audit

- 2026-11-14 — persona: `system-arch` — action: `*decompose-work` — output: `project-context/1.define/sad.md` (Work Ownership, feasibility verdict) — runtime resolved: `crewai` (env `AAMAD_TARGET_RUNTIME`, matches `aamad.config.yml`) — mode: greenfield.
- 2026-11-14 — persona: `system-arch` — action: `*draw-diagram` — files: `project-context/diagrams/system-arch/work-ownership.html`, `work-ownership.svg` — type: architecture (three ownership zones) — `diagram-design` commit `0b9b10cab3dbf695642fa1a6c4b4f60df9083689` — self_check OK. Visual render was not checked in a browser in this session (file:// blocked).
- 2026-11-14 — persona: `system-arch` — action: record operator decisions — OQ-A01 resolved (synthetic profiles modelled on public patterns); W07 confirmed as the only model-owned step.
- 2026-11-14 — persona: `system-arch` — action: `*select-pattern` — Pattern Decision: augmented call, hosted as a one-agent, one-task, tool-free CrewAI crew; Reference Architecture: document pipeline — runtime resolved: `crewai`.
- 2026-11-14 — persona: `system-arch` — action: `*draw-diagram` — files: `project-context/diagrams/system-arch/reference-architecture.html`, `reference-architecture.svg` — type: architecture (server trust boundary) — `diagram-design` commit `0b9b10cab3dbf695642fa1a6c4b4f60df9083689` — self_check OK; not visually rendered in this session.
- 2026-11-14 — persona: `system-arch` — action: record operator decision — operator accepted the one-agent, one-task CrewAI crew; no multi-agent course requirement applies.
- 2026-11-14 — persona: `system-arch` — action: `*decompose-work` and `*select-pattern` (update) — added W21 to W23 for the AI profile assistant (PRD v1.1, US-024); W21 is a second augmented call, hosted as a separate one-agent, one-task crew; the work-ownership diagram has been redrawn.
- 2026-11-14 — persona: `system-arch` — action: `*define-controls` — filled Model and Context Strategy, Control Register (CR-001 to CR-016) and Production Shape — adapter deviation: no `temperature` (rejected by 5.5-generation models); determinism comes from `effort: low`, structured output, and pinned model and prompt versions — model choice left to the operator (OQ-A02) — prices from the claude-api skill reference cached 2026-10-06 — runtime resolved: `crewai`.
- 2026-11-14 — persona: `system-arch` — action: `*draw-diagram` — files: `project-context/diagrams/system-arch/control-layers.html`, `control-layers.svg` — type: layers (governance / control catalog pattern) — `diagram-design` commit `0b9b10cab3dbf695642fa1a6c4b4f60df9083689` — self_check OK; not visually rendered in this session.
- 2026-11-14 — persona: `system-arch` — action: `*define-controls` (update) — added CR-015 (matching-only fields must not leak through reason text); recorded operator decisions on OQ-A02 (Sonnet 5.5, with Haiku 5.5 as an eval challenger; OpenRouter deferred) and OQ-A04 (rate limit accepted, with a review trigger).
- 2026-11-14 — persona: `system-arch` — action: `*draw-diagram` — files: `project-context/diagrams/system-arch/user-text-paths.html`, `user-text-paths.svg` — type: architecture (two text paths into the prompts) — `diagram-design` commit `0b9b10cab3dbf695642fa1a6c4b4f60df9083689` — self_check OK; not visually rendered in this session.
- 2026-11-14 — persona: `system-arch` — action: `*define-controls` (update) — added CR-016 (staff access to *matching only* fields, scoped and logged) after OQ-11 was resolved.
