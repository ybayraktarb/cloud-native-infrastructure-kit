# Cloud-Native-Ops-Starter

[![CI Pipeline](https://github.com/your-org/cloud-native-ops-starter/actions/workflows/ci.yaml/badge.svg)](https://github.com/your-org/cloud-native-ops-starter/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-EKS%20%7C%20ECR%20%7C%20VPC-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.0+-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.27+-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?logo=argo&logoColor=white)](https://argo-cd.readthedocs.io/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

> A **production-grade cloud-native reference architecture** demonstrating modern software delivery lifecycle (SDLC) best practices on AWS.

---

## 🌟 Key Highlights

- **Enterprise-Ready Infrastructure**: Battle-tested patterns for production workloads
- **Security-First Design**: Integrated vulnerability scanning, WAF, DDoS protection
- **GitOps Workflow**: Declarative deployments with ArgoCD
- **Multi-AZ High Availability**: EKS cluster spanning 3 Availability Zones
- **Fully Automated CI/CD**: From commit to production with zero manual intervention

---

## 🏗️ Architecture

![Cloud-Native Architecture](./architecture.png)

<details>
<summary><b>📋 Architecture Components</b></summary>

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Cloud Provider** | AWS | VPC, EKS, ECR, NLB |
| **Container Orchestration** | Amazon EKS | HA Kubernetes across 3 AZs |
| **Infrastructure as Code** | Terraform | Modular infrastructure provisioning |
| **CI/CD** | GitHub Actions | Automated build, test, and deploy |
| **GitOps** | ArgoCD | Continuous deployment & sync |
| **Ingress Controller** | Nginx | Traffic routing & load balancing |
| **Edge Security** | Cloudflare | DNS, CDN, WAF, DDoS Protection |
| **Application** | Python FastAPI | High-performance async API |
| **Containerization** | Docker | Multi-stage builds with security hardening |

</details>

---

## ✨ Features

### 🔐 Security
- 🛡️ **Trivy Vulnerability Scanning** — Container image security scanning in CI pipeline
- 👤 **Non-Root Containers** — Hardened Docker images running as non-privileged users
- 🌐 **Cloudflare WAF** — Web Application Firewall protecting against OWASP Top 10
- 🚫 **DDoS Protection** — Enterprise-grade DDoS mitigation at the edge
- 🔑 **OIDC Authentication** — Secure AWS credential management without static keys

### 🚀 Infrastructure
- 🌍 **Multi-AZ Deployment** — High availability across 3 AWS Availability Zones
- 📦 **Modular Terraform** — Reusable infrastructure modules (VPC, EKS, ECR, Bastion)
- 🔒 **Private Subnets** — Workloads isolated in private network segments
- 🖥️ **Bastion Host** — Secure SSH access with key-pair authentication

### ⚡ CI/CD
- ✅ **Automated Testing** — Unit tests with pytest and code coverage
- 🔍 **Code Quality** — Ruff linting and formatting checks
- 📊 **SBOM Generation** — Software Bill of Materials for supply chain security
- 🐳 **Multi-Stage Builds** — Optimized Docker images with build caching

### 🔄 GitOps
- 🎯 **Declarative Deployments** — Kubernetes manifests as source of truth
- 🔁 **Automatic Sync** — ArgoCD continuously reconciles desired state
- 📋 **Kustomize Overlays** — Environment-specific configurations (dev, staging, prod)

---

## 📁 Directory Structure

```
├── app/                    # FastAPI application
│   ├── __init__.py
│   └── main.py             # API endpoints
├── terraform/              # Infrastructure as Code
│   ├── main.tf             # Root module
│   ├── variables.tf        # Input variables
│   ├── outputs.tf          # Output values
│   └── modules/            # Reusable modules
│       ├── vpc/            # VPC configuration
│       ├── eks/            # EKS cluster
│       ├── ecr/            # Container registry
│       └── bastion/        # Bastion host
├── k8s/                    # Kubernetes manifests
│   ├── base/               # Base configurations
│   └── overlays/           # Environment overlays
├── argocd/                 # ArgoCD configurations
│   ├── application.yaml    # ArgoCD Application
│   └── project.yaml        # ArgoCD Project
├── .github/workflows/      # CI/CD pipeline
│   └── ci.yaml             # GitHub Actions workflow
├── docs/                   # Documentation
└── tests/                  # Test files
```

---

## 📋 Prerequisites

Before getting started, ensure you have the following tools installed:

| Tool | Version | Installation |
|------|---------|--------------|
| **AWS CLI** | v2.x | [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **Terraform** | ≥ 1.0 | [Install Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli) |
| **kubectl** | ≥ 1.27 | [Install Guide](https://kubernetes.io/docs/tasks/tools/) |
| **Helm** | ≥ 3.0 | [Install Guide](https://helm.sh/docs/intro/install/) |
| **Docker** | ≥ 20.10 | [Install Guide](https://docs.docker.com/get-docker/) |

<details>
<summary><b>🔧 Quick Install (macOS)</b></summary>

```bash
# Using Homebrew
brew install awscli terraform kubectl helm docker
```

</details>

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-org/cloud-native-ops-starter.git
cd cloud-native-ops-starter
```

### 2️⃣ Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and preferred region
```

### 3️⃣ Initialize Terraform

```bash
cd terraform

# Copy and customize variables
cp terraform.tfvars.example terraform.tfvars

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply infrastructure
terraform apply
```

### 4️⃣ Configure kubectl

```bash
# Update kubeconfig for EKS cluster
aws eks update-kubeconfig --name cloud-native-ops-dev --region us-east-1

# Verify connection
kubectl get nodes
```

### 5️⃣ Deploy Nginx Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  -f k8s/nginx-ingress-values.yaml \
  --namespace ingress-nginx \
  --create-namespace
```

### 6️⃣ Deploy ArgoCD

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Apply ArgoCD configurations
kubectl apply -f argocd/project.yaml
kubectl apply -f argocd/application.yaml
```

### 7️⃣ Access the Application

```bash
# Get the Load Balancer URL
kubectl get svc -n ingress-nginx

# Access the API
curl https://your-domain.com/health
```

---

## 🏗️ Terraform Modules

<details>
<summary><b>🌐 VPC Module</b></summary>

Creates a production-ready VPC with:
- **3 Public Subnets** — For load balancers and NAT gateways
- **3 Private Subnets** — For EKS worker nodes and workloads
- **NAT Gateways** — HA internet access for private subnets
- **Route Tables** — Proper routing for public/private traffic

```hcl
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = "10.0.0.0/16"
}
```

</details>

<details>
<summary><b>☸️ EKS Module</b></summary>

Provisions a managed Kubernetes cluster with:
- **Managed Node Groups** — Auto-scaling worker nodes
- **OIDC Provider** — For IAM roles for service accounts
- **CoreDNS & VPC-CNI** — Essential EKS add-ons
- **Cluster Autoscaler Ready** — Pre-configured for auto-scaling

```hcl
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = var.cluster_name
  cluster_version = "1.27"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
}
```

</details>

<details>
<summary><b>📦 ECR Module</b></summary>

Creates a private container registry with:
- **Image Scanning** — Automatic vulnerability scanning
- **Lifecycle Policies** — Automatic cleanup of old images
- **Cross-Account Access** — Optional repository policies

```hcl
module "ecr" {
  source = "./modules/ecr"
  
  repository_name = "cloud-native-ops-dev"
  environment     = var.environment
}
```

</details>

<details>
<summary><b>🖥️ Bastion Module</b></summary>

Deploys a secure bastion host with:
- **SSH Key Authentication** — No password access
- **Security Groups** — Restricted ingress/egress rules
- **Session Manager** — Optional AWS SSM access

```hcl
module "bastion" {
  source = "./modules/bastion"
  
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_ids[0]
  key_name         = var.ssh_key_name
}
```

</details>

---

## 🔄 CI/CD Pipeline

The GitHub Actions pipeline implements a **DevSecOps** workflow:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Lint     │───▶│    Test     │───▶│    Build    │───▶│   Security  │───▶│  Push ECR   │
│  (Ruff)     │    │  (pytest)   │    │  (Docker)   │    │   (Trivy)   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

<details>
<summary><b>📊 Pipeline Stages</b></summary>

| Stage | Description | Tools |
|-------|-------------|-------|
| **Lint** | Code quality and formatting checks | Ruff, MyPy |
| **Test** | Unit tests with code coverage | pytest, pytest-cov |
| **Build** | Multi-stage Docker image build | Docker Buildx |
| **Security** | Vulnerability scanning, SBOM generation | Trivy |
| **Push** | Tag and push to Amazon ECR | AWS ECR |

</details>

### Workflow Triggers

- **Push to `main` or `develop`** — Full pipeline execution
- **Pull Requests to `main`** — Lint, test, build, and scan (no push)

---

## ☸️ Kubernetes Deployment

The application uses **Kustomize** for managing environment-specific configurations:

### Base Configuration

```bash
k8s/base/
├── deployment.yaml      # Application deployment
├── service.yaml         # ClusterIP service
├── ingress.yaml         # Nginx ingress rules
├── configmap.yaml       # Application configuration
├── hpa.yaml             # Horizontal Pod Autoscaler
└── kustomization.yaml   # Base kustomization
```

### Environment Overlays

```bash
k8s/overlays/
├── dev/                 # Development environment
│   └── kustomization.yaml
└── staging/             # Staging environment
    └── kustomization.yaml
```

### Deploy with Kustomize

```bash
# Deploy to development
kubectl apply -k k8s/overlays/dev/

# Deploy to staging
kubectl apply -k k8s/overlays/staging/
```

---

## 🎯 ArgoCD GitOps

ArgoCD provides **declarative, GitOps continuous delivery** for Kubernetes:

### Application Configuration

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cloud-native-ops-starter
spec:
  project: cloud-native-ops
  source:
    repoURL: https://github.com/your-org/cloud-native-ops-starter
    path: k8s/overlays/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Access ArgoCD UI

```bash
# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access at https://localhost:8080
```

---

## 🔐 Security Features

| Feature | Description |
|---------|-------------|
| 🔍 **Trivy Scanning** | Container vulnerability scanning in CI pipeline, blocking CRITICAL/HIGH severity |
| 👤 **Non-Root Containers** | Docker images run as non-privileged user (UID 1001) |
| 🌐 **Cloudflare WAF** | Web Application Firewall with OWASP Core Rule Set |
| 🛡️ **DDoS Protection** | Layer 3/4/7 DDoS mitigation at Cloudflare edge |
| 🔑 **OIDC Authentication** | GitHub Actions uses OIDC for secure AWS access |
| 📜 **SBOM Generation** | Software Bill of Materials in CycloneDX format |
| 🔒 **Private Subnets** | Application workloads isolated from public internet |
| 🚪 **Network Policies** | Kubernetes network segmentation (optional) |

---

## 📡 API Endpoints

The FastAPI application exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Application metadata (name, version, description) |
| `/health` | GET | Health check with timestamp and version |
| `/live` | GET | Kubernetes liveness probe |
| `/ready` | GET | Kubernetes readiness probe |
| `/api/v1/system-status` | GET | Detailed system status and metrics |
| `/docs` | GET | Swagger UI documentation |
| `/redoc` | GET | ReDoc API documentation |

<details>
<summary><b>📝 Example Responses</b></summary>

**GET `/health`**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "api": "operational"
  }
}
```

**GET `/api/v1/system-status`**
```json
{
  "service": "Cloud-Native-Ops-Starter",
  "version": "1.0.0",
  "environment": "development",
  "region": "us-east-1",
  "status": {
    "api_gateway": "operational",
    "database": "operational",
    "cache": "operational"
  }
}
```

</details>

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines

- Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- Ensure all tests pass before submitting PR
- Update documentation for any new features
- Add tests for new functionality

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Cloud-Native-Ops Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">
  <b>Built with ❤️ by the Cloud-Native-Ops Team</b>
</p>

<p align="center">
  <a href="#cloud-native-ops-starter">⬆️ Back to Top</a>
</p>
