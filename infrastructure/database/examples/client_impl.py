import logging
from database_client_base import (
    ConnectionConfig,
    DatabaseType,
    SecurityConfig,
    SecurityLevel,
    EventConfig,
    create_secure_client
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
)
logger = logging.getLogger(__name__)


def mongodb_direct_example():
    logger.info("example_mongodb_direct_start")
    
    security = SecurityConfig(
        level=SecurityLevel.BASIC,
        rate_limit=100,
        rate_window=60
    )
    
    config = ConnectionConfig(
        db_type=DatabaseType.MONGODB,
        host="localhost",
        port=27017,
        username="admin",
        password="MongoPassword123!",
        database="testdb",
        auth_database="admin",
        security=security,
        pool_size=10,
        connection_timeout=30
    )
    
    try:
        with create_secure_client(config) as client:
            logger.info("mongodb_client_connected")
            
            health = client.health_check()
            logger.info("mongodb_health_check result=%s", health)
            
            doc_id = client.insert_one("users", {
                "name": "Alice Smith",
                "email": "alice@example.com",
                "age": 28,
                "role": "developer"
            })
            logger.info("mongodb_document_inserted id=%s", doc_id)
            
            user = client.find_one("users", {"name": "Alice Smith"})
            logger.info("mongodb_user_found user=%s", user)
            
            client.update_one("users", {"name": "Alice Smith"}, {"age": 29})
            logger.info("mongodb_user_updated")
            
            users = client.find_many("users", {"age": {"$gte": 25}}, limit=10)
            logger.info("mongodb_users_found count=%s", len(users))
            
            pipeline = [
                {"$match": {"role": "developer"}},
                {"$group": {"_id": "$role", "avg_age": {"$avg": "$age"}, "count": {"$sum": 1}}}
            ]
            agg_results = client.aggregate("users", pipeline)
            logger.info("mongodb_aggregation_complete results=%s", agg_results)
            
            client.create_index("users", [("email", 1)], unique=True)
            logger.info("mongodb_index_created")
            
            metrics = client.get_metrics()
            logger.info("mongodb_metrics ops=%s errors=%s", 
                       metrics['operations'], metrics['errors'])
        
        logger.info("example_mongodb_direct_complete")
        
    except Exception as e:
        logger.exception("example_mongodb_direct_error error=%s", e)


def mongodb_event_driven_example():
    logger.info("example_mongodb_event_driven_start")
    
    security = SecurityConfig(
        level=SecurityLevel.TOKEN,
        rate_limit=100
    )
    
    event_config = EventConfig(
        enabled=True,
        kafka_bootstrap_servers="localhost:9092",
        kafka_topic_prefix="db_events",
        batch_size=100,
        compression_type="gzip"
    )
    
    config = ConnectionConfig(
        db_type=DatabaseType.MONGODB,
        host="localhost",
        port=27017,
        username="admin",
        password="MongoPassword123!",
        database="testdb",
        auth_database="admin",
        security=security
    )
    
    try:
        with create_secure_client(config, event_config) as client:
            logger.info("mongodb_event_client_connected")
            
            doc_ids = client.insert_many("orders", [
                {"order_id": f"ORD{i:04d}", "amount": 100 + i, "status": "pending"}
                for i in range(1, 6)
            ])
            logger.info("mongodb_bulk_insert count=%s", len(doc_ids))
            
            client.update_many("orders", {"status": "pending"}, {"status": "processing"})
            logger.info("mongodb_bulk_update_complete")
            
            metrics = client.get_metrics()
            logger.info("mongodb_event_metrics ops=%s events=%s",
                       metrics['operations'], metrics['events_published'])
        
        logger.info("example_mongodb_event_driven_complete")
        
    except Exception as e:
        logger.exception("example_mongodb_event_driven_error error=%s", e)


