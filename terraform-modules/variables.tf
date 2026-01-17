# =============================================================================
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
