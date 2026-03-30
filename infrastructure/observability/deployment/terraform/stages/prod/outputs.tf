output "ecr_repository_url" {
  value = aws_ecr_repository.observability_repo.repository_url
}
output "eks_cluster_endpoint" {
  value = aws_eks_cluster.observability_cluster.endpoint
}
