output "gke_cluster_name" {
  value       = google_container_cluster.gke.name
  description = "GKE Cluster Name"
}

output "gke_connection_command" {
  value       = "gcloud container clusters get-credentials ${google_container_cluster.gke.name} --region ${var.gcp_region} --project ${var.gcp_project_id}"
  description = "gcloud CLI command to connect to GKE cluster"
}

output "postgres_instance_ip" {
  value       = google_sql_database_instance.postgres.private_ip_address
  description = "PostgreSQL instance private IP address"
}

output "redis_instance_ip" {
  value       = google_redis_instance.redis.host
  description = "MemoryStore Redis instance connection IP"
}
