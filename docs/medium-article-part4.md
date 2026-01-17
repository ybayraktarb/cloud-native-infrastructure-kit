# Production Ready: Exposing EKS via Nginx, Cloudflare and SSL

*Completing the cloud-native journey with secure, scalable ingress*

---

## Introduction: The Final Piece

We've built the application, provisioned infrastructure, automated CI/CD, and implemented GitOps. Now it's time to expose our service to the world—securely and reliably.

This final article covers the complete traffic flow from user to pod, implementing defense-in-depth with multiple layers of security and optimization.

---

## The Complete Traffic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRODUCTION TRAFFIC FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   👤 User                                                                    │
│     │                                                                        │
│     │ HTTPS Request                                                          │
│     ▼                                                                        │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                         CLOUDFLARE EDGE                               │  │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│   │  │   DNS   │ │   CDN   │ │   WAF   │ │  DDoS   │ │   SSL   │        │  │
│   │  │ Resolve │ │  Cache  │ │ Filter  │ │ Protect │ │ Termin. │        │  │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│   └────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ HTTPS (re-encrypted)                    │
│                                    ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                         AWS NETWORK LOAD BALANCER                     │  │
│   │  • Layer 4 (TCP) Load Balancing                                      │  │
│   │  • Health Checks to Nginx pods                                       │  │
│   │  • Cross-zone load balancing enabled                                 │  │
│   └────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ TCP (port 443)                          │
│                                    ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                      NGINX INGRESS CONTROLLER                         │  │
│   │  • TLS Termination (Origin Certificate)                              │  │
│   │  • Path-based routing                                                │  │
│   │  • Rate limiting (100 RPS)                                           │  │
│   │  • Security headers injection                                        │  │
│   └────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│                                    │ HTTP (internal)                         │
│                                    ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                      KUBERNETES SERVICE                               │  │
│   │  • ClusterIP (internal routing)                                      │  │
│   │  • Load balancing across pods                                        │  │
│   └────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                     │
│   │   Pod (API)   │ │   Pod (API)   │ │   Pod (API)   │                     │
│   │   Replica 1   │ │   Replica 2   │ │   Replica 3   │                     │
│   └───────────────┘ └───────────────┘ └───────────────┘                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Layer-by-Layer Security

| Layer | Component | Security Function |
|-------|-----------|-------------------|
| **1** | Cloudflare | DDoS protection, WAF, bot management |
| **2** | Cloudflare SSL | TLS 1.3 encryption, HSTS |
| **3** | AWS NLB | VPC isolation, security groups |
| **4** | Nginx Ingress | Rate limiting, security headers |
| **5** | K8s NetworkPolicy | Pod-to-pod isolation |
| **6** | Pod Security | Non-root, read-only filesystem |

---

## Nginx Ingress Configuration Deep Dive

### SSL/TLS Enforcement

```yaml
annotations:
  # Force all traffic to HTTPS
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
  nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  
  # Backend communicates over HTTP (TLS terminated at Ingress)
  nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
```

**Why terminate TLS at Nginx?**
- Simplified certificate management
- Consistent security headers
- Better observability (can inspect traffic)
- Performance optimization

### Security Headers

```yaml
nginx.ingress.kubernetes.io/configuration-snippet: |
  # Prevent clickjacking
  add_header X-Frame-Options "SAMEORIGIN" always;
  
  # Prevent MIME-type sniffing
  add_header X-Content-Type-Options "nosniff" always;
  
  # XSS protection (legacy browsers)
  add_header X-XSS-Protection "1; mode=block" always;
  
  # Control referrer information
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  
  # Content Security Policy
  add_header Content-Security-Policy "default-src 'self';" always;
```

| Header | Attack Prevented |
|--------|------------------|
| `X-Frame-Options` | Clickjacking |
| `X-Content-Type-Options` | MIME confusion attacks |
| `X-XSS-Protection` | Cross-site scripting |
| `Referrer-Policy` | Information leakage |
| `Content-Security-Policy` | Code injection |

### Rate Limiting

```yaml
annotations:
  # 100 requests per second per IP
  nginx.ingress.kubernetes.io/limit-rps: "100"
  
  # 50 concurrent connections per IP
  nginx.ingress.kubernetes.io/limit-connections: "50"
```

**Rate limiting strategy:**
- Protects against application-layer DDoS
- Prevents resource exhaustion
- Works alongside Cloudflare's edge rate limiting

---

## Cloudflare Integration

### DNS Configuration

| Record Type | Name | Target | Proxy |
|-------------|------|--------|-------|
| CNAME | api | `<NLB-DNS>` | ✅ Proxied |

