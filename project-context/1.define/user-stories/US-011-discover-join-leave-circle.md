# US-011 — Find, join and leave a circle

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-011

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-011
- **Title**: Find, join and leave a circle
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to find circles, join or request to join according to each circle's policy, and leave any time, so that I can get ongoing support and fellowship.

### 3. Acceptance Criteria

1. The circle listing shows purpose and details without exposing private member information; member-list visibility follows the circle's setting.
2. For an open circle, joining makes me a member at once; for a request-then-approve circle, I am not a member until the facilitator approves (AC-011).
3. Leaving removes my membership at once without any confirmation pressure.
4. Being in a circle with someone gives me no access to their private pair data (AC-010, MN-006).
5. Registering for an event linked to a circle does not make me a member (MN-007).

### 4. Scope Notes

- **In Scope for MVP**: Browse, join, request, leave.
- **Deferred**: Circle chat, recurring circle meetings.

### 5. Traceability

- **PRD Anchors**: FR-009, MD-009, MN-006, MN-007, AC-010, AC-011
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-04: circle creation rights and default admission policy.
- OQ-07: circle success criterion.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
