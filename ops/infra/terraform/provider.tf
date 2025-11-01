# Inscenium Terraform Provider Configuration
# =========================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Uncomment and configure for remote state storage
  # backend "s3" {
  #   bucket         = "inscenium-terraform-state"
  #   key            = "infrastructure/terraform.tfstate"
  #   region         = "us-west-2"
  #   encrypt        = true
  #   dynamodb_table = "inscenium-terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = var.common_tags
  }
}

provider "random" {
  # No configuration required
}

# Data source for current AWS caller identity
data "aws_caller_identity" "current" {}

# Data source for current AWS region
data "aws_region" "current" {}

# Data source for current AWS partition
data "aws_partition" "current" {}

# Local values for common resource naming and tagging
locals {
  # Common naming prefix
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Full resource name
  full_name = "${local.name_prefix}-${random_id.suffix.hex}"
  
  # Common tags to apply to all resources
  common_tags = merge(var.common_tags, {
    Environment   = var.environment
    Project       = var.project_name
    ManagedBy     = "Terraform"
    CreatedBy     = data.aws_caller_identity.current.user_id
    LastUpdated   = timestamp()
  })
  
  # AWS account and region info
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  partition  = data.aws_partition.current.partition
}

# Random suffix for globally unique resource names
resource "random_id" "suffix" {
  byte_length = 4
  
  keepers = {
    project     = var.project_name
    environment = var.environment
  }
}