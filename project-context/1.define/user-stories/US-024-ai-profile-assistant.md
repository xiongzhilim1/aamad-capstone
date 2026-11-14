# US-024 — Describe myself in my own words; the AI drafts my profile fields

## Context & Instructions
User story produced by `@product-mgr` `*create-stories` from the PRD and system description. Scope is limited to the PRD; nothing is invented here.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md` §4 Functional Requirements (FR-023, FR-024)
**System Description** (optional): `project-context/1.define/system-description.md`
**Story ID**: US-024

## User Story Structure — Generate All Sections Below

### 1. Story Identity

- **ID**: US-024
- **Title**: Describe myself in my own words; the AI drafts my profile fields
- **Priority**: Must
- **Persona**: Participant (seasoned, new, or aspiring entrepreneur)

### 2. Narrative

As a participant, I want to write about my business, my challenges and what I'm looking for in my own words and get a structured draft I can check, so that my profile is accurate without filling in a long form, and I decide what is public and what is used only for matching.

### 3. Acceptance Criteria

1. Given free text, when I press "Summarise", then I see a draft of tags (interests, challenges, looking-for, optional industry) plus a one-line summary, and nothing is saved yet (AC-017, MN-013).
2. I can edit any tag or the summary, remove items, add tags by hand, accept the draft, or discard it; only accepted fields are saved.
3. Every drafted tag traces to words in my text; the assistant never adds facts I did not write (MN-014).
4. Given my text mentions faith, health or family, then the draft contains no faith or sensitive tag; faith context is set only through its own optional field (AC-018, MN-004).
5. For each saved field I choose *shown on profile* or *matching only*. *Matching only* fields never appear to other participants in UI or API (AC-019). They are visible to the admin and to facilitators of circles I belong to or have applied to, each view is logged, and the choice screen says so (AC-020, MD-022).
6. My raw free text is never shown to anyone else, never sent to the suggestion model, and is deleted once I accept or discard the draft (MN-015).
7. If the assistant fails or times out, I see a clear message and can pick tags by hand (MC-006).
8. Using or skipping the assistant has no effect on my event-reconnection or directory consent (MN-016).

### 4. Scope Notes

- **In Scope for MVP**: Summarise → review → accept or discard; per-field visibility; manual fallback.
- **Deferred**: Re-summarising automatically when the profile changes; multilingual input (for example Cantonese text); importing text from other sites.

### 5. Traceability

- **PRD Anchors**: FR-023, FR-024, MD-019, MD-020, MD-021, MD-022, AC-020, MN-004, MN-013 to MN-016, MC-006, MP-007, AC-017 to AC-019
- **Related SFS**: to be created by `@system.arch` (`project-context/1.define/sfs/`)

## Sources

- `project-context/1.define/prd.md` (v1.1)
- `project-context/1.define/system-description.md`
- Operator answer, 2026-11-14: free text, summarised by an AI assistant, verified by the user, who decides what is displayed and what is used only for matching.

## Assumptions

- Synthetic data only; no real users (MN-008).
- "More context to the team for matching" means the suggestion model, the admin, and own-circle facilitators (OQ-11, resolved 2026-11-14).
- Deleting raw text after the user accepts or discards the draft is a data-minimisation default chosen by `@product-mgr`, not an explicit operator instruction.

## Open Questions

- MP-007 field-agreement threshold for the assistant eval (proposed: the same 80% as OQ-02).

## Audit

- 2026-11-14 — persona: `product-mgr` — action: `*create-stories` — runtime resolved: `crewai`
- 2026-11-14 — persona: `product-mgr` — action: `*create-stories` (update) — AC5 revised for staff access (OQ-11).
