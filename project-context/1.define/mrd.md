# Market Research Document (MRD) — Entrepreneur Peers, Circles & Events

## Context & Instructions
Discovery-stage MRD produced by `@product-mgr` `*create-mrd`. It is built from the operator's 2026-11-10 direction, `system-description.md`, and the owner draft `MRD-v0.md`.
**Status:** this is a discovery brief, not validated market research. No external sources were consulted in this action. Market size, growth, competitor features and willingness to pay are **not established**, and they are marked as such rather than estimated. The template's research-quality bar (15–20 cited sources, quantitative evidence) is **not met**; see Assumptions and OQ-M01.
Evidence labels used below: **[reported]** means the operator or organiser said it; **[hypothesis]** means it is untested; **[decision]** means the operator chose it; **[unknown]** means it has not been researched.

## Research Query Structure

**Primary Focus**: A web app that helps entrepreneurs turn an in-person event into lasting peer connections and ongoing support circles. It starts with a faith-centred entrepreneur community in Hong Kong and widens to all entrepreneurs.
**Selected Runtime** (optional for research; required later in Build): crewai

## Research Dimensions — Investigate All Areas Below

### 1. Market Analysis & Opportunity Assessment

- **Market Size**: [unknown] No count of Hong Kong entrepreneurs, faith-centred entrepreneur groups, or meetup attendees has been gathered. No TAM, SAM or SOM is asserted.
- **Growth Trends**: [unknown] No growth data has been gathered.
- **Market Gaps**: [hypothesis] Attendees who want to reconnect miss exchanging contacts (MRD-v0 H1). Ongoing support groups are scattered across churches and business networks; this is a working hypothesis, not a counted fact (MRD-v0 §3).
- **Target Audience**:
  - *Beachhead* [decision]: a faith-centred (Christian) entrepreneur community in Hong Kong that the operator reports already exists [reported]. Its size, how active it is, and how it relates to the coffee meetups are [unknown] (OQ-M02).
  - *Expansion* [decision]: all entrepreneurs, in three stages: seasoned, new, and thinking about starting. Faith is optional and self-described; faith-based circles are one kind of circle (system-description MD-010).
  - *Pain points* [hypothesis]: losing touch after events; wanting ongoing peer support and familiar faces (MRD-v0 H1, H3); wanting meetups that fit shared challenges and practical preferences (H4).
  - *Willingness to pay* [unknown]: a cafe entrance fee that includes a drink exists [reported], but it is not evidence that people would pay for a platform (MRD-v0 §7).
- **Business Case**: [unknown] No business model, return on investment or monetisation choice has been made. The capstone's value is as a learning project (MRD-v0 §8).
- **Competitive Landscape**: [unknown] Luma, Meetup, Timeleft and Lectures After Dark are inspiration only [reported], and their features have not been audited. Current workarounds are WhatsApp private messages, organiser records and manual counts, LinkedIn or contact exchange, recurring coffee meetups, and speaker and cafe word of mouth [reported]. It has not been established that these are inadequate.

### 2. Technical Feasibility & Requirements Analysis

- **Runtime Capabilities**: The CrewAI runtime is used for one narrow job: on-demand peer and circle suggestions from opted-in profiles, with grounded reasons (FR-005). Everything else is ordinary app logic. Whether CrewAI is the best choice is left to `@system.arch`.
- **Agent Architecture Patterns**: Not selected here; the SAD Pattern Decision belongs to `@system.arch`. The constraints that apply are: the AI has no write path (MN-003), faith data is excluded unless the user opts it into matching (MN-004), and filter discovery is the fallback (MC-005).
- **Integration Requirements**: None in the MVP. External connectors (Luma, Meetup, social platforms), messaging and payments are deferred; no API availability is assumed (MRD-v0 §4).
- **Scalability Considerations**: Not a driver for a synthetic capstone. Suggestion cost scales with the size of the candidate set, so it is capped before model input (MC-002).
- **Technical Risks**: privacy leaks across circle, event and pair boundaries; AI suggestions that are ungrounded or biased; reasons that infer or mention faith; model cost overruns. Mitigations are in system-description MN-*, MP-003 and MC-*.
- **Infrastructure Needs**: [unknown] The cost projection depends on the spend cap (system-description OQ-01).

