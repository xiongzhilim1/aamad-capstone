# US-003 — Opt in to the people directory

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-003

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-003
- **Title**: Opt in to the people directory
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to choose whether I appear in the people directory, and change my mind at any time, so that I control who can find me.

### 3. Acceptance Criteria

1. Global discovery consent defaults to off for every new profile.
2. Given I have not opted in, when any other user loads the directory, discovery results or AI suggestions, then I do not appear (AC-001).
3. Given I opt out, when the directory is next loaded, then I no longer appear; existing connections are unaffected.
4. Directory entries show only the profile fields allowed for discovery, never contact fields (MN-002).

### 4. Scope Notes

- **In Scope for MVP**: Consent toggle; directory listing.
- **Deferred**: Finer visibility levels (for example circles only).

### 5. Traceability

- **PRD Anchors**: FR-002, MD-002, MN-001, AC-001
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
