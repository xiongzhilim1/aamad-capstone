# System Description — Entrepreneur Peers, Circles & Events

## Context & Instructions
Structured project definition produced by `@product-mgr` `*elicit-requirements` before MRD/PRD generation.
Inputs: operator brief (2026-11-10), operator answers to four elicitation questions (2026-11-10), and owner drafts `MRD-v0.md` and `PRD-v0.md`. Where the drafts and the brief conflict, the operator's 2026-11-10 answers win; the drafts are treated as sources, not accepted requirements.
No application pattern is selected here; that belongs to `@system.arch`.

## Input Requirements

**Working title**: Entrepreneur Peers, Circles & Events (capstone)
**Author / stakeholder**: Sean Lim (operator / project owner)
**Selected Runtime** (optional at this stage): crewai (resolved from `AAMAD_TARGET_RUNTIME` and `aamad.config.yml`)

## System Description — Generate All Sections Below

### 1. Intent and Problem

- **Problem statement**: After an in-person entrepreneur gathering, attendees who want to stay in touch often leave without exchanging contacts, and there is no easy way to find ongoing groups (circles) for continued support and fellowship. The organiser currently tracks interest through private messages and manual counts (MRD-v0 §2, organiser report, not measured). Whether attendees actually want a tool for this is a hypothesis (MRD-v0 H1–H3), not a finding.
- **Primary users / operators**:
  - **Participants** at three stages: seasoned entrepreneurs, new entrepreneurs, and people thinking about starting. All are welcome; faith is optional (see Domain Context).
  - **Organisers**: invited users who draft and run events and assign co-hosts.
  - **Admin**: a platform role that approves or rejects every event before it is published (human gate).
  - **Circle facilitator**: manages a circle; who may create circles is open (OQ-04).
- **Success definition**: The capstone MVP shows, using made-up data only, the full journey: *attend an admin-approved event, opt in to reconnect, get AI-suggested peers, send and accept a connection request, share contacts by mutual consent, and find and join a circle*. Every privacy and access boundary in Must not do must pass automated tests, and the AI match suggestions must pass an eval gate. The capstone does not claim real-user demand.

### 2. Domain Context

- **Domain vocabulary and critical entities**
  - *Profile*: minimal self-described data: name or display name, entrepreneur stage, interests and challenges, coarse meetup area, meeting preferences, and an optional self-declared faith context.
  - *Discovery consent*: a separate opt-in that makes a profile discoverable, either globally (directory) or for one event (event-scoped reconnection).
  - *Connection request*: a private request from one person to another. The states are pending, accepted, declined, withdrawn and expired.
  - *Contact share*: a separate, two-sided, revocable permission to reveal contact details. It is not implied by an accepted request.
  - *Block / report*: a block stops discovery and contact both ways; a report flags a person to the admin.
  - *Circle*: a group for ongoing support. It has a purpose, visibility, an admission policy and a facilitator. A circle may optionally be faith-based (for example a Christian entrepreneurs circle).
  - *Membership*: belonging to a circle. It is not attendance and not event registration.
  - *Event*: a gathering with topic, date, time and timezone, mode, venue, optional capacity, price and what is included. Its states are draft, submitted, approved/published, rejected and cancelled.
  - *Event host / co-host*: explicitly assigned. Hosting gives no access to anyone's private peer data.
  - *Registration*, *confirmation* and *attendance* are three different facts and must never be treated as the same thing.
  - *Venue*: a hand-picked directory entry. Unknown fields are shown as unknown.
  - *Match suggestion*: an AI-produced list of suggested peers or circles, each with a stated reason drawn from profile fields.
  - *Follow-up report*: an optional self-report that a pair met (first catch-up, second catch-up), with no conversation content.
- **Existing systems, data sources, or workflows to respect**
  - Recurring coffee meetups with a cafe partner. Conversations may stay on WhatsApp, and the app does not need to host chat.
  - Organiser-led choice of topics and speakers stays human-led.
  - Payments stay with the existing organiser and cafe process. The app records price and what is included only.
  - Luma, Meetup, Timeleft and Lectures After Dark are inspiration only. No connector is assumed to be available.
