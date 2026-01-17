# Automating Security: DevSecOps with GitHub Actions and Trivy

*Implementing "Shift Left" security in your CI/CD pipeline*

---

## Introduction: The Shift Left Philosophy

Traditional security practices treat security as a final gate before production—a bottleneck that creates friction between development and operations. **DevSecOps** fundamentally changes this by shifting security left in the development lifecycle.

```
Traditional Approach:
  Code → Build → Test → [Deploy] → Security Audit → Production
                                   ↑
                        (Late discovery = expensive fixes)

Shift Left Approach:
  Code → [Lint + SAST] → Build → [Container Scan] → Deploy → Production
         ↑                        ↑
    (Early detection = cheap fixes)
```

### Why Shift Left?

| Discovery Stage | Cost to Fix | Time to Fix |
|-----------------|-------------|-------------|
| Development | 1x | Hours |
| CI Pipeline | 5x | Days |
| Pre-Production | 10x | Weeks |
| Production | 100x | Months |

By integrating security scanning directly into our CI pipeline, we catch vulnerabilities before they reach production—saving time, money, and potential security incidents.

---

## Pipeline Architecture

Our CI pipeline implements a multi-stage security-first approach:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GitHub Actions CI Pipeline                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │   LINT   │ -> │   TEST   │ -> │  BUILD   │ -> │  TRIVY   │          │
│  │          │    │          │    │          │    │  SCAN    │          │
│  │ • Ruff   │    │ • Pytest │    │ • Docker │    │          │          │
│  │ • MyPy   │    │ • Coverage│   │ • Buildx │    │ • CVE    │          │
│  └──────────┘    └──────────┘    │ • Cache  │    │ • SBOM   │          │
│                                   └──────────┘    └────┬─────┘          │
│                                                        │                 │
│                                        ┌───────────────┴───────────────┐│
│                                        │ CRITICAL/HIGH = FAIL PIPELINE ││
│                                        └───────────────┬───────────────┘│
│                                                        │                 │
│                                                        ▼                 │
│                                                 ┌──────────┐            │
│                                                 │   ECR    │            │
│                                                 │   PUSH   │            │
│                                                 │          │            │
│                                                 │ • Tag    │            │
│                                                 │ • Latest │            │
│                                                 └──────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Stage Breakdown

| Stage | Purpose | Failure Action |
|-------|---------|----------------|
| **Lint** | Code quality, formatting, type hints | Block merge |
| **Test** | Unit tests, coverage metrics | Block merge |
| **Build** | Multi-stage Docker build with caching | Block pipeline |
| **Security** | Trivy vulnerability scan | Block on HIGH/CRITICAL |
| **Push** | Deploy to ECR (main branch only) | Alert team |

---

## Why Trivy?

