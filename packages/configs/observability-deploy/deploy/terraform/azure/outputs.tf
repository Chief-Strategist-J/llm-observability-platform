output "aks_cluster_name" {
  value       = azurerm_kubernetes_cluster.aks.name
  description = "AKS Cluster Name"
}

output "aks_kube_config_command" {
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_kubernetes_cluster.aks.name}"
  description = "Azure CLI command to fetch kubeconfig for AKS cluster"
}

output "postgres_server_fqdn" {
  value       = azurerm_postgresql_flexible_server.postgres.fqdn
  description = "FQDN of the PostgreSQL server"
}

output "redis_hostname" {
  value       = azurerm_redis_cache.redis.hostname
  description = "Azure Cache for Redis connection host name"
}

output "redis_ssl_port" {
  value       = azurerm_redis_cache.redis.ssl_port
  description = "Azure Cache for Redis connection SSL port"
}
