# US-001 — Log in as a synthetic persona

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-001

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-001
- **Title**: Log in as a synthetic persona
- **Priority**: Must
- **Persona**: Demo operator acting as any seeded user

### 2. Narrative

As a demo operator, I want to pick a seeded synthetic persona to act as, so that I can demonstrate every role without real accounts or real personal data.

### 3. Acceptance Criteria

1. Given the login screen, when I pick a seeded persona, then the server creates a session for that persona and every later request uses the session's actor.
2. Given a request carrying a different actor id in its body, query or headers, when the server handles it, then the client-supplied id is ignored and the session actor is used (MN-011, PRD-v0 T12).
3. The seed contains participants at all three stages, at least one organiser, one admin and one facilitator; at least one approved and one pending event; one faith-tagged and one general circle; and at least one blocked and one declined case (MD-017).
4. Every seeded record is marked synthetic, and the UI shows a visible "synthetic data" label (MN-008, NFR-009).

### 4. Scope Notes

- **In Scope for MVP**: Persona picker, server-side session, seed dataset.
- **Deferred**: Production authentication, real accounts, password or SSO login (PRD §4 P2).

### 5. Traceability

- **PRD Anchors**: FR-021, MD-017, MN-008, MN-011, NFR-001, NFR-009
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