[Trivy](https://github.com/aquasecurity/trivy) by Aqua Security has become the industry standard for container security scanning. Here's why:

### Comprehensive Scanning

```
┌─────────────────────────────────────────┐
│            Trivy Scan Targets           │
├─────────────────────────────────────────┤
│  • Container Images (Docker, OCI)       │
│  • Filesystems                          │
│  • Git Repositories                     │
│  • Kubernetes Manifests                 │
│  • Infrastructure as Code (Terraform)   │
│  • SBOM (CycloneDX, SPDX)              │
└─────────────────────────────────────────┘
```

### Vulnerability Detection

Trivy scans for:

| Type | Examples |
|------|----------|
| **OS Packages** | Alpine, Debian, RHEL vulnerabilities |
| **Language Libraries** | Python (pip), Node (npm), Go modules |
| **IaC Misconfigurations** | Terraform, CloudFormation issues |
| **Secrets** | Exposed credentials, API keys |
| **License Compliance** | GPL, MIT, proprietary conflicts |

### Key Advantages

1. **Speed**: Scans complete in seconds, not minutes
2. **Accuracy**: Low false-positive rate with continuous CVE database updates
3. **Integration**: Native GitHub Actions support
4. **No Dependencies**: Single binary, no database server required
5. **SBOM Generation**: CycloneDX/SPDX format for compliance

---

## Key Code Snippets

### Docker Build with Layer Caching

Efficient builds are crucial for fast CI feedback loops:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build Docker Image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ./Dockerfile
    push: false
    load: true
    tags: |
      ${{ env.ECR_REPOSITORY }}:${{ env.IMAGE_TAG }}
      ${{ env.ECR_REPOSITORY }}:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
    build-args: |
      APP_VERSION=${{ env.IMAGE_TAG }}
```

**Key Optimizations:**

| Setting | Purpose |
|---------|---------|
| `docker/setup-buildx-action` | Enables BuildKit for parallel builds |
| `cache-from: type=gha` | Pulls cache from GitHub Actions cache |
| `cache-to: type=gha,mode=max` | Caches all layers, not just final |
| `load: true` | Loads image to local daemon for scanning |

### Trivy Security Scan Step

The security scan is configured to fail on HIGH and CRITICAL vulnerabilities:

```yaml
- name: Run Trivy Vulnerability Scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: '${{ env.ECR_REPOSITORY }}:${{ env.IMAGE_TAG }}'
    format: 'table'
    exit-code: '1'
    ignore-unfixed: true
    vuln-type: 'os,library'
    severity: 'CRITICAL,HIGH'
    timeout: '10m'

- name: Run Trivy SBOM Generation
  uses: aquasecurity/trivy-action@master
  if: always()
  with:
    image-ref: '${{ env.ECR_REPOSITORY }}:${{ env.IMAGE_TAG }}'
    format: 'cyclonedx'
    output: 'sbom.json'
```

**Configuration Explained:**

| Option | Value | Purpose |
|--------|-------|---------|
| `exit-code: '1'` | Fail pipeline on findings | Enforce security gate |
| `ignore-unfixed: true` | Skip CVEs without patches | Reduce noise |
| `severity: 'CRITICAL,HIGH'` | Only block on serious issues | Balance security/velocity |
| `vuln-type: 'os,library'` | Scan OS packages + Python libs | Comprehensive coverage |
| `format: 'cyclonedx'` | Industry-standard SBOM | Compliance & audit trail |

### Sample Trivy Output

When Trivy finds vulnerabilities, output looks like:

```
┌─────────────────────────────────────────────────────────────┐
│                 Vulnerability Report                         │
├──────────────┬────────┬──────────┬──────────────────────────┤
│   Library    │ CVE ID │ Severity │ Fixed Version            │
├──────────────┼────────┼──────────┼──────────────────────────┤
│ openssl      │ CVE-XX │ CRITICAL │ 1.1.1t-r0                │
│ libcrypto    │ CVE-YY │ HIGH     │ 1.1.1t-r0                │
└──────────────┴────────┴──────────┴──────────────────────────┘

Exit code: 1 (vulnerabilities found)
```

---

## Security Gates: Fail Fast Philosophy

Our pipeline implements progressive security gates:

```yaml
# Only push to ECR if ALL security checks pass
push-ecr:
  name: Push to Amazon ECR
  runs-on: ubuntu-latest
  needs: security-scan  # ← Depends on successful scan
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

### Gate Strategy

1. **Lint Stage**: Catches code smells and potential bugs early
2. **Test Stage**: Ensures functionality isn't broken
3. **Build Stage**: Validates Dockerfile syntax and dependencies
4. **Security Stage**: **HARD GATE** - No HIGH/CRITICAL CVEs allowed
5. **Push Stage**: Only main branch, only after all gates pass

---

## OIDC Authentication: No More Long-Lived Credentials

Modern CI/CD uses OIDC for AWS authentication—no secrets required:

```yaml
permissions:
  id-token: write   # Required for OIDC
  contents: read

- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ env.AWS_REGION }}
```

### Why OIDC?

| Approach | Security Risk | Maintenance |
|----------|---------------|-------------|
| Access Keys | High (can leak) | Rotate every 90 days |
| OIDC Tokens | Low (short-lived) | None required |

---

## What's Next

In **Part 3**, we'll cover:
- ArgoCD GitOps deployment configuration
- Kubernetes manifests with External Secrets Operator
- Nginx Ingress Controller setup

---

## Resources

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides)
- [Docker Build Caching Strategies](https://docs.docker.com/build/cache/)
- [AWS OIDC with GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

---

*This article is part of the Cloud-Native-Ops-Starter series, demonstrating production-grade DevOps practices for modern software delivery.*
