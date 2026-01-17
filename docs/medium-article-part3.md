# The GitOps Way: Continuous Delivery with ArgoCD on EKS

*Why pull-based deployments are transforming cloud-native operations*

---

## Introduction: Push vs. Pull Deployments

Traditional CI/CD pipelines use a **push-based** model: CI servers (Jenkins, GitHub Actions) directly deploy to production clusters. This approach has fundamental security and operational challenges.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PUSH-BASED DEPLOYMENT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Developer → Git → CI Server → [kubectl apply] → Kubernetes Cluster   │
│                         │                                                │
│                         └── CI needs cluster credentials                 │
│                             (security risk)                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      PULL-BASED DEPLOYMENT (GitOps)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Developer → Git ← [monitors] ← ArgoCD (in-cluster) → Reconciles      │
│                                                                          │
│                         └── No external access to cluster                │
│                             (secure by design)                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why GitOps is Superior

| Aspect | Push-Based (Jenkins) | Pull-Based (ArgoCD) |
|--------|---------------------|---------------------|
| **Security** | CI needs cluster credentials | No external access required |
| **Audit Trail** | Build logs (ephemeral) | Git history (permanent) |
| **Drift Detection** | Manual checks | Automatic & continuous |
| **Rollback** | Re-run old pipeline | `git revert` |
| **Single Source of Truth** | CI server state | Git repository |
| **Multi-Cluster** | Complex credential management | Native support |

---

## GitOps Core Principles

GitOps, coined by Weaveworks, is built on four pillars:

### 1. Declarative Configuration

Everything is described declaratively in Git—not just application code, but the entire desired state of the system:

```yaml
# The complete desired state lives in Git
spec:
  replicas: 3
  containers:
    - image: myapp:v2.0.0
```

### 2. Version Controlled

Git is the single source of truth. Every change is:
- **Versioned**: Complete history of all changes
- **Auditable**: Who changed what, when, and why
- **Reversible**: Rollback to any previous state

### 3. Automated Application

Changes are **automatically** applied when Git state changes. No manual `kubectl` commands.

### 4. Continuous Reconciliation

The system continuously compares actual state with desired state and corrects any drift:

```
                    ┌─────────────────┐
                    │   Git (Desired)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  ArgoCD Watches  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │ Synced  │    │  Drift  │    │ Missing │
        │   ✓     │    │    !    │    │    ✗    │
        └─────────┘    └────┬────┘    └────┬────┘
                            │              │
                            ▼              ▼
                       ┌────────────────────┐
                       │   Self-Heal        │
                       │   (Reconcile)      │
                       └────────────────────┘
```

---

## ArgoCD Application Manifest Deep Dive

The ArgoCD Application CRD is the heart of GitOps deployment:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cloud-native-ops-api
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default

  # Where to get the manifests
  source:
    repoURL: https://github.com/cloud-native-ops/starter.git
    targetRevision: HEAD    # Track latest commit
    path: k8s/overlays/production
    kustomize:
      images:
        - myregistry/myapp:v2.0.0

  # Where to deploy
  destination:
    server: https://kubernetes.default.svc
    namespace: cloud-native-ops

  # Automation settings
  syncPolicy:
    automated:
      prune: true      # Delete resources removed from Git
      selfHeal: true   # Fix drift automatically
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

### Key Configuration Explained

| Field | Value | Purpose |
|-------|-------|---------|
| `targetRevision: HEAD` | Track latest commit | Continuous deployment |
| `prune: true` | Auto-delete removed resources | Clean state |
| `selfHeal: true` | Fix manual changes | Prevent drift |
| `ServerSideApply` | K8s native merge | Better conflict handling |

---

## The Sync Process: What Happens When Code Changes