- **Regulatory or organizational constraints**
  - Faith is a voluntary, self-described attribute. It is never inferred, never verified, and never required to join (operator answer: *all entrepreneurs, faith optional*).
  - Before any real-user version, consent wording, retention and deletion, and personal-data obligations must be resolved (PRD-v0 S10). This does not apply to the synthetic capstone, but it is recorded as a gate.

### 3. Discovery Buckets

#### Must do

| ID | Item | Kind (requirement / assumption) | Testable constraint |
|----|------|---------------------------------|---------------------|
| MD-001 | Participants create a minimal profile that includes entrepreneur stage (seasoned / new / aspiring) | requirement | A profile cannot be saved without a stage value from the three allowed values; every other field except display name is optional |
| MD-002 | Opt-in people directory | requirement | A profile appears in directory results only when its global discovery consent is `true`; the default is `false` |
| MD-003 | Event-scoped reconnection after an event | requirement | After an event ends, only attendees marked attended who have opted in for that event can see each other in that event's reconnection list |
| MD-004 | Discovery tool: filter people and circles by stage, interests/challenges, meetup area and meeting preference | requirement | Filter results contain only discoverable, unblocked profiles and visible circles that match every applied filter |
| MD-005 | AI suggests peers and circles from opted-in profiles; the user decides | requirement | Every suggestion shown is discoverable to the viewer, is not the viewer, is not blocked, and has a reason that names at least one profile field both sides share; no request is sent without a user action |
| MD-006 | Private connection request with accept / decline | requirement | Only the recipient can accept or decline; the sender never sees more about a decline than the OQ-06 policy allows |
| MD-007 | Contact sharing that is mutual and can be revoked | requirement | Contact details are visible to a counterpart only when both have granted sharing; revoking hides them immediately from the next request onward |
| MD-008 | Block and report | requirement | After A blocks B, neither appears in the other's directory, reconnection, suggestion or request surfaces; a report creates a record the admin can see |
| MD-009 | Circle discovery, join by admission policy, leave | requirement | A circle's member list is visible only according to its visibility setting; joining follows the circle's policy (open, or request then approve); leaving takes effect at once |
| MD-010 | Faith-based circles as an optional circle type | requirement | A circle can carry an optional faith-context tag; there is no feature that a user can reach only by declaring a faith |
| MD-011 | Organisers submit events; the admin approves or rejects every event (human gate) | requirement | An event in state `draft`, `submitted` or `rejected` returns not-found or forbidden to every non-organiser, non-admin user in both the UI and the API; each approval stores admin id, timestamp and decision |
| MD-012 | Event registration, withdrawal, and attendance confirmation by the organiser | requirement | Registration, confirmation and attendance are stored as separate fields; a registration alone never makes someone eligible to reconnect |
| MD-013 | Explicit co-host assignment | requirement | Only the event organiser can assign co-hosts; a co-host can manage that event only |
| MD-014 | Curated venue directory; an event can reference a venue | requirement | Venue fields with no data render as "Unknown"; only the admin can create venue entries (no user submissions) |
| MD-015 | Optional follow-up self-report for an accepted pair | requirement | Submitting a report more than once does not change its count; a pair is counted once; "no report" is stored as a different value from "reported no catch-up" |
| MD-016 | Funnel metrics in separate units | requirement | The metrics view reports opportunities, opt-ins, requests, acceptances and follow-ups as separate counts with their denominators, and labels them synthetic |
| MD-017 | Directory, discovery, connection and circles work on made-up data | assumption | The seed dataset covers all three stages, at least two events (one approved, one pending), at least two circles (one faith-tagged), and blocked and declined cases |

#### Must not do

