---
name: ai-gateway-landscape
version: 1.0.0
description: AI Gateway ecosystem research — verify tech stacks, compare open-source and commercial offerings, curate language-specific alternatives.
author: coordinate35
---

# AI Gateway Landscape

Research and verify AI Gateway / LLM Gateway / Agent Gateway projects. Distinguish marketing claims from actual implementation languages and architectures.

## When to Use

- User asks "Is X company's AI Gateway written in Rust/Go/Python?"
- Need to verify a project's real tech stack vs marketing materials
- Curating alternatives for a specific language or architecture preference
- Evaluating enterprise vs open-source AI Gateway options

## Verification Workflow

### Step 1: Query GitHub Org Repos
```bash
curl -s "https://api.github.com/orgs/{org}/repos?per_page=100" | python3 -c "import sys,json; [print(r['name'], r.get('language',''), str(r.get('description',''))[:80]) for r in json.load(sys.stdin)]"
```

### Step 2: Search for Language-Specific Code
```bash
curl -s "https://api.github.com/search/code?q=org:{org}+{keyword}" | python3 -c "import sys,json; print('total:', json.load(sys.stdin).get('total_count',0))"
```

### Step 3: Read Raw README / Install Docs
```bash
curl -s "https://raw.githubusercontent.com/{org}/{repo}/main/README.md" | head -80
curl -s "https://raw.githubusercontent.com/{org}/{repo}/main/docs/install.md" | grep -i "image\|registry\|rust\|go\|envoy"
```

### Step 4: Check Workshop / Example Repos
Enterprise vendors often publish workshop repos with detailed install steps that reveal the true tech stack:
```bash
curl -s "https://api.github.com/search/repositories?q=org:{org}+{product}+workshop+OR+demo+OR+example"
```

### Step 5: Cross-Reference Helm Values / CRDs
Helm charts and Kubernetes CRDs expose the controller language and proxy type:
```bash
curl -s "https://raw.githubusercontent.com/{org}/{repo}/main/install/values.yaml" | grep -i "controller\|proxy\|envoy\|image"
```

## Common Architecture Patterns

| Pattern | Control Plane | Data Plane | Examples |
|:---|:---|:---|:---|
| **Envoy-based** | Go | Envoy (C++) | solo.io Gloo/Agentgateway, Kong, Istio |
| **Native Rust** | Rust | Rust/hyper | edgee, aisix, wirken |
| **Go-native** | Go | Go | TensorZero (gateway component) |
| **Wasm-extended** | Go | Envoy + Rust WASM | solo.io wasm filters |

## Pitfalls

1. **"AI Gateway" is a marketing umbrella** — the same vendor may have multiple products (API Gateway, AI Gateway, Agent Gateway) with different tech stacks. Verify the *specific product name*.
2. **Workshop repos leak enterprise details** — public workshop repos often contain install docs, CRD definitions, and Helm values that reveal the true architecture. Search for `{product}-workshop` or `{product}-demo` repos.
3. **WASM extensions ≠ Rust product** — A Go/Envoy product may support Rust WASM filters, but the core is not Rust. Distinguish "supports Rust" from "written in Rust".
4. **License requirements** — Enterprise products (solo.io Enterprise Agentgateway) require trial license keys even for POC. Factor this into evaluations.

## References

- `references/rust-ai-gateways.md` — Curated list of Rust AI Gateway projects with stars and descriptions
- `references/solo-io-agentgateway.md` — Verified tech-stack details for solo.io products
