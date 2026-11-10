# User Stories — Index

MVP user stories for Entrepreneur Peers, Circles & Events. There is one file per story, derived from `../prd.md` and `../system-description.md`.

| ID | Title | Priority | Persona | Anchors |
|----|-------|----------|---------|---------|
| [US-001](US-001-persona-login-and-seed-data.md) | Log in as a synthetic persona | Must | Demo operator acting as any seeded user | FR-021, MD-017, MN-008, MN-011, NFR-001, NFR-009 |
| [US-002](US-002-create-profile.md) | Create a minimal profile with entrepreneur stage | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-001, MD-001, MN-004, MN-012 |
| [US-003](US-003-opt-in-directory.md) | Opt in to the people directory | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-002, MD-002, MN-001, AC-001 |
| [US-004](US-004-event-reconnection.md) | Reconnect with people from an event I attended | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-003, MD-003, MD-012, MN-007, AC-002 |
| [US-005](US-005-filter-discovery.md) | Discover people and circles with filters | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-004, MD-004, MC-005 |
| [US-006](US-006-ai-match-suggestions.md) | Get AI-suggested peers and circles with reasons | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-005, MD-005, MN-003, MN-004, MC-001–MC-005, MP-003, AC-007–AC-009, AC-015 |
| [US-007](US-007-send-connection-request.md) | Send or withdraw a connection request | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-006, MD-006, MN-002 |
| [US-008](US-008-respond-to-connection-request.md) | Accept or decline a connection request | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-006, MD-006, AC-003 |
| [US-009](US-009-mutual-contact-sharing.md) | Share contact details by mutual consent | Must | Connected pair of participants | FR-007, MD-007, MN-002, AC-004 |
| [US-010](US-010-block-and-report.md) | Block or report another user | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-008, MD-008, AC-005 |
| [US-011](US-011-discover-join-leave-circle.md) | Find, join and leave a circle | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-009, MD-009, MN-006, MN-007, AC-010, AC-011 |
| [US-012](US-012-organiser-submits-event.md) | Organiser drafts and submits an event | Must | Organiser | FR-012, MD-011, MN-005, AC-006 |
| [US-013](US-013-admin-approves-event.md) | Admin approves or rejects every event | Must | Admin | FR-013, FR-014, MD-011, MN-005, MP-002, AC-006 |
| [US-014](US-014-register-for-event.md) | Register for or withdraw from an event | Must | Participant (seasoned, new, or aspiring entrepreneur) | FR-015, MD-012, MN-007 |
| [US-015](US-015-confirm-attendance.md) | Organiser confirms who attended | Must | Organiser (or assigned co-host) | FR-015, MD-003, MD-012 |
| [US-016](US-016-facilitator-manages-circle.md) | Facilitator manages a circle | Should | Circle facilitator | FR-010, MD-009 |
| [US-017](US-017-faith-tagged-circles.md) | Optional faith-context circles | Should | Participant (seasoned, new, or aspiring entrepreneur) | FR-011, MD-010, MN-004 |
| [US-018](US-018-assign-co-hosts.md) | Organiser assigns co-hosts | Should | Organiser | FR-016, MD-013, MN-006 |
| [US-019](US-019-link-event-to-circle.md) | Link an event to a circle | Should | Organiser | FR-017, MN-006, MN-007 |
| [US-020](US-020-venue-directory.md) | Browse a curated venue directory | Should | Organiser and Admin | FR-018, MD-014, MN-009, MN-010, AC-012 |
| [US-021](US-021-follow-up-report.md) | Report a catch-up after connecting | Should | Connected pair of participants | FR-019, MD-015, AC-013 |
| [US-022](US-022-funnel-metrics.md) | View funnel metrics in separate units | Should | Admin | FR-020, MD-016, MP-005 |

Must stories cover the end-to-end journey (MP-004, AC-014): US-001 → US-013 → US-014 → US-015 → US-004 → US-006 → US-007 → US-008 → US-009 → US-011. Should stories (US-016 to US-022) are PRD P1.

## Sources
- `project-context/1.define/prd.md`; `project-context/1.define/system-description.md`

## Assumptions
- One story per PRD feature, except FR-006 (split into send and respond) and FR-015 (split into register and confirm attendance).

## Open Questions
- See PRD Open Questions OQ-01 to OQ-10.

## Audit
- 2026-11-10 — persona: `product-mgr` — action: `*create-stories` — 22 stories — runtime resolved: `crewai`
