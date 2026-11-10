# US-005 — Discover people and circles with filters

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-005

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-005
- **Title**: Discover people and circles with filters
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to filter people and circles by stage, interests and challenges, area and meeting preference, so that I can find relevant peers and circles without relying on AI.

### 3. Acceptance Criteria

1. Results include only discoverable, unblocked profiles and visible circles that match every applied filter (MD-004).
2. Faith-tagged circles can be filtered when FR-011 is delivered; there is no faith filter on people.
3. With no matches, an empty state explains what happened and suggests widening the filters.
4. Filter discovery works when the AI suggestion service is unavailable (MC-005).

### 4. Scope Notes

- **In Scope for MVP**: Filters on people and circles.
- **Deferred**: Saved searches, alerts.

### 5. Traceability

- **PRD Anchors**: FR-004, MD-004, MC-005
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
