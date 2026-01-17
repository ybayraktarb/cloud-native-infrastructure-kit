#!/usr/bin/env python3
"""
Cloud-Native-Ops-Starter - Terraform Setup Script

This script creates the complete Terraform infrastructure code
using terraform-aws-modules for VPC and EKS.

Usage:
    python setup_terraform.py
"""

import os
from pathlib import Path

# =============================================================================
# Terraform File Contents
# =============================================================================

VERSIONS_TF = '''# =============================================================================
# Terraform & Provider Configuration
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local backend for development (no S3 dependency)
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "devops-portfolio"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
'''

VARIABLES_TF = '''# =============================================================================
# Input Variables
# =============================================================================

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-central-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "devops-portfolio-cluster"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}
'''

VPC_TF = '''# =============================================================================
# VPC using Official AWS Module
# =============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # NAT Gateway (single for cost savings)
  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

  # DNS settings
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Kubernetes tags for subnet discovery
  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = 1
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = 1
  }

  tags = {
    Environment = var.environment
    Cluster     = var.cluster_name
  }
}
'''

EKS_TF = '''# =============================================================================
# EKS Cluster using Official AWS Module
# =============================================================================

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.29"

  # Networking
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster access
  cluster_endpoint_public_access = true

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    spot-nodes = {
      name = "spot-nodes"

      # Spot Instances for cost optimization
      capacity_type  = "SPOT"
      instance_types = ["t3.medium"]

      # Scaling configuration
      min_size     = 1
      max_size     = 3
      desired_size = 2

      labels = {
        Environment = var.environment
        NodeType    = "spot"
      }
    }
  }

  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
  }

  tags = {
    Environment = var.environment
  }
}
'''

OUTPUTS_TF = '''# =============================================================================
# Outputs
# =============================================================================

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "region" {
  description = "AWS region"
  value       = var.region
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
'''

# =============================================================================
# File Mapping
# =============================================================================

TERRAFORM_FILES = {
    "versions.tf": VERSIONS_TF,
    "variables.tf": VARIABLES_TF,
    "vpc.tf": VPC_TF,
    "eks.tf": EKS_TF,
    "outputs.tf": OUTPUTS_TF,
}


def main():
    """Create Terraform directory and files."""
    # Get the script's directory
    script_dir = Path(__file__).parent.resolve()
    terraform_dir = script_dir / "terraform-modules"
    
    # Create terraform directory
    terraform_dir.mkdir(exist_ok=True)
    print(f"📁 Created directory: {terraform_dir}")
    
    # Create each file
    for filename, content in TERRAFORM_FILES.items():
        file_path = terraform_dir / filename
        file_path.write_text(content.strip() + "\n")
        print(f"✅ Created: {file_path.name}")
    
    print("\n" + "=" * 60)
    print("🎉 Terraform setup complete!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  cd {terraform_dir}")
    print(f"  terraform init")
    print(f"  terraform validate")
    print(f"  terraform plan")


if __name__ == "__main__":
    main()
