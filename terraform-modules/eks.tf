# =============================================================================
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
