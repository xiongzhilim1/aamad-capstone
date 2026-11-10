# US-016 — Facilitator manages a circle

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-016

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-016
- **Title**: Facilitator manages a circle
- **Priority**: Should
- **Persona**: Circle facilitator

### 2. Narrative

As a circle facilitator, I want to edit my circle's details, approve or decline join requests, and set member-list visibility, so that the circle stays purposeful and safe.

### 3. Acceptance Criteria

1. Only the circle's facilitator or the admin can edit details, admission policy and member-list visibility.
2. The facilitator can approve or decline pending join requests.
3. Facilitator powers give no access to members' private pair data (MN-006).

### 4. Scope Notes

- **In Scope for MVP**: Edit circle, admissions, visibility.
- **Deferred**: Removing members, multiple facilitators, capacity rules.

### 5. Traceability

- **PRD Anchors**: FR-010, MD-009
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-04: facilitator powers and circle creation rights.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
