# US-006 — Get AI-suggested peers and circles with reasons

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-006

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-006
- **Title**: Get AI-suggested peers and circles with reasons
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to ask for suggested peers and circles and see why each was suggested, so that I can find good matches faster and decide for myself whether to reach out.

### 3. Acceptance Criteria

1. Suggestions are generated only when I press "Suggest"; nothing runs in the background (MC-001).
2. Every suggested person is discoverable to me, is not me, and is not blocked either way; every suggested circle is visible to me (AC-007).
3. Every suggestion shows a reason that names at least one field we share; reasons not grounded in real profile data are removed before display (guardrail).
4. Given my faith matching opt-in is off or I have no faith context, then faith is excluded from model input and no reason mentions faith (AC-008).
5. Suggestions never send requests, join circles or change any state; I act through the normal buttons (MN-003).
6. Given the model fails, times out or is over budget, then I see a clear message and a link to filter discovery (AC-009).
7. Suggestions are clearly labelled as AI-generated, and a loading state appears while they are generated (p95 target in MC-003).

### 4. Scope Notes

- **In Scope for MVP**: On-demand suggestions for peers and circles; reasons; graceful fallback.
- **Deferred**: Autonomous matchmaking, background or bulk runs, notifications of new matches.

### 5. Traceability

- **PRD Anchors**: FR-005, MD-005, MN-003, MN-004, MC-001–MC-005, MP-003, AC-007–AC-009, AC-015
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- OQ-01: spend cap and latency target.
- OQ-02: eval gold set and relevance threshold.
- OQ-03: which matching signals are allowed.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