When a developer pushes to the repository, here's the complete flow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GITOPS SYNC PROCESS                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. COMMIT                                                               │
│     Developer pushes code → GitHub                                      │
│                    │                                                     │
│                    ▼                                                     │
│  2. CI PIPELINE                                                          │
│     GitHub Actions: Lint → Test → Build → Scan → Push to ECR           │
│                    │                                                     │
│                    ▼                                                     │
│  3. MANIFEST UPDATE                                                      │
│     CI updates image tag in k8s/overlays/production/kustomization.yaml │
│                    │                                                     │
│                    ▼                                                     │
│  4. ARGOCD DETECTION (polling every 3 min or webhook)                   │
│     ArgoCD detects Git SHA changed                                      │
│                    │                                                     │
│                    ▼                                                     │
│  5. DIFF CALCULATION                                                     │
│     ArgoCD compares: Git State vs Cluster State                         │
│     Status: OutOfSync                                                    │
│                    │                                                     │
│                    ▼                                                     │
│  6. SYNC OPERATION                                                       │
│     ArgoCD applies manifests to EKS (kubectl apply internally)          │
│                    │                                                     │
│                    ▼                                                     │
│  7. HEALTH CHECK                                                         │
│     ArgoCD monitors: Deployment rollout, Pod health, Service endpoints  │
│                    │                                                     │
│                    ▼                                                     │
│  8. SYNC COMPLETE                                                        │
│     Status: Synced + Healthy                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Sync Timing

| Trigger | Latency | Use Case |
|---------|---------|----------|
| **Polling** | 3 min (default) | Standard deployments |
| **Webhook** | Seconds | Immediate deployment |
| **Manual** | Instant | Emergency changes |

---

## Production Kubernetes Manifests

### Deployment with Distinct Health Probes

Our deployment uses three types of probes, each serving a different purpose:

```yaml
# Liveness Probe - Is the container alive?
# Failure: Kubernetes RESTARTS the container
livenessProbe:
  httpGet:
    path: /live
    port: http
  initialDelaySeconds: 10
  periodSeconds: 15
  failureThreshold: 3

# Readiness Probe - Can it receive traffic?
# Failure: Pod removed from Service endpoints (no traffic)
readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3

# Startup Probe - Has it finished starting?
# Until success: Liveness/Readiness probes are disabled
startupProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5
  failureThreshold: 30
```

### Probe Endpoints Design

| Endpoint | Check | When to Fail |
|----------|-------|--------------|
| `/live` | Process running | Deadlock, infinite loop |
| `/ready` | Can handle requests | Warming cache, loading ML model |
| `/health` | Full system health | Database down, dependencies unavailable |

---

## Kustomize for Environment Management

We use Kustomize to manage environment-specific configurations:

```
k8s/
├── base/                    # Common resources
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── namespace.yaml
│   └── kustomization.yaml
└── overlays/
    ├── development/         # Dev-specific patches
    │   └── kustomization.yaml
    └── production/          # Prod-specific patches
        └── kustomization.yaml
```

### Production Overlay

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

replicas:
  - name: cloud-native-ops-api
    count: 3    # Scale up for production

patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: cloud-native-ops-api
      spec:
        template:
          spec:
            containers:
              - name: api
                resources:
                  limits:
                    cpu: 1000m
                    memory: 512Mi
```

---

## Rollback: The Power of Git

When issues occur in production, rollback is trivial:

```bash
# Option 1: Git Revert (preferred - maintains history)
git revert HEAD
git push

# Option 2: ArgoCD UI
# Click "History" → Select previous revision → "Rollback"

# Option 3: ArgoCD CLI
argocd app rollback cloud-native-ops-api
```

ArgoCD detects the Git change and syncs the cluster back to the previous state. No pipeline re-runs, no complex rollback scripts.

---

## What's Next

In **Part 4**, we'll cover:
- Nginx Ingress Controller configuration
- External Secrets Operator with AWS Secrets Manager
- Prometheus & Grafana observability stack

---

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles - OpenGitOps](https://opengitops.dev/)
- [Kustomize Documentation](https://kustomize.io/)
- [Kubernetes Probes Best Practices](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

*This article is part of the Cloud-Native-Ops-Starter series, demonstrating production-grade DevOps practices for modern software delivery.*