| ID | Item | Kind (requirement / assumption) | Testable constraint |
|----|------|---------------------------------|---------------------|
| MN-001 | No automatic directory entry from attending or registering | requirement | Registering for or attending an event leaves both discovery consents unchanged |
| MN-002 | No contact details revealed because of a request or an acceptance | requirement | API responses for requests and connections contain no contact fields unless both sides have granted sharing |
| MN-003 | AI never sends, accepts or declines requests, joins circles, or approves events | requirement | The AI component has no write path to request, membership or event-state tables; this is checked by tests and a tool or permission review |
| MN-004 | AI never infers or labels religion, and never uses faith context unless the user opted that field into matching | requirement | Eval cases where faith is undeclared produce no faith-based reason; the faith field is excluded from model input unless its matching opt-in is `true` |
| MN-005 | No unapproved event is visible publicly | requirement | See MD-011, applied to the listing, detail and share-link endpoints |
| MN-006 | Circle membership or co-hosting gives no access to private pair data | requirement | A circle member or co-host gets forbidden responses for another pair's requests, contact shares and follow-ups (PRD-v0 T06, T07) |
| MN-007 | Registration does not count as attendance, and event participation does not count as circle membership | requirement | See MD-012; registering does not create a membership |
| MN-008 | No real users, real personal data or real outreach in the capstone | requirement | All seed data is labelled synthetic; the app sends no email, SMS or WhatsApp messages; agents contact no person or venue |
| MN-009 | No venue booking requests, reservations or payments | requirement | There are no booking or payment endpoints or UI; venue entries are informational only |
| MN-010 | No invented venue listings | requirement | Every seeded venue is marked synthetic or comes from operator-supplied data |
| MN-011 | Authorization is enforced on the server, not only by hiding buttons | requirement | Direct API calls with a forged actor id are rejected; the actor comes from the server-side session, even with synthetic logins (PRD-v0 T12) |
| MN-012 | Matching does not require sensitive personal disclosures (struggles, recordings, contact lists, exact addresses, live location) | requirement | The profile schema has no such fields; meetup area is coarse (an area or district, not an address) |

#### Must cost

| ID | Item | Kind (requirement / assumption) | Testable constraint |
|----|------|---------------------------------|---------------------|
| MC-001 | AI suggestions run only when a user asks, never in the background | assumption | Model calls are triggered only by an explicit "suggest" action; there are no scheduled or bulk runs in the MVP |
| MC-002 | Bounded model use per suggestion request | assumption | At most one crew kickoff per request, with `max_iter` ≤ 12 and the candidate set capped (proposed: ≤ 50 profiles) before model input |
| MC-003 | Suggestion latency | assumption | Proposed: p95 ≤ 15 s on the synthetic dataset, with a loading state shown; the value must be confirmed (OQ-01) |
| MC-004 | Capstone model spend cap | assumption | A total and per-request spend ceiling and an rpm limit (`max_rpm`) are set before evals run; amounts are not yet given (OQ-01) |
| MC-005 | A degraded mode keeps discovery usable | requirement | If the model call fails, times out or exceeds budget, filter-based discovery (MD-004) still works and the UI says suggestions are unavailable |

#### Must prove

| ID | Item | Kind (requirement / assumption) | Evidence the system must produce |
|----|------|---------------------------------|----------------------------------|
| MP-001 | Privacy and access boundaries hold | requirement | Passing automated tests for MN-001, MN-002, MN-005, MN-006, MN-007 and MN-011, and for PRD-v0 T01–T09 and T11–T12 as they apply to the MVP |
| MP-002 | The admin event gate works and leaves a record | requirement | Tests showing an unapproved event is invisible on every surface, plus an approval log entry (admin, time, decision) for every published event |
| MP-003 | AI suggestions are safe and useful | requirement | An eval report (`evals.md`) on a labelled synthetic gold set: 100% eligibility (no self, blocked or undiscoverable profiles); 100% of reasons grounded in real shared fields; 0 faith-based reasons when faith is undeclared or not opted in; relevance against the gold set with a threshold set before the run (OQ-02) |
| MP-004 | The end-to-end journey works | requirement | A scripted end-to-end test: admin approves event → attendance confirmed → opt in → AI suggestion → request → accept → mutual contact share → follow-up report → join circle |
| MP-005 | Funnel metrics are computed correctly | requirement | A metrics output on the seed data that matches hand-computed counts per unit, labelled synthetic |
| MP-006 | The MVP does not demonstrate market demand | assumption | Docs and UI label the data synthetic; the MRD keeps H1–H5 as unvalidated hypotheses |