**Why proxy through Cloudflare?**
- Hides origin IP address
- Enables CDN caching
- Activates WAF and DDoS protection
- Free SSL certificates

### SSL/TLS Mode: Full (Strict)

```
User ─── HTTPS ──→ Cloudflare ─── HTTPS ──→ Origin (NLB/Nginx)
         │                          │
    Cloudflare Cert            Origin Cert
    (Edge)                     (Cloudflare Origin CA)
```

This ensures end-to-end encryption with certificate validation.

---

## AWS NLB Configuration

The Nginx Ingress Controller's Service uses AWS annotations:

```yaml
annotations:
  # Network Load Balancer (Layer 4)
  service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
  
  # Internet-facing for Cloudflare access
  service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
  
  # High availability across zones
  service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
```

**NLB vs ALB:**

| Feature | NLB | ALB |
|---------|-----|-----|
| Layer | 4 (TCP) | 7 (HTTP) |
| Performance | Ultra-low latency | Higher latency |
| Static IP | ✅ | ❌ |
| WebSockets | ✅ Native | ✅ with config |
| Use Case | Ingress Controller | Direct HTTP apps |

We use NLB because Nginx handles Layer 7 logic.

---

## Complete Project Summary

Over five sprints, we built a production-grade cloud-native platform:

### Sprint 1: Application Core
- FastAPI with health probes
- Multi-stage Docker builds
- Non-root container security

### Sprint 2: Infrastructure as Code
- Terraform modular architecture
- EKS with Spot Instances (90% cost savings)
- VPC with multi-AZ NAT gateways

### Sprint 3: CI Pipeline (DevSecOps)
- GitHub Actions 5-stage pipeline
- Trivy vulnerability scanning
- Docker build caching with BuildKit

### Sprint 4: GitOps Deployment
- ArgoCD with auto-sync
- Kustomize environment overlays
- Self-healing drift correction

### Sprint 5: Production Networking
- Nginx Ingress with rate limiting
- Cloudflare edge security
- End-to-end SSL/TLS

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     CLOUD-NATIVE-OPS-STARTER ARCHITECTURE                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              DEVELOPER                                   │ │
│  │   git push → GitHub → Actions (Lint/Test/Scan/Push) → ECR              │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                         │
│                                     ▼ GitOps                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              ARGOCD                                      │ │
│  │   Watches Git → Detects Drift → Syncs to EKS → Reports Status          │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                         │
│                                     ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         AWS EKS CLUSTER                                  │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │ │
│  │  │  Nginx Ingress → Service → Pods (FastAPI) ← Prometheus Metrics   │   │ │
│  │  └──────────────────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                         │
│                                     │ AWS NLB                                 │
│                                     ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                            CLOUDFLARE                                    │ │
│  │   DNS → CDN → WAF → DDoS Protection → SSL                              │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                         │
│                                     ▼                                         │
│                                  👤 USERS                                     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Future Work: Observability Stack

The next evolution would include:

### Prometheus & Grafana
```yaml
# Already prepared with annotations
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
```

### Planned Dashboards
- **Application Metrics**: Request rate, latency, error rate
- **Infrastructure**: CPU, memory, network I/O
- **Business**: API usage patterns, user behavior

### Alert Manager
- PagerDuty integration for critical alerts
- Slack notifications for warnings
- Escalation policies

---

## Key Takeaways

1. **Security is Layered**: No single point of security—defense in depth
2. **GitOps is the Future**: Version-controlled, auditable, automated
3. **Cost Optimization Matters**: Spot Instances save 90%
4. **Shift Left**: Catch issues in CI, not production
5. **Automation Everywhere**: From code commit to production

---

## Resources

- [Complete Repository: Cloud-Native-Ops-Starter](https://github.com/cloud-native-ops/starter)
- [Nginx Ingress Controller Docs](https://kubernetes.github.io/ingress-nginx/)
- [Cloudflare SSL/TLS Documentation](https://developers.cloudflare.com/ssl/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

---

## Series Conclusion

This four-part series demonstrated how to build a complete, production-grade cloud-native platform:

| Part | Title | Focus |
|------|-------|-------|
| 1 | Building a Cost-Effective AWS EKS Foundation | Terraform, VPC, EKS |
| 2 | Automating Security: DevSecOps with GitHub Actions | CI, Trivy, Security |
| 3 | The GitOps Way: Continuous Delivery with ArgoCD | CD, GitOps, ArgoCD |
| 4 | Production Ready: Exposing EKS via Nginx & Cloudflare | Networking, SSL |

The **Cloud-Native-Ops-Starter** is now a complete reference architecture ready for production workloads or as a foundation for your own projects.

---

*Thank you for following this series. Star the repository on GitHub and share your implementations!*
