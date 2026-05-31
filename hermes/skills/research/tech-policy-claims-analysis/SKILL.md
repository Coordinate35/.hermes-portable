---
name: tech-policy-claims-analysis
description: Analyze tech/policy claims by peeling back marketing narratives to reveal real technical capabilities and strategic motivations. Distinguishes technical capability vs commercial reality vs policy intent vs geopolitical rationale.
author: Assistant
created: 2026-05-31
tags: [technology, policy, claims-verification, industrial-policy, skepticism]
---

# Tech/Policy Claims Analysis

## When to Use

- User asks "X能做Y不能做的事吗" about a technology (e.g., 5G vs 4G)
- User asks "为什么大力发展X" about an industrial/policy initiative
- User challenges a technology narrative or marketing claim
- Any question where the surface technical explanation seems insufficient

## Core Framework: Four Layers

### Layer 1: Technical Capability — Three Tiers
- **Physical layer limits**: What the standard physically enables (e.g., 5G NR mini-slot → 1ms; 4G HARQ → ~10ms floor)
- **Commercial deployment reality**: What's at scale vs. lab/demo
- **Marketing claims**: What's said but not delivered

Key question: "Physical impossibility for the old tech, or just 'not deployed yet'?"

### Layer 2: Replacement Logic — What Does It Actually Replace?
- 5G in factories replaces WiFi for mobile units, NOT industrial Ethernet for fixed equipment
- Comparing 5G to WiFi ≠ comparing 5G to wired PROFINET
- Wired almost always more reliable; wireless wins only for mobility/flexibility

Principle: "替代什么" matters more than "能做什么"

### Layer 3: Policy/Industrial Drivers — Ranked by Real Importance

| Driver | Identify By | Example |
|--------|-------------|---------|
| Standards/patents leverage | Do domestic firms hold key SEP? | China 5G → Huawei/ZTE patents vs Qualcomm 4G royalties |
| Supply chain security | Chokepoint risk in this sector? | Post-Huawei sanctions → 5G as exportable tech capability |
| Keynesian investment | Growth slowdown? SOE can absorb cost? | 5G buildout during real estate downturn |
| Technical merit | Marginal improvement large enough alone? | 4G→5G << 3G→4G |

Key test: "If purely a technical decision, would other countries deploy at the same speed?" If no → real drivers are non-technical.

### Layer 4: Geopolitical Context
- Who benefits from the narrative?
- What happens if the country does NOT invest? (patent dependency, supply chain risk)
- Counter-examples: other countries opting out → ROI alone doesn't justify

## Workflow

### Step 1: Initial Answer with Explicit Uncertainty
- Tag each claim: [标准事实] / [行业共识] / [待验证] / [分析判断]
- If data access blocked, SAY SO upfront

### Step 2: Expect User Challenge — It's a Feature
- Don't get defensive
- Publicly correct overstatements (e.g., "5G颠覆有线" → "5G补位移动场景")
- The challenge often points to a deeper structural question

### Step 3: Peel Back to Structural Drivers
- Shift from "what can it do" to "why is it being pushed"
- Apply Layer 3 framework
- Present as ranked list, not conspiracy theory

### Step 4: Honest Conclusion
"X is primarily driven by [policy/strategic reason], not [technical reason]. The technical improvement is [marginal/significant] but alone doesn't justify [investment scale]."

## Data Access Failure Protocol

When government/industry reports blocked by anti-crawling/Cloudflare:
1. Admit explicitly: "未能现场访问X，以下基于行业公开认知"
2. Tag confidence: distinguish "know" from "believe based on patterns"
3. Offer to re-verify: "如果要拿具体数字去用，建议换条路再查"
4. Do NOT fabricate numbers, no "approximately X" from memory

## Pitfalls

- ❌ Accepting industry/marketing framing at face value
- ❌ Listing capabilities without asking "what does this replace?"
- ❌ Explaining state investment purely through technical merit when ROI doesn't justify
- ❌ Fabricating data when primary sources blocked
- ❌ Getting defensive when challenged — challenge IS the real question
- ❌ Treating policy-driven investment as irrational — may be rational strategically even if ROI-negative at project level

## Good Practices

- ✅ Ask "what does this replace?" before "what can this do?"
- ✅ Separate physical impossibility from commercial non-deployment
- ✅ Rank drivers by actual importance, not official narrative
- ✅ Use cross-country comparison as natural experiment
- ✅ Publicly correct your own overstatements
- ✅ Admit data access failures rather than working around silently

## Output Format on QQ

- Structured comparisons/ranked lists → text (语音说不清楚)
- Short confirmations/single answers → 语音
- Default to text when answer requires "清单+对比"

## Related Skills

- `investment-research-verification` — epistemic honesty for investment claims (this skill extends the same stance to tech/policy)
- `luqiyuan-macro-analysis` — for macro/financial drivers
