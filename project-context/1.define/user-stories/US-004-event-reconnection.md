# US-004 — Reconnect with people from an event I attended

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-004

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-004
- **Title**: Reconnect with people from an event I attended
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to opt in, after an event I attended, to see other opted-in attendees of that event, so that I can reconnect with people I met even if we did not exchange contacts.

### 3. Acceptance Criteria

1. Given an approved event has ended and the organiser has confirmed I attended, when I open the event, then I can opt in to its reconnection list.
2. Given A and B both attended and opted in, when A opens the reconnection list, then B appears; C, who registered but was not confirmed as attending, does not appear (AC-002).
3. Opting in to an event's reconnection list does not change my global directory consent (MN-001).
4. People I blocked, or who blocked me, do not appear (AC-005).
5. From the list, I can send a connection request (US-007).

### 4. Scope Notes

- **In Scope for MVP**: Per-event opt-in; reconnection list.
- **Deferred**: A time limit on reconnection after the event (not decided).

### 5. Traceability

- **PRD Anchors**: FR-003, MD-003, MD-012, MN-007, AC-002
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/system-description.md`
- `project-context/1.define/PRD-v0.md` (owner draft, where cited)

## Assumptions

- Synthetic data only; no real users (MN-008).
- See PRD Assumptions for organiser-confirmed attendance and circle creation rights.

## Open Questions

- Should the event reconnection list close after a set period? Not specified in the PRD.

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
