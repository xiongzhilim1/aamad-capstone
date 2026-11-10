# US-015 — Organiser confirms who attended

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-015

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-015
- **Title**: Organiser confirms who attended
- **Priority**: Must
- **Persona**: Organiser (or assigned co-host)

### 2. Narrative

As an organiser, I want to mark which registrants actually attended, so that only real attendees become eligible to reconnect.

### 3. Acceptance Criteria

1. Only the event's organiser or assigned co-hosts can mark attendance, and only after the event starts.
2. Marking someone attended makes them eligible for that event's reconnection list (US-004); it does not opt them in.
3. Registered-but-not-attended people never become eligible (AC-002).
4. Attendance marks can be corrected, and the correction is recorded.

### 4. Scope Notes

- **In Scope for MVP**: Mark and unmark attendance.
- **Deferred**: Check-in by QR code; attendee self-check-in.

### 5. Traceability

- **PRD Anchors**: FR-015, MD-003, MD-012
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.
- Inferred, not in the PRD: attendance can be marked only after the event starts, and corrections are recorded.

## Open Questions

- Organiser-confirmed attendance is an assumption for the synthetic MVP and must be revisited before a pilot (PRD Assumptions).

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
