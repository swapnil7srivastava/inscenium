# Inscenium Infrastructure

This directory contains Terraform configuration for Inscenium's cloud infrastructure.

⚠️ **WARNING: This is scaffolding code for development reference only. Do not use in production without proper review and customization.**

## Architecture

The infrastructure includes:

- **VPC**: Isolated network with public and private subnets
- **RDS PostgreSQL**: Scene Graph Intelligence database
- **S3**: Asset storage and video processing artifacts
- **CloudFront**: CDN for global content delivery
- **ElastiCache Redis**: Optional caching layer
- **Security Groups**: Network-level security
- **EKS**: Kubernetes cluster for GPU workloads (placeholder)

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0 installed
- kubectl (for EKS features)

### Local Development

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="environment=dev" -var="local_development=true"

# Apply infrastructure
terraform apply -var="environment=dev" -var="local_development=true"

# Get outputs
terraform output
```

### Production Deployment

1. Configure remote state backend:
   ```hcl
   # Uncomment in provider.tf
   backend "s3" {
     bucket         = "your-terraform-state-bucket"
     key            = "infrastructure/terraform.tfstate"
     region         = "us-west-2"
     encrypt        = true
     dynamodb_table = "terraform-locks"
   }
   ```

2. Set production variables:
   ```bash
   terraform apply -var="environment=prod" \
     -var="local_development=false" \
     -var="db_password=secure-password" \
     -var="allowed_cidr_blocks=[\"your-office-ip/32\"]"
   ```

## Configuration

### Environment Variables

```bash
# AWS Configuration
export AWS_REGION=us-west-2
export AWS_PROFILE=inscenium

# Terraform Variables
export TF_VAR_environment=dev
export TF_VAR_db_password=secure-password
```

### Terraform Variables

Key variables to customize:

```hcl
# terraform.tfvars
project_name = "inscenium"
environment  = "dev"
aws_region   = "us-west-2"

# Database
db_instance_class = "db.t3.micro"  # Scale up for production
db_password       = "change-me-please"

# Networking  
vpc_cidr               = "10.0.0.0/16"
allowed_cidr_blocks    = ["0.0.0.0/0"]  # Restrict in production!

# Features
enable_redis           = true
enable_gpu_nodes       = false  # Enable for ML workloads
skip_expensive_resources = true # Disable for production
```

## Outputs

After deployment, key outputs include:

```bash
# Database connection
terraform output database_connection_string

# S3 bucket for assets
terraform output s3_bucket_name

# CDN domain
terraform output cloudfront_domain_name

# Application configuration
terraform output application_config
```

## Cost Optimization

### Development

- Use `t3.micro` instances
- Enable `skip_expensive_resources = true`
- Set `enable_spot_instances = true`
- Minimize `db_allocated_storage`

### Production

- Right-size instances based on load testing
- Enable S3 lifecycle policies
- Use Reserved Instances for predictable workloads
- Monitor costs with AWS Cost Explorer

## Security Considerations

### Network Security

- Database in private subnets only
- Security groups with least privilege
- VPC Flow Logs enabled (add if needed)

### Data Security

- S3 server-side encryption enabled
- RDS encryption at rest enabled
- Transit encryption for Redis/RDS

### Access Security

- IAM roles with minimal permissions
- CloudTrail for audit logging (add if needed)  
- AWS Config for compliance (add if needed)

### Secrets Management

```bash
# Store sensitive values in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "inscenium/database/password" \
  --secret-string "your-secure-password"
```

## Monitoring and Logging

### CloudWatch

```bash
# Enable CloudWatch logs
terraform apply -var="enable_cloudwatch_logs=true"

# Set retention policy
terraform apply -var="log_retention_days=30"
```

### Application Monitoring

Add these resources for production:

- CloudWatch dashboards
- SNS alerts for critical metrics
- X-Ray tracing for API performance

## Disaster Recovery

### Backup Strategy

- RDS automated backups (7-30 days retention)
- S3 cross-region replication (add if needed)
- Database point-in-time recovery

### Recovery Procedures

```bash
# Database recovery from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier inscenium-restored \
  --db-snapshot-identifier rds:inscenium-dev-2024-01-01

# S3 data recovery
aws s3 sync s3://backup-bucket s3://primary-bucket --delete
```

## Maintenance

### Updates

```bash
# Update Terraform providers
terraform init -upgrade

# Plan and apply changes
terraform plan
terraform apply
```

### Cleanup

```bash
# Destroy development resources
terraform destroy -var="environment=dev"

# Clean up state files
rm -rf .terraform
rm terraform.tfstate*
```

## Troubleshooting

### Common Issues

**Terraform Init Fails**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify S3 backend bucket exists and is accessible

**RDS Connection Issues**
- Ensure security groups allow access
- Check VPC routing and NACLs
- Verify database is in correct subnets

**S3 Access Denied**
- Confirm bucket policies and IAM permissions
- Check CloudFront OAI configuration

**High Costs**
- Review instance sizes and storage allocations
- Check for unattached EBS volumes
- Monitor data transfer costs

### Debug Mode

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
terraform plan

# AWS CLI debug mode
aws s3 ls --debug
```

## Support

For infrastructure issues:

1. Check Terraform plan output for changes
2. Review AWS CloudFormation events (if applicable)
3. Check CloudWatch logs for application errors
4. Consult AWS Support for service-specific issues

## Future Enhancements

Planned additions:

- [ ] EKS cluster with GPU node groups
- [ ] Application Load Balancer configuration
- [ ] WAF security rules
- [ ] Route53 DNS management
- [ ] Certificate Manager SSL certificates
- [ ] Systems Manager Parameter Store integration
- [ ] Lambda functions for automation
- [ ] API Gateway for serverless components