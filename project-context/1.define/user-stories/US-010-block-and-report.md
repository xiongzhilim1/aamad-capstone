# US-010 — Block or report another user

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-010

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-010
- **Title**: Block or report another user
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to block someone, or report them to the admin, so that I am protected from unwanted contact.

### 3. Acceptance Criteria

1. Given A blocks B, then neither appears in the other's directory, event reconnection, filters or suggestions, and requests between them are rejected (AC-005).
2. Blocking hides any existing contact share between the two.
3. A report creates a record with reporter, subject, reason and timestamp that only the admin can see (NFR-008).
4. Blocks and reports are never visible to the person blocked or reported.

### 4. Scope Notes

- **In Scope for MVP**: Block, unblock, report, admin report list.
- **Deferred**: Admin enforcement actions (OQ-10); a real-user response process (S09).

### 5. Traceability

- **PRD Anchors**: FR-008, MD-008, AC-005
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-10: what the admin can do with a report.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
