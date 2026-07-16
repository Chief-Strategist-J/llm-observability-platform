output "eks_cluster_name" {
  value       = module.eks.cluster_name
  description = "EKS Cluster Name"
}

output "eks_cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "EKS Control Plane Endpoint"
}

output "rds_postgres_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "PostgreSQL RDS Connection Endpoint"
}

output "redis_primary_endpoint" {
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  description = "Redis primary endpoint"
}

output "msk_bootstrap_brokers" {
  value       = aws_msk_cluster.kafka.bootstrap_brokers_tls
  description = "MSK Kafka Bootstrap Brokers TLS"
}
