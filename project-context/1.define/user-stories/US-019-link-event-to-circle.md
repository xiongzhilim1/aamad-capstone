# US-019 — Link an event to a circle

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-019

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-019
- **Title**: Link an event to a circle
- **Priority**: Should
- **Persona**: Organiser

### 2. Narrative

As an organiser, I want to optionally link my event to a circle, so that circle members can find relevant gatherings.

### 3. Acceptance Criteria

1. An event can stand alone or link to one circle (PRD-v0 T09).
2. The link grants no access to circle members' private data, and grants circle membership to no one (MN-006, MN-007).
3. A linked event still requires admin approval (MD-011).

### 4. Scope Notes

- **In Scope for MVP**: Optional link shown on circle and event pages.
- **Deferred**: Circle-only (members-only) events.

### 5. Traceability

- **PRD Anchors**: FR-017, MN-006, MN-007
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-05: whether linked events can be visible to circle members only.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
