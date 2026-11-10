# Community app — pilot PRD v0

Date: 2026-11-08. Status: draft for owner review; not a production release approval.
This is a product contract for the next learning increments, not a claim of validated demand.
The source map distinguishes user decisions, reported observations and proposed defaults.

## 1. Product purpose
Help Christian entrepreneurs find voluntary, ongoing supportive peer relationships.
Shared faith is an intended community context, not a claim about the project owner's identity
or a guarantee of business expertise, trustworthiness or shared biblical interpretation.
Business coaching and mentorship follow the relationship-first experience.
The project also teaches product judgement, data modelling, implementation, evaluation and deployment.
Agents can implement and test; the learner owns product taste, trade-offs and acceptance.

## 2. Pilot scope and user roles
The pilot includes thin versions of all three flows: peers, circles and events.
Build sequence: shared foundation → peers → circles → events → cross-flow verification.
This is an implementation sequence, not a requirement that people experience the app in that order.

- Participant: create a minimal profile; choose discovery preferences; request/join appropriate connections;
  register for events; optionally report follow-up or perceived usefulness.
- Invited organiser: create events and explicitly assign eligible co-hosts. Hosting is not a self-selected role.
- Event co-host: manage the assigned event, not participants' private peer relationships.
- Circle facilitator: a proposed pilot role; who may create/manage circles remains an open decision.
- Venue partner: an operational counterpart, not automatically an app account or confirmed booking provider.

Topic/speaker curation stays human-led. WhatsApp may remain the conversation channel.
The app need not make all relationship activity happen on-platform.

## 3. Product outcomes
A peer pathway succeeds when a pair reports a first coffee/meal and a second catch-up,
online or in person. Count the pair once. Reports are not independently verified attendance.
A circle pathway may succeed through return to the same people/circle and perceived support;
its precise criterion is proposed, not yet selected.
Two meetings or repeated visits alone do not establish a supportive relationship.
A brief, optional usefulness/continuation check can complement behaviour; wording is unresolved.
No numeric growth, retention or conversion targets have been agreed.

## 4. Peer and reconnection journey
P01. A participant explicitly opts into the relevant discovery surface; no automatic attendee-directory entry.
P02. Offer minimal permitted profiles with shared challenges/interests and feasible meeting preferences.
     Exact fields, match constraints and ranking are unresolved. Same industry is not a mandatory rule.
P03. Send a private connection request. The recipient can accept or decline; nobody can accept for them.
P04. No automatic contact disclosure on request or acceptance. Explicit contact-sharing permission is separate.
P05. Respect bilateral blocking; provide a reporting route before exposing the product to real participants.
P06. Optionally record a later catch-up with minimal self-report data, not conversation content.

Event-scoped entry: after a gathering, eligible participants may opt into reconnecting with other
opted-in participants from that event. An RSVP alone must not assert that somebody attended.
How attendance eligibility is established is a pre-pilot decision, not solved by the synthetic fixture.
Broader peer discovery remains in scope; it must not silently make every profile globally visible.
A proposed first entry is event-scoped discovery to bound privacy and simplify a small test.

## 5. Circle journey
C01. Discover an appropriately visible circle and its purpose without exposing private member information.
C02. Request or accept membership according to an explicit admission policy; membership is not an RSVP.
C03. See allowed group details and gatherings; choose which events to attend.
C04. Leave a circle without being coerced into ongoing participation.
C05. Keep private peer data separate even when the pair shares a circle or hosts an event together.

Circle creation rights, admission, capacity, member-list visibility and facilitator powers remain open.
The pilot does not require a new group chat system or automated recurrence engine.

## 6. Event and venue journey
E01. An invited organiser creates a draft event with topic, date/time/timezone, meetup mode,
     permitted venue/location details, optional capacity, price/currency and what is included.
E02. Assign co-hosts explicitly. Participant price and venue charges are separate facts.
E03. An event may belong to a pair/circle or stand alone. The association grants no private-data access.
E04. Publish only approved event details to the selected audience; participant/contact lists stay protected.
     Public versus invite-only visibility and publish permissions must be decided before real publication.
E05. Provide a shareable event link and organiser-triggered invitation workflow. Direct external-platform
     publishing is later work; sharing a link does not automatically send messages or grant membership.
E06. Record event registration and organiser confirmation separately; display counts with clear meanings.
     RSVP, confirmation, payment and attendance must not be treated as synonyms.
E07. Allow cancellation/withdrawal and maintain a usable organiser list. Capacity policy remains unresolved.

The existing cafe workflow was reported as flexible and generally workable. Manual counting is not yet
an established pain point; do not make waitlists or strict allocation the centre of this pilot.
Payments may remain with the existing organiser/cafe process. Who receives them and when is unknown.

V01. Offer a curated venue directory with known information or explicitly unknown fields; no invented listings.
V02. Capture a booking request tied to event, venue, requested date/time and party size.
V03. Keep draft/prepared, actually sent, acknowledgement and confirmation distinct. The first delivery
     can prepare a request for the organiser to send manually; never label a draft as sent.
V04. No provider-backed availability, automated reservation guarantee or payment checkout in this pilot.
     Submission of additional venues and regular automated bookings belong to the later roadmap.

