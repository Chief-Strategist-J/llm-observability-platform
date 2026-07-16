variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS Target Region"
}

variable "project_name" {
  type        = string
  default     = "llm-obs"
  description = "Project name prefix"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment"
}

variable "db_password" {
  type        = string
  sensitive   = true
  default     = "SuperSecurePassword123"
  description = "RDS Postgres Master Password"
}
