provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Network Layer (VPC)
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project_name}-subnet"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.gcp_region
  network       = google_compute_network.vpc.id
}

# Private Service Access for Cloud SQL & Redis
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "${var.project_name}-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_range_names    = [google_compute_global_address.private_ip_alloc.name]
}

# 2. GKE Cluster
resource "google_container_cluster" "gke" {
  name     = "${var.project_name}-cluster"
  location = var.gcp_region

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "/14"
    services_ipv4_cidr_block = "/20"
  }
}

resource "google_container_node_pool" "gke_nodes" {
  name       = "${var.project_name}-node-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.gke.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "e2-standard-4"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# 3. Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-postgres"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  depends_on       = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = "db-custom-2-7680" # 2 vCPU, 7.5GB RAM
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
}

resource "google_sql_database" "database" {
  name     = "llm_observability"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "users" {
  name     = "postgres"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# 4. Google MemoryStore Redis
resource "google_redis_instance" "redis" {
  name               = "${var.project_name}-redis"
  tier               = "BASIC"
  memory_size_gb     = 2
  region             = var.gcp_region
  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}
