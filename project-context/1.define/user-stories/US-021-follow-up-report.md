# US-021 — Report a catch-up after connecting

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-021

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-021
- **Title**: Report a catch-up after connecting
- **Priority**: Should
- **Persona**: Connected pair of participants

### 2. Narrative

As a member of a connected pair, I want to optionally record that we met up (first and second catch-up), so that the product can learn whether connections turn into relationships.

### 3. Acceptance Criteria

1. Only members of an accepted pair can report, and the report holds only the catch-up number, a date range and an optional usefulness rating; no conversation content.
2. Submitting the same report twice does not change counts; the pair is counted once (AC-013).
3. "No report" is stored and shown as a different value from "reported no catch-up".
4. Reports are visible only to the pair and, in aggregate only, to the metrics view (MN-006).

### 4. Scope Notes

- **In Scope for MVP**: Self-report form.
- **Deferred**: Reminders to report; verification.

### 5. Traceability

- **PRD Anchors**: FR-019, MD-015, AC-013
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.
- Inferred, not in the PRD: the report fields are the catch-up number, a date range and an optional usefulness rating.

## Open Questions

- Usefulness check wording (PRD-v0 §3, unresolved).

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