def redis_direct_example():
    logger.info("example_redis_direct_start")
    
    security = SecurityConfig(level=SecurityLevel.NONE)
    
    config = ConnectionConfig(
        db_type=DatabaseType.REDIS,
        host="localhost",
        port=6379,
        database="0",
        security=security,
        pool_size=10
    )
    
    try:
        with create_secure_client(config) as client:
            logger.info("redis_client_connected")
            
            health = client.health_check()
            logger.info("redis_health_check result=%s", health)
            
            client.set("user:1001:name", "Bob Johnson", ex=3600)
            logger.info("redis_string_set")
            
            name = client.get("user:1001:name")
            logger.info("redis_string_get value=%s", name)
            
            client.hset("user:1001:profile", {
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "age": "32",
                "city": "San Francisco"
            })
            logger.info("redis_hash_set")
            
            profile = client.hgetall("user:1001:profile")
            logger.info("redis_hash_get profile=%s", profile)
            
            client.lpush("notifications", "Welcome!", "New message", "System update")
            logger.info("redis_list_push")
            
            notifications = client.lrange("notifications", 0, -1)
            logger.info("redis_list_range count=%s", len(notifications))
            
            counter = client.incr("page:views", 1)
            logger.info("redis_counter_incr value=%s", counter)
            
            metrics = client.get_metrics()
            logger.info("redis_metrics ops=%s errors=%s",
                       metrics['operations'], metrics['errors'])
        
        logger.info("example_redis_direct_complete")
        
    except Exception as e:
        logger.exception("example_redis_direct_error error=%s", e)


def neo4j_direct_example():
    logger.info("example_neo4j_direct_start")
    
    security = SecurityConfig(
        level=SecurityLevel.BASIC,
        rate_limit=50
    )
    
    config = ConnectionConfig(
        db_type=DatabaseType.NEO4J,
        host="localhost",
        port=7687,
        username="neo4j",
        password="Neo4jPassword123!",
        database="neo4j",
        security=security,
        pool_size=5
    )
    
    try:
        with create_secure_client(config) as client:
            logger.info("neo4j_client_connected")
            
            health = client.health_check()
            logger.info("neo4j_health_check result=%s", health)
            
            client.create_node("Person", {"name": "Charlie", "age": 35})
            logger.info("neo4j_node_created")
            
            client.create_node("Person", {"name": "Diana", "age": 30})
            logger.info("neo4j_node_created")
            
            client.create_relationship(
                "Person", {"name": "Charlie"},
                "Person", {"name": "Diana"},
                "KNOWS",
                {"since": 2020}
            )
            logger.info("neo4j_relationship_created")
            
            persons = client.find_nodes("Person", limit=10)
            logger.info("neo4j_nodes_found count=%s", len(persons))
            
            query = """
            MATCH (p:Person)-[r:KNOWS]->(friend:Person)
            RETURN p.name as person, friend.name as friend, r.since as since
            """
            results = client.execute_query(query)
            logger.info("neo4j_query_executed result_count=%s", len(results))
            
            metrics = client.get_metrics()
            logger.info("neo4j_metrics ops=%s errors=%s",
                       metrics['operations'], metrics['errors'])
        
        logger.info("example_neo4j_direct_complete")
        
    except Exception as e:
        logger.exception("example_neo4j_direct_error error=%s", e)


def qdrant_direct_example():
    logger.info("example_qdrant_direct_start")
    
    security = SecurityConfig(level=SecurityLevel.NONE)
    
    config = ConnectionConfig(
        db_type=DatabaseType.QDRANT,
        host="localhost",
        port=6333,
        security=security
    )
    
    try:
        with create_secure_client(config) as client:
            logger.info("qdrant_client_connected")
            
            health = client.health_check()
            logger.info("qdrant_health_check result=%s", health)
            
            client.create_collection("documents", vector_size=384, distance="Cosine")
            logger.info("qdrant_collection_created")
            
            points = [
                {
                    "id": i,
                    "vector": [0.1 * i] * 384,
                    "payload": {"text": f"Document {i}", "category": "technical"}
                }
                for i in range(1, 11)
            ]
            client.upsert_points("documents", points)
            logger.info("qdrant_points_upserted count=%s", len(points))
            
            query_vector = [0.5] * 384
            results = client.search("documents", query_vector, limit=5, score_threshold=0.8)
            logger.info("qdrant_search_complete result_count=%s", len(results))
            
            for result in results:
                logger.info("qdrant_search_result id=%s score=%s payload=%s",
                           result['id'], result['score'], result['payload'])
            
            collections = client.list_collections()
            logger.info("qdrant_collections_listed count=%s", len(collections))
            
            metrics = client.get_metrics()
            logger.info("qdrant_metrics ops=%s errors=%s",
                       metrics['operations'], metrics['errors'])
        
        logger.info("example_qdrant_direct_complete")
        
    except Exception as e:
        logger.exception("example_qdrant_direct_error error=%s", e)