### 3. User Experience & Workflow Analysis

- **User Journey Mapping**: admin approves event → participant registers → attends (organiser confirms) → opts in to reconnect → views event-scoped peers and AI suggestions → sends a request → mutual accept → mutual contact share → optional follow-up report → discovers and joins a circle for ongoing support.
- **Interface Requirements**: a responsive web app; an opt-in directory; a discovery tool (filters plus "suggest"); requests and connections; circles; events; an admin approval queue; the venue directory.
- **Automation Opportunities**: *Partial*: AI ranks and explains suggestions. *None*: sending requests, accepting, sharing contacts, joining circles, publishing events; these are always human actions.
- **Human-in-the-Loop**: the admin approves every event before it is published [decision]; recipients alone decide on requests; topic and speaker choice stays with organisers [reported].
- **Success Metrics** (MRD-v0 §5, PRD-v0 §8): opportunities offered → opt-ins → requests → acceptances → pairs reporting a first and second catch-up, each counted in its own unit with its own denominator. Circle continuity means returning to the same circle plus a usefulness signal; the definition is pending. No numeric targets have been agreed.
- **User Adoption Factors** [hypothesis]: *Enablers*: an existing trusted community and familiarity from repeat events. *Barriers*: privacy concern, low perceived need, reluctance to adopt "another app", unwanted approaches, and the effort of responding (MRD-v0 §5 interpretations).

### 4. Production & Operations Requirements

- **Deployment Architecture**: Out of MRD scope; deferred to SAD and deploy.md. The capstone runs on synthetic data only.
- **Monitoring & Observability**: funnel units in system-description MD-016; AI prompt traces and eval logs (NFR-006).
- **Security Considerations**: opt-in visibility only; contacts are never disclosed automatically; server-side authorization; faith is voluntary, never inferred and never verified; coarse locations only. A real-user pilot additionally needs consent wording, retention and deletion, and a block and report process with a defined response (PRD-v0 S01, S09, S10).
- **Maintenance & Updates**: requirements are versioned rather than silently rewritten (PRD-v0 §11).
- **Cost Structure**: [unknown] The platform cost and the model spend cap are unset.
- **Risk Assessment**: see the Risk Assessment Matrix.

### 5. Innovation & Differentiation Analysis