## 7. Non-negotiable access and data boundaries
S01. Before real-user access, authenticate identity and derive the actor on the server; ignore claimed actor IDs.
S02. Authorise every resource/action on the backend, not just by hiding interface buttons.
S03. A circle member or event co-host cannot read another private pair's check-ins merely through association.
S04. Event participation is not circle membership, profile-publication permission or marketing opt-in.
S05. Religious affiliation is voluntarily described, not inferred or labelled verified by the app.
S06. Prefer coarse meetup-area preferences over exact workplace addresses or live location.
S07. Do not require spiritual struggles, recordings, contact lists or private conversation contents for matching.
S08. Revoke future app access/sharing as designed, while explaining that copied contacts cannot be recalled.
S09. Require a usable block/report process and defined organiser response before real-user use.
S10. Resolve data retention/deletion, consent wording and profile/member-list visibility before collecting real data.

These are product safeguards, not a completed security audit or a statement of legal compliance.

## 8. Funnel and evaluation contract
Measure separate units; do not combine people, requests and pairs into an unexplained conversion rate.

- Opportunity offered: unique eligible event-person opportunities actually offered the optional flow.
  A registered attendee or page view is not automatically an exposure. Delivery measurement remains to be defined.
- Opt-in: unique eligible event-person opt-ins; rate denominator is observed opportunities offered.
- Request: distinct valid request records. Also report people sending at least one request against opted-in people.
- Acceptance: accepted request records divided by valid requests, with pending/closed states reported separately.
- Follow-up: distinct accepted pairs with the specified optional follow-up report, divided by accepted pairs
  that have reached the agreed observation window. Distinguish no report from a reported no-catch-up.
- Circle continuity: return to the same circle/people plus an optional usefulness signal; definition pending.

Observation windows, denominators for cross-event deduplication and decision thresholds are open.
Use rates only with counts and exposure windows. Small pilots are directional signals, not population proof.
Historical acceptance is distinct from current unblocked contact access.
Synthetic counts are clearly labelled synthetic; self-reports are clearly labelled self-reports.
No real funnel data or behavioural trial has been collected in this work.

## 9. Verification and pilot gates
Synthetic verification can run alongside an owner-run, voluntary manual demand experiment.
The manual experiment still needs clear opt-in, private handling and mutual permission for contact sharing.
Real people may use an app version only after that version's access/privacy and operational gates pass.
No human outreach, invitations, bookings or promotion are authorised to an agent by this PRD.

Acceptance scenarios:
T01. Opted-in event attendees can discover permitted peers; non-opted-in people remain hidden.
T02. A sender cannot accept their own request; a third party cannot read/respond to it.
T03. Request/acceptance does not reveal contacts; explicit bilateral sharing is required and revocable.
T04. Duplicate and reverse requests do not inflate counts or auto-accept. Final expiry/retry policy must be set.
T05. Blocks prevent further discovery/contact access according to policy; declined responses remain private.
T06. Two private pairs can share a circle without cross-pair private-data access.
T07. Peer partners can co-host an event without granting event staff access to the peer relationship.
T08. Someone can attend an event without joining a circle; registration does not assert attendance.
T09. A standalone event can exist without an artificial circle, and with independent hosting permissions.
T10. A booking request/draft is never displayed as a sent or confirmed reservation without evidence.
T11. Follow-up reports are idempotent and pairs are counted once under the chosen cohort definition.
T12. Direct API calls and forged actor IDs fail in the future authenticated app, even if UI controls are bypassed.

The delivered starter covers selected sequential domain rules with assumed actor identities. Its recorded
23 passing tests and five detected deliberate defects are historical synthetic evidence, not coverage of
all scenarios above or permission to run a real-user pilot. Circle/event CRUD, authentication and persistence
are not implemented by that starter.

## 10. Architectural direction and roadmap
Candidate direction: responsive web app, modular monolith and relational data model; final stack unselected.
Keep User/Profile, Space/Membership, Event/EventHost, Participation, DiscoveryConsent,
ConnectionRequest/contact-sharing, Venue and BookingRequest responsibilities explicit.
Events may reference Spaces optionally. A membership is not attendance or access to every linked resource.
The schema-learning thread explores these ideas; this PRD does not freeze its illustrative schema.

Later: automated recurrence, richer dinner/lecture/networking formats, mentorship,
user-submitted venues, confirmed bookings/payments and cancellation/refund handling.
Later distribution: permission-based promotional communications and Luma/Meetup/social connectors,
subject to verified API/authentication and operational feasibility. No connector availability is asserted.
Optional AI comes after a non-AI baseline, with usefulness, failure, privacy, latency and cost evaluations.
Not required now: native mobile, built-in chat, microservices, autonomous matchmaking or a mentoring marketplace.

## 11. Version and decision discipline
Change this draft when evidence changes; version requirements rather than silently rewriting their status.
Use the separate open-decisions file before implementing unresolved user-facing policies.
Next implementation increment should be a synthetic UI/API slice with explicit identity boundaries.
No real-user launch is approved by this document. Independent agent review is pending; the current
workspace workflow does not permit subagents, so it must not be described as independently verified.

## Source map
See SOURCE-MAP-v0.md for the conversation evidence, installed-source records and proposed-requirement status.
