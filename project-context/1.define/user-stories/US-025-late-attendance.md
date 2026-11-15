# US-025 — Say "I was there" after joining the app

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 (FR-025, FR-026, FR-027)
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-025

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-025
- **Title**: Say "I was there" after joining the app
- **Priority**: Should
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur) who joined the app after attending an event

### 2. Narrative

As a participant who only joined the app after an event, I want to record that I attended, using the event code the host shared or by asking the host to confirm, so that I can reconnect with the people I met there.

### 3. Acceptance Criteria

1. On an approved event that has started, a participant who is not marked attended sees **I was there**, even without a prior registration.
2. **With a code**: entering the code the host shared, within 7 days after the event ends, confirms attendance at once; the *After the event* tab then offers the reconnection opt-in (AC-022).
3. **Without a code**: the claim is sent to the host, and the participant sees "Waiting for the host to confirm"; no attendee data is shown while it is pending (AC-021, MN-017).
4. A wrong, expired or disabled code changes nothing and explains what to do next ("Ask the host for the current code, or send a claim instead"); the sixth wrong attempt within an hour is refused (MD-024).
5. When the host declines, the participant sees "The host couldn't confirm your attendance", and nothing about the attendees is revealed.
6. Confirmed attendance never opts anyone in by itself; reconnection still needs the person's own opt-in (US-004, MN-001).
7. Claims and codes work only for approved events; an unpublished event stays not-found (MN-005, MN-017).
8. The scenario "five friends find the app after a cafe meetup, claim attendance, the host confirms, they opt in and send each other requests" passes end to end on seed data.

### 4. Scope Notes

- **In Scope for MVP**: The "I was there" claim; code entry; pending, confirmed and declined states; past-dated events created by organisers (US-012).
- **Deferred**: QR-code check-in; claim expiry; reminders to hosts; abuse handling beyond host decline and code rotation.

### 5. Traceability

- **PRD Anchors**: FR-025, FR-026, FR-027, MD-023, MD-024, MD-025, MN-017, AC-021, AC-022, AC-023
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md` (v1.2)
- `project-context/1.define/system-description.md`
- Operator decisions, 2026-11-15: include late attendance now; claim plus event code (options 1 + 2); past-dated events with admin approval.

## Assumptions

- Synthetic data only; no real users (MN-008).
- The 7-day code window and the limit of 5 attempts per hour are proposed values (OQ-12).

## Open Questions

- OQ-12: confirm the code window and the attempt limit.

## Audit

- 2026-11-15 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