### 4. Functional Requirements

| ID | Description | Priority (Must/Should/Could) | Source bucket ID |
|----|-------------|------------------------------|------------------|
| FR-001 | Create and edit a minimal profile with entrepreneur stage, interests/challenges, coarse area, meeting preferences, and an optional faith context with its own matching opt-in | Must | MD-001, MN-004, MN-012 |
| FR-002 | Toggle global discovery consent; the opt-in people directory lists only consenting profiles | Must | MD-002, MN-001 |
| FR-003 | Event-scoped reconnection list for attended and opted-in participants of an ended event | Must | MD-003, MD-012 |
| FR-004 | Filter-based discovery of people and circles | Must | MD-004, MC-005 |
| FR-005 | AI match suggestions (peers and circles) on request, each with a grounded reason; the user chooses whether to act | Must | MD-005, MN-003, MN-004, MC-001, MC-002 |
| FR-006 | Send, withdraw, accept and decline connection requests; duplicate and reverse requests are deduplicated and never auto-accepted | Must | MD-006 |
| FR-007 | Mutual, revocable contact sharing between connected users | Must | MD-007, MN-002 |
| FR-008 | Block a user; report a user to the admin | Must | MD-008 |
| FR-009 | Browse circles, request or join by admission policy, leave a circle | Must | MD-009 |
| FR-010 | Facilitator manages circle details, admission requests and member-list visibility | Should | MD-009 |
| FR-011 | Optional faith-context tag on circles, usable as a discovery filter | Should | MD-010 |
| FR-012 | Organiser creates a draft event and submits it for approval | Must | MD-011 |
| FR-013 | Admin queue to approve or reject submitted events, with an optional reason; the decision is logged | Must | MD-011, MP-002 |
| FR-014 | Published event listing, detail page and share link for approved events only | Must | MD-011, MN-005 |
| FR-015 | Register for and withdraw from an event; the organiser confirms attendance | Must | MD-012, MN-007 |
| FR-016 | Organiser assigns co-hosts | Should | MD-013 |
| FR-017 | Event may optionally link to a circle; the link grants no data access | Should | MN-006 |
| FR-018 | Admin-curated venue directory; an event may reference a venue | Should | MD-014, MN-009, MN-010 |
| FR-019 | Follow-up self-report for accepted pairs | Should | MD-015 |
| FR-020 | Funnel metrics view in separate units, labelled synthetic | Should | MD-016, MP-005 |
| FR-021 | Synthetic seed dataset and synthetic login (choose a persona to act as) | Must | MD-017, MN-008 |

### 5. Non-Functional Requirements

| ID | Requirement | Trace |
|----|-------------|-------|
| NFR-001 | Security: every read and write is authorized on the server against a session-derived actor; actor ids sent by the client are ignored | MN-011, MP-001 |
| NFR-002 | Privacy: API responses include only the fields the viewer may see; contact fields and private pair data are never sent to clients that are not authorized | MN-002, MN-006 |
| NFR-003 | AI cost and latency: suggestions are on demand, bounded (MC-002), and have an rpm and spend cap | MC-001–MC-004 |
| NFR-004 | Reliability: suggestion failure degrades to filter discovery without blocking any other flow | MC-005 |
| NFR-005 | AI determinism: low temperature and memory=False, as in the CrewAI adapter; model, temperature and token limits recorded in Audit | MP-003 |
| NFR-006 | AI observability: the prompt trace and suggestion outputs are logged under `project-context/2.build/logs` with personal data limited to synthetic records | MP-003 |
| NFR-007 | Usability: a responsive web UI for phone and desktop widths; empty, loading and error states for each flow; accessibility to WCAG 2.1 AA baseline | Module 3 criteria |
| NFR-008 | Auditability: admin event decisions and reports are stored with actor and timestamp | MP-002 |
| NFR-009 | Data labelling: synthetic data and self-reports are labelled as such in the UI and metrics | MP-005, MP-006 |

