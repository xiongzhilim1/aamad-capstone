# US-023 — Short onboarding for new participants

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements (FR-022)
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-023

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-023
- **Title**: Short onboarding for new participants
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want a short guided start that asks only what matters and lets me skip the rest, so that I reach a usable profile quickly and stay in control of what I share.

### 3. Acceptance Criteria

1. Onboarding has at most 4 screens, in this order: (1) display name and stage, (2) what I'm looking for, (3) interests and challenges, (4) discovery choice (AC-016).
2. Only display name and stage are required; screens 2 and 3 have a visible "Skip for now" option, and skipped fields can be completed later from the profile (US-002).
3. Screens 2 and 3 accept free text and offer the AI profile assistant (US-024); the user can also pick tags by hand without using AI.
4. Screen 4 offers directory consent, preselected to "not listed", with one sentence on who can see what; finishing onboarding never turns on directory or event-reconnection consent by itself (MN-001, MN-016).
5. A participant who leaves onboarding early can still opt in to event reconnection and the directory later (MN-016).
6. Every screen has loading and error states; if the assistant is unavailable, the screen falls back to manual tag entry (MC-006).

### 4. Scope Notes

- **In Scope for MVP**: The four-screen flow, skip-for-now, consent choice at the end.
- **Deferred**: Progress gamification, onboarding emails, importing a profile from LinkedIn or other sources.

### 5. Traceability

- **PRD Anchors**: FR-022, MD-018, MN-001, MN-016, AC-016
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md` (v1.1)
- `project-context/1.define/system-description.md`
- Operator answers, 2026-11-14 (onboarding length, consent timing)

## Assumptions

- Synthetic data only; no real users (MN-008).
- Screen order and wording are for `@ux.designer` to refine; the four steps and the defaults are the requirement.

## Open Questions

- None specific to this story; see PRD Open Questions.

## Audit

- 2026-11-14 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
