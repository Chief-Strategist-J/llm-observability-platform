variable "azure_location" {
  type        = string
  default     = "East US"
  description = "Azure Target Location"
}

variable "project_name" {
  type        = string
  default     = "llmobs"
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
  default     = "SuperSecurePassword123!"
  description = "Azure Database Postgres administrator password"
}
