# Inscenium Infrastructure - Main Configuration
# =============================================
# WARNING: This is scaffolding code for development reference only.
# Do not use in production without proper review and customization.

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
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources for existing resources
data "aws_availability_zones" "available" {
  state = "available"
}

# S3 bucket for video assets and processing artifacts
resource "aws_s3_bucket" "inscenium_assets" {
  bucket = "${var.project_name}-assets-${var.environment}"

  tags = merge(var.common_tags, {
    Name        = "Inscenium Assets"
    Component   = "Storage"
  })
}

resource "aws_s3_bucket_versioning" "inscenium_assets" {
  bucket = aws_s3_bucket.inscenium_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "inscenium_assets" {
  bucket = aws_s3_bucket.inscenium_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# RDS PostgreSQL instance for SGI database
resource "aws_db_subnet_group" "inscenium" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(var.common_tags, {
    Name = "Inscenium DB Subnet Group"
  })
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "Inscenium RDS Security Group"
  })
}

resource "aws_db_instance" "inscenium" {
  identifier = "${var.project_name}-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true
  
  db_name  = "inscenium"
  username = var.db_username
  password = var.db_password
  
  db_subnet_group_name   = aws_db_subnet_group.inscenium.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  backup_retention_period = var.db_backup_retention_days
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"
  
  tags = merge(var.common_tags, {
    Name      = "Inscenium Database"
    Component = "Database"
  })
}

# VPC and networking
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.common_tags, {
    Name = "Inscenium VPC"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.common_tags, {
    Name = "Inscenium IGW"
  })
}

resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.common_tags, {
    Name = "Inscenium Public Subnet ${count.index + 1}"
    Type = "Public"
  })
}

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.common_tags, {
    Name = "Inscenium Private Subnet ${count.index + 1}"
    Type = "Private"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.common_tags, {
    Name = "Inscenium Public Route Table"
  })
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# EKS cluster for GPU workloads (placeholder)
resource "aws_security_group" "eks_cluster" {
  name_prefix = "${var.project_name}-eks-cluster-"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "Inscenium EKS Cluster Security Group"
  })
}

resource "aws_security_group" "app" {
  name_prefix = "${var.project_name}-app-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "Inscenium App Security Group"
  })
}

# CloudFront distribution placeholder
resource "aws_cloudfront_distribution" "inscenium" {
  comment             = "Inscenium CDN Distribution"
  default_root_object = "index.html"
  enabled             = true
  is_ipv6_enabled     = true

  origin {
    domain_name = aws_s3_bucket.inscenium_assets.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.inscenium_assets.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.inscenium_assets.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(var.common_tags, {
    Name      = "Inscenium CDN"
    Component = "CDN"
  })
}

resource "aws_cloudfront_origin_access_identity" "main" {
  comment = "Inscenium CloudFront OAI"
}

# ElastiCache Redis for caching (optional)
resource "aws_elasticache_subnet_group" "inscenium" {
  name       = "${var.project_name}-cache-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(var.common_tags, {
    Name = "Inscenium Cache Subnet Group"
  })
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = merge(var.common_tags, {
    Name = "Inscenium Redis Security Group"
  })
}

resource "aws_elasticache_replication_group" "inscenium" {
  count = var.enable_redis ? 1 : 0

  replication_group_id       = "${var.project_name}-${var.environment}"
  description                = "Inscenium Redis cluster"
  
  node_type                  = var.redis_node_type
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = var.redis_num_cache_nodes
  
  subnet_group_name          = aws_elasticache_subnet_group.inscenium.name
  security_group_ids         = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = merge(var.common_tags, {
    Name      = "Inscenium Redis"
    Component = "Cache"
  })
}