### 6. Constraints

- **Technology**: the generated runtime is CrewAI (`AAMAD_TARGET_RUNTIME=crewai`), with agents and tasks in YAML under `config/`. The draft PRD suggests a responsive web app, a modular monolith and a relational data model; the final stack is `@system.arch`'s decision. No native mobile app and no built-in chat.
- **Budget / timeline**: this is a capstone learning project. The model spend cap and deadline are not given (OQ-01, OQ-08).
- **Integration**: must not integrate with Luma, Meetup, payment providers, booking providers or messaging channels in the MVP. WhatsApp stays outside the app.
- **Data**: synthetic only; no real participant or venue data.

### 7. Assumptions

- "Mock" in the brief means a demo on made-up data with no real users (operator answer, 2026-11-10).
- "Directory" in the brief means the opt-in people directory; circles and events have their own listings.
- An organiser is any user the admin has granted the organiser role; organisers draft events but cannot publish them without admin approval. The draft PRD did not include an admin gate, and the brief adds it.
- The organiser confirming attendance is how someone becomes eligible to reconnect after an event (the draft PRD left this open). This is enough for synthetic data but must be revisited before a real pilot.
- The admin is a single platform role in the MVP, not a per-circle role.
- Circle creation is limited to the admin and to people the admin names as facilitators (the draft left this open; see OQ-04).
- The MC-002 and MC-003 values are proposed defaults until the operator confirms them.

### 8. Acceptance Criteria

- **AC-001** Given a participant who has not opted in, when any other user loads the directory, discovery results, AI suggestions or an event reconnection list, then that participant does not appear. (MD-002, MN-001)
- **AC-002** Given an approved event that has ended, and A and B both marked attended and opted in for it, when A opens that event's reconnection list, then B appears; and a registered-but-not-attended C does not. (MD-003, MN-007)
- **AC-003** Given A sends B a request, when A or a third party C tries to accept it through the API, then the server returns forbidden; only B can accept or decline. (MD-006, MN-011)
- **AC-004** Given A and B are connected, when only A has granted contact sharing, then neither sees the other's contact details; when both have granted it, both see them; when either revokes, they disappear. (MD-007, MN-002)
- **AC-005** Given A blocked B, when B requests suggestions, filters discovery or sends a request, then A is absent and requests to A are rejected. (MD-008)
- **AC-006** Given an organiser submits an event, when any non-admin, non-organiser user lists events, opens its URL or calls its API, then it is not visible until the admin approves it; after approval it is visible, and the log shows admin, time and decision. (MD-011, MN-005, MP-002)
- **AC-007** Given a request for suggestions, when the crew returns results, then every suggestion is eligible (opted in, not self, not blocked), has a reason that cites a shared field, and no request, membership or event state changes. (MD-005, MN-003)
- **AC-008** Given a user with no faith context or with faith matching turned off, when suggestions are generated, then the model input excludes faith and no reason mentions faith. (MN-004)
- **AC-009** Given the model is unavailable or over budget, when the user requests suggestions, then a clear message appears and filter discovery still returns results. (MC-005)
- **AC-010** Given A and B are in the same circle, or co-host the same event, when A asks for B's private pair data with someone else, then the server returns forbidden. (MN-006)
- **AC-011** Given a circle with a request-then-approve policy, when a user requests to join, then they are not a member until the facilitator approves; leaving removes membership at once. (MD-009)
- **AC-012** Given a venue with an unknown capacity, when shown, then capacity reads "Unknown"; there is no booking or payment action anywhere in the UI or API. (MD-014, MN-009)
- **AC-013** Given an accepted pair submits the same follow-up report twice, then metrics count the pair once and keep "no report" separate from "reported no catch-up". (MD-015, MD-016)
- **AC-014** The scripted end-to-end journey in MP-004 passes on the seed dataset. (MP-004)
- **AC-015** The AI eval in MP-003 meets its thresholds before release. (MP-003)

