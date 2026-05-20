# solo.io AI/Agent Gateway — Verified Tech-Stack Details

**Verification date:** 2026-05-20  
**Sources:** GitHub org repos, public workshop repos, install docs

## Products Overview

solo.io offers multiple gateway products. Do not confuse them:

| Product | What it is | Core Tech |
|:---|:---|:---|
| **Gloo Gateway** | Kubernetes-native API Gateway (general purpose) | Go (control plane) + Envoy (C++ data plane) |
| **Gloo AI Gateway** | AI/LLM routing layer on top of Gloo Gateway | Same as Gloo + AI-specific Envoy filters |
| **Enterprise Agentgateway** | Agent-native gateway (MCP, Guardrails, Identity) | Go (control plane) + Envoy (C++ data plane) |

## Enterprise Agentgateway (Detailed)

### Architecture
- **Control plane:** Go (`enterprise-agentgateway` controller)
- **Data plane:** Envoy Proxy (`agentgateway-proxy` pods)
- **API:** Kubernetes Gateway API v1.4–1.5 + solo.io custom CRDs
- **Deployment:** Helm chart, requires license key

### CRDs
```
agentgatewaybackends               agbe    agentgateway.dev/v1alpha1
agentgatewayparameters             agpar   agentgateway.dev/v1alpha1
agentgatewaypolicies               agpol   agentgateway.dev/v1alpha1
enterpriseagentgatewayparameters   eagpar  enterpriseagentgateway.solo.io/v1alpha1
enterpriseagentgatewaypolicies     eagpol  enterpriseagentgateway.solo.io/v1alpha1
authconfigs                        ac      extauth.solo.io/v1
ratelimitconfigs                   rlc     ratelimit.solo.io/v1alpha1
```

### System Requirements (v2026.5.0)
- Kubernetes 1.31–1.35
- Helm ≥ 3.12
- Gateway API CRDs 1.4–1.5
- Istio 1.26–1.29 (optional, for waypoint/ambient features)

### Resource Sizing (POC)
| Component | CPU Request | CPU Limit | MEM Request | MEM Limit |
|:---|:---:|:---:|:---:|:---:|
| Controller | 500m | 1 | 512Mi | 1Gi |
| Proxy (x2) | 100m | 500m | 128Mi | 512Mi |

### Key Capabilities (from workshop docs)
- LLM routing (OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google Vertex AI)
- Semantic caching
- Rate limiting
- Guardrails
- Request/response transformations
- MCP (Model Context Protocol) support
- Identity & delegation (token exchange)
- Inference routing with vLLM
- LLM failover

### Not Rust
Despite Envoy supporting WASM filters (which *can* be written in Rust), the core Agentgateway product is **Go + Envoy/C++**, not a Rust-native implementation.

## Public Workshop Repos
- `solo-io/fe-enterprise-agentgateway-workshop` — Enterprise install labs
- `solo-io/agentgateway-llm-d` — llm-d inference scheduling demo
- `solo-io/enterprise-mcp-flow` — MCP auth with Entra ID demo

## Related solo.io Repos (Not AI Gateway)
- `solo-io/wasm` — WASM tools and SDKs for extending cloud-native infrastructure
- `solo-io/envoy-wasm-filters` — Envoy WASM filters (C++ repo)
