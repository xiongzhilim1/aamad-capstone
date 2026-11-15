# US-012 — Organiser drafts and submits an event

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-012

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-012
- **Title**: Organiser drafts and submits an event
- **Priority**: Must
- **Persona**: Organiser

### 2. Narrative

As an organiser, I want to draft an event and submit it for admin approval, so that it can be published to participants once approved.

### 3. Acceptance Criteria

1. Only users with the organiser role can create events.
2. The date may be in the past ("Added after the event"), and the event still needs admin approval (MD-025, AC-023). A draft records topic, date, time and timezone, mode, optional venue (from the directory, or free text), optional capacity, price and currency, and what is included.
3. Submitting moves the event from draft to submitted; organisers can edit a draft but not a submitted event without withdrawing it.
4. A draft, submitted or rejected event is invisible to everyone except its organiser and the admin, through listing, detail, share link and API (AC-006, MN-005).

### 4. Scope Notes

- **In Scope for MVP**: Create, edit, submit, withdraw submission.
- **Deferred**: Recurring events, ticketing, payments, external publishing.

### 5. Traceability

- **PRD Anchors**: FR-012, MD-011, MN-005, AC-006
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.
- Inferred, not in the PRD: a submitted event must be withdrawn before it can be edited.

## Open Questions

- OQ-05: whether events are public or invite-only.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
- 2026-11-15 — persona: `product-mgr` — action: `*create-stories` (update) — past-dated events allowed.
