# US-007 — Send or withdraw a connection request

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-007

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-007
- **Title**: Send or withdraw a connection request
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to send a private connection request to someone I can see, and withdraw it if I change my mind, so that I can start a connection without exposing my contacts.

### 3. Acceptance Criteria

1. I can send a request only to someone visible to me through the directory, an event reconnection list, filters or suggestions.
2. A second request to the same person while one is pending does not create a duplicate; a reverse request does not auto-accept either one (PRD-v0 T04).
3. Sending a request reveals no contact details to either side (MN-002).
4. I can withdraw a pending request; it then disappears from the recipient's view.
5. Requests to someone who blocked me, or whom I blocked, are rejected (AC-005).

### 4. Scope Notes

- **In Scope for MVP**: Send, withdraw, dedupe.
- **Deferred**: An optional message with the request; request expiry (OQ-06).

### 5. Traceability

- **PRD Anchors**: FR-006, MD-006, MN-002
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-06: request expiry and retry policy.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
