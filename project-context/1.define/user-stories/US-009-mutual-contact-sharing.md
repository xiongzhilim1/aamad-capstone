# US-009 — Share contact details by mutual consent

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-009

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-009
- **Title**: Share contact details by mutual consent
- **Priority**: Must
- **Persona**: Connected pair of participants

### 2. Narrative

As a member of a connected pair, I want each of us to choose whether to share contact details, with the option to revoke, so that contacts are exchanged only when both of us want it.

### 3. Acceptance Criteria

1. Given only A has granted sharing, then neither A nor B sees the other's contact details (AC-004).
2. Given both have granted sharing, then both see each other's contact details.
3. Given either revokes, then contact details are hidden from the next request onward, and the UI explains that copies already made cannot be recalled (PRD-v0 S08).
4. Contact fields never appear in any API response unless both sides have granted sharing (NFR-002).

### 4. Scope Notes

- **In Scope for MVP**: Grant and revoke per connection.
- **Deferred**: In-app messaging; WhatsApp deep links.

### 5. Traceability

- **PRD Anchors**: FR-007, MD-007, MN-002, AC-004
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
