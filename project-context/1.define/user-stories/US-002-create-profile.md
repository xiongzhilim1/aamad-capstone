# US-002 — Create a minimal profile with entrepreneur stage

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-002

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-002
- **Title**: Create a minimal profile with entrepreneur stage
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to create and edit a minimal profile with my entrepreneur stage and optional details, so that others can find relevant peers if I choose to be discoverable.

### 3. Acceptance Criteria

1. Given the profile form, when I save without a stage, then saving fails; the allowed stages are exactly seasoned, new and aspiring (MD-001).
2. Display name and stage are the only required fields; interests and challenges, coarse meetup area, meeting preferences and faith context are optional.
3. Meetup area is chosen from coarse areas (district level); there is no address, workplace or live-location field (MN-012).
4. Faith context is free self-description, never inferred or verified, and has its own "use in matching" opt-in that defaults to off (MN-004).
5. Saving a profile does not change any discovery consent (MN-001).

### 4. Scope Notes

- **In Scope for MVP**: Create and edit profile; optional faith field with a matching opt-in.
- **Deferred**: Profile photos, verification badges, exact-location features.

### 5. Traceability

- **PRD Anchors**: FR-001, MD-001, MN-004, MN-012
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-03: which profile fields matching may use, and how they are weighted.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
