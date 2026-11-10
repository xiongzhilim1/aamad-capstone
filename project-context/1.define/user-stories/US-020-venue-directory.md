# US-020 — Browse a curated venue directory

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-020

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-020
- **Title**: Browse a curated venue directory
- **Priority**: Should
- **Persona**: Organiser and Admin

### 2. Narrative

As an organiser, I want to pick an event venue from a curated directory, with missing details clearly marked, so that events reference real-looking venue information without invented facts.

### 3. Acceptance Criteria

1. Only the admin can create and edit venue entries.
2. Fields with no data render as "Unknown" (AC-012).
3. Seeded venues are labelled synthetic (MN-010).
4. No booking request, reservation or payment action exists anywhere (MN-009).

### 4. Scope Notes

- **In Scope for MVP**: Venue directory and selection on an event.
- **Deferred**: Booking requests, availability, user-submitted venues (PRD-v0 V02–V04).

### 5. Traceability

- **PRD Anchors**: FR-018, MD-014, MN-009, MN-010, AC-012
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
