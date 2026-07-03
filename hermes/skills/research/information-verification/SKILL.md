---
name: information-verification
description: |
  Verify facts before stating them. Choose authoritative primary sources over secondary aggregators.
  Trigger when: searching for event/competition details, verifying claims, fact-checking, or any time
  the user asks "who/what/when/where" about a specific entity.
tags: [research, fact-checking, source-selection, verification]
---

# Information Verification

## Core Principle

**Go to the primary source first.** When searching for information about an entity (event, organization, product), the entity's own platform is the authoritative source — not third-party aggregators, video platforms, or social media.

## Source Selection Heuristic

| You want to know... | Search here first |
|---|---|
| Event schedule / organizer | The organizer's own platform (e.g., 虎牙 for 虎牙-sponsored events) |
| Official rules / announcements | The entity's official website or app |
| Match results / scores | The platform that broadcast it |
| Community discussion / clips | Bilibili, NGA, Tieba (secondary) |

## Pitfalls

1. **Bilibili is not a primary source.** It's a video platform with user-generated content. Video titles may contain the information you need, but they are not authoritative. Use them as leads, not as answers.

2. **Inertial searching: don't stay on a platform just because it worked before.** When Bilibili returns rich results for one query (e.g., match videos), it's tempting to keep searching there for every related question. But the right source depends on the *question type*: match videos → Bilibili is fine; organizer/schedule → go to the organizer's platform. Ask yourself: "Is this platform the authoritative source for *this specific question*?"

3. **Don't assume continuity between versions.** S2 is not necessarily the same as S1. Organizers, formats, and platforms can change between editions. Verify each edition independently.

4. **Bing/Google returning empty results is a signal.** If a search engine repeatedly returns no results for your query, the problem may be your search terms or your choice of search platform — not that the information doesn't exist. Try the entity's own site directly.

5. **Don't state assumptions as facts.** If you can't verify something, say so explicitly. "I couldn't find this, but based on S1..." is acceptable. "The organizer is X" without verification is not. When the user challenges an assumption, admit the gap immediately — don't defend the unverified claim.

6. **When you find a lead on a secondary platform, follow it to the primary source.** E.g., seeing "虎牙不朽杯" in a Bilibili video title should trigger: "Go to huya.com now." Don't treat the video title as the answer — treat it as a signpost pointing to where the answer lives.

7. **Disambiguate ambiguous event references before answering.** When a user mentions an event that could refer to multiple timeframes or instances (e.g., "美伊战争", "the Fed rate cut", "the election"), do NOT assume which one they mean. List the possible interpretations and ask them to clarify which specific event/timeframe they're asking about. Answering about 2024 when they meant 2026 March wastes the entire response and erodes trust. This is especially critical for geopolitical/economic events where the same parties may have had multiple conflicts or interactions over time.

## Tech/Policy Claims Analysis (from archived `tech-policy-claims-analysis`)

When analyzing technology or industrial-policy claims, apply a four-layer framework to peel back marketing narratives:

### Layer 1: Technical Capability — Three Tiers
- **Physical layer limits**: What the standard physically enables
- **Commercial deployment reality**: What's at scale vs. lab/demo
- **Marketing claims**: What's said but not delivered

Key question: "Physical impossibility for the old tech, or just 'not deployed yet'?"

### Layer 2: Replacement Logic — What Does It Actually Replace?
- "替代什么" matters more than "能做什么"
- Wired almost always more reliable; wireless wins only for mobility/flexibility

### Layer 3: Policy/Industrial Drivers — Ranked by Real Importance

| Driver | Identify By |
|--------|-------------|
| Standards/patents leverage | Do domestic firms hold key SEP? |
| Supply chain security | Chokepoint risk in this sector? |
| Keynesian investment | Growth slowdown? SOE can absorb cost? |
| Technical merit | Marginal improvement large enough alone? |

Key test: "If purely a technical decision, would other countries deploy at the same speed?" If no → real drivers are non-technical.

### Layer 4: Geopolitical Context
- Who benefits from the narrative?
- What happens if the country does NOT invest?
- Counter-examples: other countries opting out → ROI alone doesn't justify

### Workflow
1. **Initial Answer with Explicit Uncertainty** — tag each claim: [标准事实] / [行业共识] / [待验证] / [分析判断]
2. **Expect User Challenge** — don't get defensive; the challenge often points to a deeper structural question
3. **Peel Back to Structural Drivers** — shift from "what can it do" to "why is it being pushed"
4. **Honest Conclusion** — "X is primarily driven by [policy/strategic reason], not [technical reason]"

### Data Access Failure Protocol
When government/industry reports blocked by anti-crawling/Cloudflare:
1. Admit explicitly: "未能现场访问X，以下基于行业公开认知"
2. Tag confidence: distinguish "know" from "believe based on patterns"
3. Do NOT fabricate numbers, no "approximately X" from memory
