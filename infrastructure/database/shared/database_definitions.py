from enum import Enum


TRAEFIK_HOST_IP = "127.0.2.1"


class DatabaseNetwork(str, Enum):
    NAME = "database-network"
    SUBNET = "172.29.0.0/16"
    GATEWAY = "172.29.0.1"


class DatabaseService(str, Enum):
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    REDIS = "redis"
    NEO4J = "neo4j"
    QDRANT = "qdrant"
    MINIO = "minio"
    CLICKHOUSE = "clickhouse"
    OPENSEARCH = "opensearch"
    CASSANDRA = "cassandra"
    MILVUS = "milvus"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"


DATABASE_CONFIG = {
    "postgres": {
        "hostnames": ["scaibu.postgres", "scaibu.pgadmin"],
        "container_ip": "172.29.0.10",
        "ui_hostname": "scaibu.pgadmin",
    },
    "mongodb": {
        "hostnames": ["scaibu.mongodb", "scaibu.mongoexpress"],
        "container_ip": "172.29.0.20",
        "ui_hostname": "scaibu.mongoexpress",
    },
    "redis": {
        "hostnames": ["scaibu.redis"],
        "container_ip": "172.29.0.30",
        "ui_hostname": "scaibu.redis",
    },
    "neo4j": {
        "hostnames": ["scaibu.neo4j"],
        "container_ip": "172.29.0.40",
        "ui_hostname": "scaibu.neo4j",
    },
    "qdrant": {
        "hostnames": ["scaibu.qdrant"],
        "container_ip": "172.29.0.50",
        "ui_hostname": "scaibu.qdrant",
    },
    "minio": {
        "hostnames": ["scaibu.minio", "scaibu.minio-console"],
        "container_ip": "172.29.0.60",
        "ui_hostname": "scaibu.minio-console",
    },
    "clickhouse": {
        "hostnames": ["scaibu.clickhouse"],
        "container_ip": "172.29.0.70",
        "ui_hostname": "scaibu.clickhouse",
    },
    "opensearch": {
        "hostnames": ["scaibu.opensearch", "scaibu.opensearch-dashboards"],
        "container_ip": "172.29.0.80",
        "ui_hostname": "scaibu.opensearch-dashboards",
    },
    "cassandra": {
        "hostnames": ["scaibu.cassandra"],
        "container_ip": "172.29.0.90",
        "ui_hostname": "scaibu.cassandra",
    },
    "milvus": {
        "hostnames": ["scaibu.milvus"],
        "container_ip": "172.29.0.100",
        "ui_hostname": "scaibu.milvus",
    },
    "weaviate": {
        "hostnames": ["scaibu.weaviate"],
        "container_ip": "172.29.0.110",
        "ui_hostname": "scaibu.weaviate",
    },
    "chroma": {
        "hostnames": ["scaibu.chroma"],
        "container_ip": "172.29.0.120",
        "ui_hostname": "scaibu.chroma",
    },
}


def get_host_entries(service_name: str) -> list:
    config = DATABASE_CONFIG.get(service_name, {})
    hostnames = config.get("hostnames", [])
    return [{"hostname": h, "ip": TRAEFIK_HOST_IP} for h in hostnames]


def get_all_hostnames(service_name: str) -> list:
    config = DATABASE_CONFIG.get(service_name, {})
    return config.get("hostnames", [])
