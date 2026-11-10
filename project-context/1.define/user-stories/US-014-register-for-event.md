# US-014 — Register for or withdraw from an event

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-014

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-014
- **Title**: Register for or withdraw from an event
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to register for a published event, and withdraw if I cannot go, so that the organiser knows who plans to come.

### 3. Acceptance Criteria

1. I can register only for approved, published events.
2. Registration, organiser confirmation and attendance are stored and displayed as separate facts (MD-012).
3. Registration does not change discovery consent or circle membership (MN-001, MN-007).
4. Withdrawing removes my registration; the organiser's list updates with labels that make the meaning of each count clear (PRD-v0 E06).

### 4. Scope Notes

- **In Scope for MVP**: Register, withdraw, organiser list.
- **Deferred**: Waitlists, capacity allocation, payment.

### 5. Traceability

- **PRD Anchors**: FR-015, MD-012, MN-007
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
