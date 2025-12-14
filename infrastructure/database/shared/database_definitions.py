from enum import Enum

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
