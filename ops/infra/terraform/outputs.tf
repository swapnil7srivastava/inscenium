# Inscenium Infrastructure Outputs
# ================================

# Database outputs
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.inscenium.endpoint
  sensitive   = false
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.inscenium.port
}

output "database_name" {
  description = "RDS database name"
  value       = aws_db_instance.inscenium.db_name
}

output "database_username" {
  description = "RDS master username"
  value       = aws_db_instance.inscenium.username
  sensitive   = true
}

output "database_connection_string" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${aws_db_instance.inscenium.username}:${var.db_password}@${aws_db_instance.inscenium.endpoint}:${aws_db_instance.inscenium.port}/${aws_db_instance.inscenium.db_name}"
  sensitive   = true
}

# Storage outputs
output "s3_bucket_name" {
  description = "S3 bucket name for assets"
  value       = aws_s3_bucket.inscenium_assets.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.inscenium_assets.arn
}

output "s3_bucket_domain_name" {
  description = "S3 bucket regional domain name"
  value       = aws_s3_bucket.inscenium_assets.bucket_regional_domain_name
}

# CDN outputs
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.inscenium.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.inscenium.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  value       = aws_cloudfront_distribution.inscenium.hosted_zone_id
}

# Networking outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# Security groups
output "app_security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.app.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

output "eks_cluster_security_group_id" {
  description = "ID of the EKS cluster security group"
  value       = aws_security_group.eks_cluster.id
}

# Cache outputs (conditional)
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = var.enable_redis ? aws_elasticache_replication_group.inscenium[0].primary_endpoint_address : null
}

output "redis_port" {
  description = "Redis cluster port"
  value       = var.enable_redis ? aws_elasticache_replication_group.inscenium[0].port : null
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = var.enable_redis ? "redis://${aws_elasticache_replication_group.inscenium[0].primary_endpoint_address}:${aws_elasticache_replication_group.inscenium[0].port}" : null
  sensitive   = false
}

# Environment configuration
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# Configuration for applications
output "application_config" {
  description = "Configuration values for applications"
  value = {
    # Database
    postgres_dsn = "postgresql://${aws_db_instance.inscenium.username}:${var.db_password}@${aws_db_instance.inscenium.endpoint}:${aws_db_instance.inscenium.port}/${aws_db_instance.inscenium.db_name}"
    
    # Storage
    s3_bucket     = aws_s3_bucket.inscenium_assets.id
    s3_region     = var.aws_region
    cdn_base_url  = "https://${aws_cloudfront_distribution.inscenium.domain_name}"
    
    # Cache
    redis_url = var.enable_redis ? "redis://${aws_elasticache_replication_group.inscenium[0].primary_endpoint_address}:${aws_elasticache_replication_group.inscenium[0].port}" : ""
    
    # Environment
    environment = var.environment
    aws_region  = var.aws_region
  }
  sensitive = true
}

# Terraform state information
output "terraform_workspace" {
  description = "Terraform workspace name"
  value       = terraform.workspace
}

# Resource ARNs for IAM policies
output "resource_arns" {
  description = "ARNs of created resources for IAM policy reference"
  value = {
    s3_bucket                = aws_s3_bucket.inscenium_assets.arn
    s3_bucket_objects        = "${aws_s3_bucket.inscenium_assets.arn}/*"
    rds_instance            = aws_db_instance.inscenium.arn
    cloudfront_distribution = aws_cloudfront_distribution.inscenium.arn
    vpc                     = aws_vpc.main.arn
  }
}

# Local development helpers
output "local_development_notes" {
  description = "Notes for local development setup"
  value = var.local_development ? {
    database_tunnel = "Use 'kubectl port-forward' or AWS Systems Manager Session Manager to connect to RDS"
    s3_access      = "Configure AWS CLI with appropriate credentials to access S3 bucket"
    cdn_testing    = "CloudFront distribution may take 15-20 minutes to deploy"
    cost_warning   = "Remember to destroy resources when not needed: 'terraform destroy'"
  } : null
}

# Security considerations
output "security_notes" {
  description = "Important security considerations"
  value = {
    database_security   = "Database is in private subnets, accessible only from application security group"
    s3_security        = "S3 bucket uses server-side encryption and CloudFront OAI"
    network_security   = "VPC uses private subnets for database and application tiers"
    password_security  = "Change default database password in production!"
    access_security    = "Review and restrict CIDR blocks for production deployments"
  }
}