- **Unique Value Propositions** [hypothesis]: (1) reconnection scoped to an event, private and mutual, with nothing visible by default; (2) a path from a one-off event into ongoing circles; (3) a faith-friendly setting where faith is optional, not a gate (MRD-v0 H5, widened by the operator's decision).
- **Emerging Technologies**: LLM-based suggestions with explanations, gated by evals; the AI comes after a filter-based baseline that still works without it.
- **Patent Landscape**: [unknown] Not investigated.
- **Future Trends**: [unknown] Not investigated.
- **Partnership Opportunities** [reported]: cafe partners and speakers already spread the word about events. Churches and business networks are possible partners [hypothesis]. No agent is authorised to contact any partner.
- **Monetization Strategies**: [unknown] None selected. Business coaching and mentorship need separate evidence (MRD-v0 §6).

## Output Format Requirements

### Executive Summary (2-3 paragraphs)

- **Market Opportunity**: The opportunity is real but unquantified. In Hong Kong there is a faith-centred entrepreneur community the operator already has access to [reported], and recurring coffee meetups where attendees sometimes, but not usually, follow up afterwards [reported]. Whether attendees want a tool to reconnect and form circles is untested (H1–H5). No market size, competitor audit or willingness-to-pay evidence exists yet.
- **Technical Feasibility**: Building a synthetic MVP is feasible and low-risk. Most of the work is ordinary access-controlled web app logic. The one AI capability, suggestions, is narrow, has no write access, is gated by evals, and has a fallback that works without the model. The main technical risk is a privacy boundary failing, not AI complexity.
- **Recommended Approach**: Start with the HK faith-centred community as the beachhead, because the operator has existing trust and access there, while designing the product for all entrepreneurs, with faith as an optional profile field and circle type. Build the synthetic capstone now. Separately, the owner should run the low-cost manual reconnection experiment (MRD-v0 §5) at a real gathering to test H1–H3 before investing in a real-user app.

### Detailed Findings by Dimension

**Dimension 1 — Market**
- *Key Insights*: (1) A beachhead community exists in HK [reported]. (2) Following up after events is "not typical", but familiarity builds through repeat events [reported]. (3) Current workarounds exist, and it has not been shown that they are inadequate.
- *Data Points*: None quantitative. Organiser reports are qualitative and not measured.
- *Source Citations*: MRD-v0 §2–§4 (2026-11-08); operator direction (2026-11-10).
- *Implications*: The product must earn adoption against WhatsApp and LinkedIn; the design keeps conversations off-platform and focuses on permissioned reconnection and circles.

**Dimension 2 — Technical**
- *Key Insights*: (1) The AI is used narrowly, for suggestions only. (2) Privacy boundaries are the core of the build. (3) No external integrations are needed for the MVP.
- *Data Points*: None. Starter-test counts in PRD-v0 §9 refer to code not in this repo.
- *Source Citations*: system-description.md (2026-11-10); PRD-v0 §7, §9–§10.
- *Implications*: SAD should weight authorization and data visibility above agent orchestration.

**Dimension 3 — UX**
- *Key Insights*: (1) Nothing is visible by default and every step needs mutual consent. (2) RSVP, attendance, membership and contact sharing are different things. (3) Familiarity may matter more than one-to-one matching.
- *Data Points*: None collected.
- *Source Citations*: MRD-v0 §3, §5–§6; PRD-v0 §4–§6.
- *Implications*: If evidence shows that familiarity is the main value, simplify toward circles and recurring events (MRD-v0 §6).

**Dimension 4 — Operations**
- *Key Insights*: (1) The synthetic capstone defers real-user obligations. (2) The admin event gate gives a human control point. (3) Organiser workload is unmeasured.
- *Data Points*: None.
- *Source Citations*: MRD-v0 §7; PRD-v0 §7, §9.
- *Implications*: Real-user gates (S01, S09, S10) must be cleared before any pilot.

**Dimension 5 — Differentiation**
- *Key Insights*: (1) Event-scoped, mutual reconnection. (2) A path from events to circles. (3) A setting where faith is optional.
- *Data Points*: None. Demand for these differentiators is untested.
- *Source Citations*: MRD-v0 H2–H5; operator direction (2026-11-10).
- *Implications*: Messaging to the beachhead can lead with faith-centred fellowship; the product itself must not require faith.

### Critical Decision Points

- **Go/No-Go Factors**: *Capstone*: go, because it is a reversible learning prototype on synthetic data. *Real-user pilot*: no-go until the manual experiment shows voluntary opt-in and mutual value, and until the real-user safeguards (S01, S09, S10) are in place.
- **Technical Architecture Choices**: These belong to `@system.arch`. The MRD's inputs are: a responsive web app; a narrow AI suggestion capability on CrewAI with no write path and an eval gate; a filter-discovery fallback.
- **Market Positioning**: Beachhead: a faith-centred entrepreneur community in Hong Kong. Positioning: "turn the people you met into ongoing peers and circles." Expansion: all entrepreneurs in HK, with faith optional.
- **Resource Requirements**: [unknown] The capstone deadline, model spend cap and team size are not given (system-description OQ-01, OQ-08).

### Risk Assessment Matrix

- **High Risk**
  - Privacy failures: exposing attendees, contacts or private pair data. *Mitigation*: system-description MN-001, MN-002, MN-006, MN-011 and their tests.
  - Faith treated as a gate or inferred, which alienates the wider audience or harms users. *Mitigation*: MN-004, AC-008, and the optional field and circle tag.
  - Low genuine need, where workarounds are good enough. *Mitigation*: the manual experiment before investing in real users.
- **Medium Risk**
  - AI suggestions that are irrelevant or not explained. *Mitigation*: MP-003 eval gate and grounded reasons.
  - Unwanted approaches or burden of responding. *Mitigation*: block, report, private declines, request expiry (OQ-06).
  - Admin approval becoming a bottleneck. *Mitigation*: monitor how long approvals take; [unknown] admin capacity.
- **Low Risk**
  - Model cost overrun in a synthetic capstone. *Mitigation*: on-demand calls only, caps (MC-001–MC-004).
  - Venue directory accuracy. *Mitigation*: unknown fields shown as "Unknown"; synthetic entries are labelled.

### Actionable Recommendations

- **Immediate Next Steps**: Run `*create-prd` from system-description.md, using PRD-v0 as a source. Answer system-description OQ-01 (spend cap) and OQ-02 (eval threshold) before Build.
- **Short-term Priorities**: Build the synthetic MVP. Separately, the owner should set the cohort, observation window and keep/change/stop criteria for the manual experiment before collecting any results (MRD-v0 §5).
- **Long-term Strategy**: If the manual experiment shows value, plan a real-user pilot within the HK beachhead after the safeguards are in place. Then widen to all entrepreneurs. Consider connectors, bookings and coaching only with separate evidence.

## Research Quality Requirements

Not met in this version. There are 0 external sources; the evidence is the operator's reports and decisions plus owner drafts. External research is OQ-M01.

## Sources

- Operator direction in chat, 2026-11-10: widen to all entrepreneurs, start with the faith-centred community that already exists in Hong Kong, and refer to the owner's MRD.
- Operator brief and elicitation answers, 2026-11-10 (recorded in `system-description.md`).
- `project-context/1.define/system-description.md` (2026-11-10).
- `project-context/1.define/MRD-v0.md`: owner discovery draft, 2026-11-08 (observations §2, hypotheses §3, alternatives §4, experiment §5–§6, commercial unknowns §7).
- `project-context/1.define/PRD-v0.md`: owner draft, 2026-11-08 (roles, safeguards, funnel contract).

## Assumptions

- Research was abbreviated: no web research was done in this persona action, and every quantitative field is marked [unknown] rather than estimated.
- The HK faith-centred community is Christian, consistent with MRD-v0 §1. Its size and how it relates to the coffee meetups are unknown.
- The coffee meetups in MRD-v0 §2 are assumed to take place in Hong Kong (inference; OQ-M02).
- No inference is made about any individual attendee's faith (kept from MRD-v0 §1).

## Open Questions

- **OQ-M01** Should external research be done (HK entrepreneur population, faith-based business networks in HK, a competitor feature audit of Luma, Meetup and Timeleft) to meet the template's evidence bar? This needs web access, which is outside this persona's declared tools.
- **OQ-M02** How big and how active is the HK faith-centred community, and is it the same group as the coffee-meetup regulars?
- **OQ-M03** What counts as the beachhead-to-expansion trigger, meaning what evidence would justify opening to all entrepreneurs?
- **OQ-M04** Will the manual demand experiment run, and with which cohort, observation window and keep/change/stop criteria (MRD-v0 §5)?
- **OQ-M05** Is there any monetisation intent beyond the capstone (MRD-v0 §7)?

## Audit

- 2026-11-10 — persona: `product-mgr` — action: `*create-mrd` — output: `project-context/1.define/mrd.md` — runtime resolved: `crewai` (env `AAMAD_TARGET_RUNTIME`, matches `aamad.config.yml`) — no external sources consulted; research-quality bar not met (OQ-M01).
