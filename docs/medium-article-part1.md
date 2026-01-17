# Building a Cost-Effective AWS EKS Foundation with Terraform

*A practical guide to infrastructure as code for production Kubernetes*

---

## Introduction

In modern cloud-native architectures, Kubernetes has become the de facto standard for container orchestration. However, running Kubernetes in production—especially on AWS—requires careful consideration of infrastructure design, security, and cost optimization.

This article is the first in a series documenting the **Cloud-Native-Ops-Starter** project, a production-grade reference architecture that demonstrates a complete software delivery lifecycle using modern DevOps practices.

### Why Terraform?

Infrastructure as Code (IaC) is non-negotiable for production systems. Terraform offers:

- **Declarative Configuration**: Define desired state, not procedural steps
- **Provider Ecosystem**: Native AWS support with 5,000+ resources
- **State Management**: Track infrastructure changes over time
- **Modularity**: Reusable components across environments
- **Plan/Apply Workflow**: Preview changes before execution

### Why EKS?

Amazon EKS provides a managed Kubernetes control plane, eliminating the operational burden of running `etcd`, the API server, and scheduler. Key benefits:

- **Managed Control Plane**: AWS handles availability, scaling, and patching
- **AWS Integration**: Native IAM, VPC, ALB, and CloudWatch integration
- **Security**: OIDC-based IAM Roles for Service Accounts (IRSA)
- **Flexibility**: Managed node groups, Fargate, or self-managed nodes

---

## Architecture Overview

Our infrastructure follows AWS Well-Architected Framework principles:

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     VPC (10.0.0.0/16)                     │  │
│  │                                                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐ │  │
│  │  │  Public Subnet  │  │  Public Subnet  │  │  Public   │ │  │
│  │  │   10.0.0.0/20   │  │   10.0.16.0/20  │  │  Subnet   │ │  │
│  │  │    us-east-1a   │  │    us-east-1b   │  │ us-east-1c│ │  │
│  │  │    [NAT GW]     │  │    [NAT GW]     │  │ [NAT GW]  │ │  │
│  │  └────────┬────────┘  └────────┬────────┘  └─────┬─────┘ │  │
│  │           │                    │                  │       │  │
│  │           ▼                    ▼                  ▼       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐ │  │
│  │  │ Private Subnet  │  │ Private Subnet  │  │  Private  │ │  │
│  │  │  10.0.48.0/20   │  │  10.0.64.0/20   │  │  Subnet   │ │  │
│  │  │   us-east-1a    │  │   us-east-1b    │  │ us-east-1c│ │  │
│  │  │  [EKS Nodes]    │  │  [EKS Nodes]    │  │[EKS Nodes]│ │  │
│  │  └─────────────────┘  └─────────────────┘  └───────────┘ │  │
│  │                                                           │  │
│  │                 ┌─────────────────────┐                   │  │
│  │                 │   EKS Control Plane │                   │  │
│  │                 │   (AWS Managed)     │                   │  │
│  │                 └─────────────────────┘                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────┐                                                │
│  │     ECR     │  Container Registry                           │
│  └─────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Subnets | 3 AZs, Public + Private | High availability, security isolation |
| NAT Gateway | Per-AZ | Eliminate cross-AZ data transfer, fault tolerance |
| EKS Nodes | Private subnets | Security best practice |
| Control Plane | Public + Private endpoints | Convenient access with secure node communication |

---

## Key Code Snippets

### VPC Module: Multi-AZ Network Foundation

The VPC module creates a production-ready network with proper isolation:

```hcl
# Public Subnets with EKS-compatible tags
resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name                                           = "${var.project_name}-${var.environment}-public-${var.availability_zones[count.index]}"
    "kubernetes.io/role/elb"                       = "1"
    "kubernetes.io/cluster/${var.project_name}-${var.environment}" = "shared"
  })
}

# Private Subnets for EKS workloads
resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name                                           = "${var.project_name}-${var.environment}-private-${var.availability_zones[count.index]}"
    "kubernetes.io/role/internal-elb"              = "1"
    "kubernetes.io/cluster/${var.project_name}-${var.environment}" = "shared"
  })
}
```

**Key Points:**
- `cidrsubnet()` dynamically calculates CIDR blocks
- Kubernetes-specific tags enable automatic subnet discovery by AWS Load Balancer Controller
- Separate tagging for external (`elb`) vs internal (`internal-elb`) load balancers

### EKS Spot Instance Configuration

Spot Instances provide up to 90% cost savings compared to On-Demand:

```hcl
# EKS Managed Node Group with Spot Instances
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_name}-${var.environment}-node-group"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  # Spot Instance Configuration
  capacity_type  = "SPOT"  # Key setting for cost optimization
  instance_types = ["t3.medium"]

  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 4
  }

  labels = {
    Environment = var.environment
    NodeType    = "spot"
  }

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}
```

**Configuration Highlights:**
- `capacity_type = "SPOT"` enables Spot pricing
- `t3.medium` provides good balance of cost and capability
- `lifecycle` block prevents Terraform from fighting with autoscaler
- Labels enable node selection in Kubernetes manifests

---

## Challenge & Solution: Cost Optimization with Spot Instances

### The Challenge

Running Kubernetes on AWS can be expensive. A typical 3-node `t3.medium` cluster costs approximately:

| Type | Hourly | Monthly (730h) |
|------|--------|----------------|
| On-Demand | $0.1248 | ~$273 |
| Spot | ~$0.0125 | ~$27 |
| **Savings** | - | **~90%** |

### The Solution

**1. Use Spot Instances for Non-Critical Workloads**

EKS managed node groups handle Spot interruption gracefully:
- 2-minute warning before termination
- Automatic pod rescheduling
- No single point of failure with multi-AZ deployment

**2. Instance Type Diversification**

For production, consider multiple instance types:

```hcl
instance_types = ["t3.medium", "t3a.medium", "t2.medium"]
```

This increases Spot capacity availability and reduces interruption probability.

**3. Mixed Capacity Strategy**

For critical workloads, combine On-Demand and Spot:

```hcl
# Separate node groups for different workload types
# On-Demand for stateful/critical services
# Spot for stateless/batch workloads
```

---

## Challenge & Solution: State Management

### The Challenge

Terraform state contains sensitive information and must be:
- Centrally accessible for team collaboration
- Protected from corruption
- Versioned for rollback capability
- Locked during operations

### The Solution

**Local State (Development)**

For individual development:

```hcl
backend "local" {
  path = "terraform.tfstate"
}
```

**S3 Remote State (Production)**

For team environments:

```hcl
backend "s3" {
  bucket         = "cloud-native-ops-terraform-state"
  key            = "infrastructure/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

| Feature | Local | S3 + DynamoDB |
|---------|-------|---------------|
| Team Access | ❌ | ✅ |
| State Locking | ❌ | ✅ |
| Encryption | ❌ | ✅ |
| Versioning | ❌ | ✅ |
| Cost | Free | ~$1/month |

---

## What's Next

In **Part 2**, we'll cover:
- GitHub Actions CI pipeline with Trivy security scanning
- Building and pushing container images to ECR
- Implementing trunk-based development workflow

---

## Resources

- [GitHub Repository: Cloud-Native-Ops-Starter](https://github.com/cloud-native-ops/starter)
- [AWS EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

*This article is part of the Cloud-Native-Ops-Starter series, demonstrating production-grade DevOps practices for modern software delivery.*