def multi_database_workflow_example():
    logger.info("example_multi_database_workflow_start")
    
    try:
        security = SecurityConfig(level=SecurityLevel.BASIC)
        
        event_config = EventConfig(
            enabled=True,
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic_prefix="workflow_events"
        )
        
        mongo_config = ConnectionConfig(
            db_type=DatabaseType.MONGODB,
            host="localhost",
            port=27017,
            username="admin",
            password="MongoPassword123!",
            database="workflow_db",
            auth_database="admin",
            security=security
        )
        
        redis_config = ConnectionConfig(
            db_type=DatabaseType.REDIS,
            host="localhost",
            port=6379,
            database="0",
            security=security
        )
        
        neo4j_config = ConnectionConfig(
            db_type=DatabaseType.NEO4J,
            host="localhost",
            port=7687,
            username="neo4j",
            password="Neo4jPassword123!",
            database="neo4j",
            security=security
        )
        
        with create_secure_client(mongo_config, event_config) as mongo_client, \
             create_secure_client(redis_config) as redis_client, \
             create_secure_client(neo4j_config) as neo4j_client:
            
            logger.info("workflow_all_clients_connected")
            
            user_id = mongo_client.insert_one("users", {
                "username": "workflow_user",
                "email": "workflow@example.com",
                "created_at": "2024-01-01"
            })
            logger.info("workflow_user_created mongo_id=%s", user_id)
            
            redis_client.hset(f"user:{user_id}", {
                "session_id": "sess_12345",
                "last_active": "2024-01-01T12:00:00",
                "status": "active"
            })
            logger.info("workflow_session_cached redis_key=user:%s", user_id)
            
            neo4j_client.create_node("User", {
                "user_id": user_id,
                "username": "workflow_user"
            })
            logger.info("workflow_graph_node_created")
            
            mongo_metrics = mongo_client.get_metrics()
            redis_metrics = redis_client.get_metrics()
            neo4j_metrics = neo4j_client.get_metrics()
            
            logger.info("workflow_metrics mongo_ops=%s redis_ops=%s neo4j_ops=%s events=%s",
                       mongo_metrics['operations'],
                       redis_metrics['operations'],
                       neo4j_metrics['operations'],
                       mongo_metrics['events_published'])
        
        logger.info("example_multi_database_workflow_complete")
        
    except Exception as e:
        logger.exception("example_multi_database_workflow_error error=%s", e)


def security_features_example():
    logger.info("example_security_features_start")
    
    try:
        security = SecurityConfig(
            level=SecurityLevel.TOKEN,
            rate_limit=10,
            rate_window=60,
            validate_ssl=False,
            timeout=30,
            max_retries=3
        )
        
        logger.info("security_token_generated token=%s", security.token[:10] + "...")
        
        test_value = "sensitive_password_123"
        encrypted = security.encrypt_value(test_value)
        logger.info("security_value_encrypted original_length=%s encrypted_length=%s",
                   len(test_value), len(encrypted))
        
        decrypted = security.decrypt_value(encrypted)
        logger.info("security_value_decrypted matches=%s", decrypted == test_value)
        
        valid = security.validate_token(security.token)
        logger.info("security_token_validation result=%s", valid)
        
        invalid = security.validate_token("wrong_token")
        logger.info("security_invalid_token_validation result=%s", invalid)
        
        config = ConnectionConfig(
            db_type=DatabaseType.REDIS,
            host="localhost",
            port=6379,
            security=security
        )
        
        with create_secure_client(config) as client:
            logger.info("security_client_connected_with_rate_limit")
            
            for i in range(15):
                try:
                    client.set(f"test:key:{i}", f"value_{i}")
                    logger.info("security_operation_succeeded iteration=%s", i)
                except Exception as e:
                    logger.warning("security_rate_limit_hit iteration=%s error=%s", i, e)
                    break
            
            metrics = client.get_metrics()
            logger.info("security_metrics ops=%s errors=%s",
                       metrics['operations'], metrics['errors'])
        
        logger.info("example_security_features_complete")
        
    except Exception as e:
        logger.exception("example_security_features_error error=%s", e)


if __name__ == "__main__":
    logger.info("examples_execution_start")
    
    logger.info("running_mongodb_direct_example")
    mongodb_direct_example()
    
    logger.info("running_mongodb_event_driven_example")
    mongodb_event_driven_example()
    
    logger.info("running_redis_direct_example")
    redis_direct_example()
    
    logger.info("running_neo4j_direct_example")
    neo4j_direct_example()
    
    logger.info("running_qdrant_direct_example")
    qdrant_direct_example()
    
    logger.info("running_multi_database_workflow_example")
    multi_database_workflow_example()
    
    logger.info("running_security_features_example")
    security_features_example()
    
    logger.info("examples_execution_complete")