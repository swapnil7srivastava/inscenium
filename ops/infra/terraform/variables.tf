# Inscenium Infrastructure Variables
# ==================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "inscenium"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "Inscenium"
    ManagedBy   = "Terraform"
    Environment = "development"
  }
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# Database
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial database storage size in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum database storage size in GB"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "inscenium"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  default     = "changeme-inscenium-db-password"
}

variable "db_backup_retention_days" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

# Redis Cache
variable "enable_redis" {
  description = "Enable Redis caching cluster"
  type        = bool
  default     = false
}

variable "redis_node_type" {
  description = "Redis node instance type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 2
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "enable_gpu_nodes" {
  description = "Enable GPU node groups for ML workloads"
  type        = bool
  default     = false
}

variable "gpu_node_instance_types" {
  description = "Instance types for GPU nodes"
  type        = list(string)
  default     = ["g4dn.xlarge", "g4dn.2xlarge"]
}

variable "gpu_node_desired_size" {
  description = "Desired number of GPU nodes"
  type        = number
  default     = 0
}

variable "gpu_node_max_size" {
  description = "Maximum number of GPU nodes"
  type        = number
  default     = 3
}

variable "gpu_node_min_size" {
  description = "Minimum number of GPU nodes"
  type        = number
  default     = 0
}

# CDN Configuration
variable "cloudfront_price_class" {
  description = "CloudFront distribution price class"
  type        = string
  default     = "PriceClass_100"
  validation {
    condition = contains([
      "PriceClass_All",
      "PriceClass_200", 
      "PriceClass_100"
    ], var.cloudfront_price_class)
    error_message = "CloudFront price class must be PriceClass_All, PriceClass_200, or PriceClass_100."
  }
}

# Security
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the infrastructure"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # WARNING: Restrict this in production
}

# Storage
variable "s3_enable_versioning" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "s3_lifecycle_enabled" {
  description = "Enable S3 lifecycle policies"
  type        = bool
  default     = true
}

variable "s3_glacier_transition_days" {
  description = "Days after which to transition objects to Glacier"
  type        = number
  default     = 30
}

variable "s3_deep_archive_transition_days" {
  description = "Days after which to transition objects to Deep Archive"
  type        = number
  default     = 90
}

# Monitoring
variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch log groups"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
}

# Cost optimization
variable "enable_spot_instances" {
  description = "Use spot instances for cost optimization"
  type        = bool
  default     = false
}

# Domain configuration
variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "create_route53_zone" {
  description = "Create Route53 hosted zone"
  type        = bool
  default     = false
}

# Feature flags
variable "enable_waf" {
  description = "Enable AWS WAF for security"
  type        = bool
  default     = false
}

variable "enable_secrets_manager" {
  description = "Use AWS Secrets Manager for sensitive data"
  type        = bool
  default     = false
}

# Local development overrides
variable "local_development" {
  description = "Flag to indicate local development setup"
  type        = bool
  default     = true
}

variable "skip_expensive_resources" {
  description = "Skip expensive resources for local/dev environments"
  type        = bool
  default     = true
}