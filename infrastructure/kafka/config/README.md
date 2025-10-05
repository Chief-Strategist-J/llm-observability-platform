# Example Kafka broker configuration for different environments

# development.properties
# Lightweight settings for development
KAFKA_NUM_PARTITIONS=3
KAFKA_DEFAULT_REPLICATION_FACTOR=1

# production.properties
# Production settings with higher replication
KAFKA_NUM_PARTITIONS=6
KAFKA_DEFAULT_REPLICATION_FACTOR=3
