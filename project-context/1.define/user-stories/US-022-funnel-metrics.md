# US-022 — View funnel metrics in separate units

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-022

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-022
- **Title**: View funnel metrics in separate units
- **Priority**: Should
- **Persona**: Admin

### 2. Narrative

As an admin, I want to see opportunities, opt-ins, requests, acceptances and follow-ups as separate counts with denominators, so that I can understand the funnel without misleading combined rates.

### 3. Acceptance Criteria

1. Each unit is shown as a count with its denominator; no single combined conversion rate is shown (MD-016).
2. Metrics on seed data match hand-computed values (MP-005).
3. All figures are labelled synthetic, and self-reports are labelled self-reported (NFR-009).
4. Only aggregates are shown; no individual pair data is exposed.

### 4. Scope Notes

- **In Scope for MVP**: Admin metrics view.
- **Deferred**: Thresholds, observation windows, cohort definitions (open in PRD-v0 §8).

### 5. Traceability

- **PRD Anchors**: FR-020, MD-016, MP-005
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- Observation window and decision thresholds for a future pilot.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