### 9. Out of Scope / Future Work

- Real users, real attendee data, consent and retention flows, production authentication (PRD-v0 S01, S09, S10 become gates for a later real pilot).
- Venue booking requests, reservations and payments (PRD-v0 V02–V04); user-submitted venues.
- Built-in chat; outbound email, SMS or WhatsApp; promotional communications.
- External connectors (Luma, Meetup, social platforms).
- Automated recurring events or circles; waitlists and capacity allocation.
- Business coaching or mentorship features and a mentoring marketplace (MRD-v0 §6 needs separate evidence).
- Autonomous matchmaking (the AI acting without the user); background or bulk AI runs.
- Native mobile apps; microservices.
- The owner-run manual demand experiment (MRD-v0 §5). It is valid but sits outside the app build, and no agent is authorised to contact anyone.

## Sources

- Operator brief in chat, 2026-11-10: title, users (seasoned, new, aspiring entrepreneurs), the job (connect after an in-person event, find circles), the mock scope (directory, discovery tool, connection and circles), and the human gate (admin approves any event).
- Operator elicitation answers, 2026-11-10: audience = all entrepreneurs, faith optional; venue directory in scope, booking deferred; AI suggests matches; synthetic data only.
- `project-context/1.define/MRD-v0.md` (owner draft, 2026-11-08): the problem, organiser observations, hypotheses H1–H5, alternatives, and the demand-experiment design.
- `project-context/1.define/PRD-v0.md` (owner draft, 2026-11-08): roles, journeys P01–P06, C01–C05, E01–E07, V01–V04, safeguards S01–S10, funnel contract, and scenarios T01–T12.
- `aamad.config.yml` (project.mode greenfield, runtime crewai); `.claude/rules/adapter-crewai.md`.

## Assumptions

- The faith-centred framing in the drafts is replaced by "all entrepreneurs, faith optional"; faith-based circles stay as an option. The drafts' religious-data safeguards (S05, S07) are kept as MN-004 and MN-012.
- The 23 passing tests and the starter code mentioned in PRD-v0 §9 are not in this repo and are not relied on.
- `OPEN-DECISIONS-v0.md` and `SOURCE-MAP-v0.md`, which the drafts reference, are not present in the repo; their contents are unknown.
- The drafts' "invited organiser" model is combined with the brief's admin gate: organisers draft and submit, and the admin publishes.

## Open Questions

- **OQ-01** Model spend: the total capstone budget, the per-request ceiling, and the target latency (MC-003, MC-004).
- **OQ-02** AI eval: how the relevance gold set is built and labelled, and the pass threshold (MP-003). Set before the first run.
- **OQ-03** Matching signals: which profile fields the AI may use and how they are weighted. "Same industry" is not required (PRD-v0 P02).
- **OQ-04** Circle creation rights, admission policy defaults, capacity, and facilitator powers.
- **OQ-05** Can users see public events without logging in, and should events be public or invite-only (PRD-v0 E04)?
- **OQ-06** Request expiry and retry policy, and what the sender sees after a decline (PRD-v0 T04, T05).
- **OQ-07** Circle success criterion (return visits plus a usefulness signal; the wording is unresolved, PRD-v0 §3).
- **OQ-08** Capstone deadline and demo format.
- **OQ-09** ~~Rewrite the MRD for all entrepreneurs, or keep it faith-centred?~~ Resolved 2026-11-10: widen to all entrepreneurs, with the existing HK faith-centred community as the beachhead (see `mrd.md`).
- **OQ-10** What can the admin do with a report (for example suspend, hide or contact the user) in the synthetic MVP?

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*elicit-requirements` — output: `project-context/1.define/system-description.md` — runtime resolved: `crewai` (env `AAMAD_TARGET_RUNTIME`, matches `aamad.config.yml`) — mode: greenfield — no application pattern selected — Prompt Trace omitted: this is a Define-phase artifact, not a runtime output.
- 2026-11-10 — persona: `product-mgr` — action: quality pass — clarified MD-006 wording; marked OQ-09 resolved.
