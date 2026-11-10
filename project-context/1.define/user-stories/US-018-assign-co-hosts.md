# US-018 — Organiser assigns co-hosts

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-018

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-018
- **Title**: Organiser assigns co-hosts
- **Priority**: Should
- **Persona**: Organiser

### 2. Narrative

As an organiser, I want to assign co-hosts to my event, so that others can help me run it.

### 3. Acceptance Criteria

1. Only the event's organiser can assign or remove co-hosts.
2. A co-host can manage only that event (edit draft details, mark attendance), not publish it.
3. Co-hosting gives no access to any participant's private pair data (MN-006, PRD-v0 T07).

### 4. Scope Notes

- **In Scope for MVP**: Assign and remove co-hosts.
- **Deferred**: Co-host invitations by link.

### 5. Traceability

- **PRD Anchors**: FR-016, MD-013, MN-006
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.
- Inferred, not in the PRD: co-hosts can edit draft details and mark attendance but cannot submit or publish.

## Open Questions

- None specific to this story; see PRD Open Questions.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
