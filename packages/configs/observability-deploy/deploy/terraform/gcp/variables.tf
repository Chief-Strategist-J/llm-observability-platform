variable "gcp_project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "gcp_region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region"
}

variable "project_name" {
  type        = string
  default     = "llm-obs"
  description = "Project name prefix"
}

variable "db_password" {
  type        = string
  sensitive   = true
  default     = "SuperSecurePassword123"
  description = "Cloud SQL Postgres Master Password"
}
