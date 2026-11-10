# US-013 — Admin approves or rejects every event

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-013

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-013
- **Title**: Admin approves or rejects every event
- **Priority**: Must
- **Persona**: Admin

### 2. Narrative

As an admin, I want to review submitted events and approve or reject them, so that only events I have checked are published.

### 3. Acceptance Criteria

1. The admin sees a queue of submitted events.
2. Approving publishes the event to the listing, detail page and share link; rejecting returns it to the organiser with an optional reason.
3. Every decision is stored with admin id, timestamp and decision (MP-002, NFR-008).
4. No path, through UI or API, publishes an event without an admin approval record (AC-006).
5. AI never approves or rejects events (MN-003).

### 4. Scope Notes

- **In Scope for MVP**: Approval queue, approve, reject, decision log.
- **Deferred**: Delegated approvers; automatic pre-checks.

### 5. Traceability

- **PRD Anchors**: FR-013, FR-014, MD-011, MN-005, MP-002, AC-006
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- None specific to this story; see PRD Open Questions.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
