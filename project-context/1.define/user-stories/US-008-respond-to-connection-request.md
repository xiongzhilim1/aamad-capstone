# US-008 — Accept or decline a connection request

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-008

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-008
- **Title**: Accept or decline a connection request
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to accept or decline requests sent to me, so that only connections I want are made.

### 3. Acceptance Criteria

1. Only the recipient can accept or decline; the sender or a third party gets a forbidden response from the API (AC-003).
2. Accepting creates a connection but shares no contact details (MN-002); contact sharing is a separate step (US-009).
3. A decline is private; what the sender sees follows the policy in OQ-06 and never reveals more than that policy allows.
4. Pending requests are listed separately from accepted connections.

### 4. Scope Notes

- **In Scope for MVP**: Accept, decline, request inbox.
- **Deferred**: Bulk actions.

### 5. Traceability

- **PRD Anchors**: FR-006, MD-006, AC-003
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-06: what the sender sees after a decline.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
