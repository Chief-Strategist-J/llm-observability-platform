import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import redis
from redis import Redis, ConnectionPool
from pydantic import BaseModel, Field, ConfigDict

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient


class RedisConnectionConfig(BaseModel):
    model_config = ConfigDict(extra='allow')
    host: str = Field("172.29.0.50")
    port: int = Field(6379)
    database: int = Field(0)
    password: Optional[str] = Field("RedisPassword123!")
    connection_timeout: int = Field(30)
    socket_timeout: int = Field(30)
    max_connections: int = Field(100)
    decode_responses: bool = Field(True)


class RedisQueryResult(BaseModel):
    result: Any
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    command: Optional[str] = None
    key_count: Optional[int] = None


obs = ObservabilityClient(service_name="redis-client")


def get_connection_pool(config: Optional[RedisConnectionConfig] = None) -> ConnectionPool:
    if config is None:
        config = RedisConnectionConfig()
    
    obs.log_info("Initializing Redis connection pool", {
        "host": config.host,
        "port": config.port,
        "database": config.database
    })
    
    try:
        pool = ConnectionPool(
            host=config.host,
            port=config.port,
            db=config.database,
            password=config.password,
            connection_timeout=config.connection_timeout,
            socket_timeout=config.socket_timeout,
            max_connections=config.max_connections,
            decode_responses=config.decode_responses
        )
        
        obs.log_info("Redis connection pool initialized successfully")
        return pool
    
    except Exception as e:
        obs.log_error(f"Failed to initialize Redis connection pool: {e}")
        raise


def get_redis_client(config: Optional[RedisConnectionConfig] = None) -> Redis:
    try:
        pool = get_connection_pool(config)
        client = Redis(connection_pool=pool)
        
        # Test connection
        client.ping()
        
        obs.log_info("Redis client initialized successfully")
        return client
    
    except Exception as e:
        obs.log_error(f"Failed to create Redis client: {e}")
        raise


def execute_command(
    client: Redis,
    command: str,
    *args,
    **kwargs
) -> RedisQueryResult:
    start_time = datetime.now()
    
    try:
        # Execute the command
        result = client.execute_command(command, *args, **kwargs)
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Count keys if applicable
        key_count = None
        if command.upper() in ['KEYS', 'HKEYS', 'SCAN', 'HSCAN', 'SSCAN', 'ZSCAN']:
            if isinstance(result, list):
                key_count = len(result)
            elif isinstance(result, dict):
                key_count = len(result)
        
        obs.log_info(f"Redis command executed successfully", {
            "command": command,
            "execution_time_ms": execution_time_ms,
            "key_count": key_count
        })
        
        return RedisQueryResult(
            result=result,
            execution_time_ms=execution_time_ms,
            success=True,
            command=command,
            key_count=key_count
        )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Redis command execution failed: {e}")
        
        return RedisQueryResult(
            result=None,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e),
            command=command
        )


def execute_query_with_timing(
    client: Redis,
    query: str,
    *args,
    **kwargs
) -> RedisQueryResult:
    """Execute a Redis query with detailed timing information"""
    start_time = datetime.now()
    
    try:
        # Parse the query into command and arguments
        parts = query.split()
        command = parts[0].upper()
        query_args = parts[1:] + list(args)
        
        # Execute with timing
        result = client.execute_command(command, *query_args, **kwargs)
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get additional info based on command type
        key_count = None
        memory_usage = None
        
        if command in ['KEYS', 'HKEYS', 'SCAN', 'HSCAN', 'SSCAN', 'ZSCAN']:
            key_count = len(result) if isinstance(result, (list, dict)) else 1
        elif command in ['MEMORY', 'INFO']:
            memory_usage = result if command == 'MEMORY' else None
        
        obs.log_info(f"Redis query executed successfully", {
            "query": query,
            "command": command,
            "execution_time_ms": execution_time_ms,
            "key_count": key_count
        })
        
        return RedisQueryResult(
            result=result,
            execution_time_ms=execution_time_ms,
            success=True,
            command=command,
            key_count=key_count
        )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Redis query execution failed: {e}")
        
        return RedisQueryResult(
            result=None,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e),
            command=query.split()[0].upper() if query else 'UNKNOWN'
        )


def get_database_info(client: Redis) -> Dict[str, Any]:
    try:
        info = {}
        
        # Get basic info
        info_command = client.info()
        if info_command:
            info['server_info'] = info_command
        
        # Get database size
        db_size = client.dbsize()
        info['database_size'] = db_size
        
        # Get memory usage
        memory_info = client.info('memory')
        if memory_info:
            info['memory_info'] = memory_info
        
        # Get key space info
        keyspace_info = client.info('keyspace')
        if keyspace_info:
            info['keyspace_info'] = keyspace_info
        
        return {
            "success": True,
            "info": info,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"Failed to get database info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_key_statistics(client: Redis, pattern: str = "*") -> Dict[str, Any]:
    try:
        stats = {}
        
        # Get all keys matching pattern
        keys = client.keys(pattern)
        stats['total_keys'] = len(keys)
        
        # Analyze key types
        key_types = {}
        for key in keys[:1000]:  # Limit to first 1000 keys for performance
            key_type = client.type(key)
            if key_type not in key_types:
                key_types[key_type] = 0
            key_types[key_type] += 1
        
        stats['key_types'] = key_types
        
        # Get memory usage for sample keys
        memory_usage = {}
        for key in keys[:100]:  # Sample first 100 keys
            try:
                memory = client.memory_usage(key)
                if memory:
                    memory_usage[key] = memory
            except:
                pass
        
        stats['sample_memory_usage'] = memory_usage
        
        return stats
    
    except Exception as e:
        obs.log_error(f"Failed to get key statistics: {e}")
        return {}


def get_slow_log(client: Redis) -> List[Dict[str, Any]]:
    try:
        # Get slow log (last 10 entries)
        slow_log = client.slowlog_get(10)
        
        formatted_log = []
        for entry in slow_log:
            formatted_log.append({
                "id": entry[0],
                "timestamp": datetime.fromtimestamp(entry[1]).isoformat() if entry[1] > 0 else None,
                "execution_time_micros": entry[2],
                "command": entry[3],
                "client_info": entry[4] if len(entry) > 4 else None
            })
        
        return formatted_log
    
    except Exception as e:
        obs.log_error(f"Failed to get slow log: {e}")
        return []


def close_connection_pool(pool: ConnectionPool):
    try:
        pool.disconnect()
        obs.log_info("Redis connection pool closed successfully")
    except Exception as e:
        obs.log_error(f"Failed to close Redis connection pool: {e}")


class RedisTransactionManager:
    def __init__(self, client: Redis):
        self.client = client
        self.obs = ObservabilityClient(service_name="redis-transaction-manager")

    def execute_transaction(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            with self.client.pipeline() as pipe:
                for cmd in commands:
                    command = cmd["command"]
                    args = cmd.get("args", [])
                    
                    if args:
                        getattr(pipe, command.lower())(*args)
                    else:
                        getattr(pipe, command.lower())()
                
                results = pipe.execute()
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                self.obs.log_info(f"Redis transaction executed successfully", {
                    "commands_count": len(commands),
                    "execution_time_ms": execution_time_ms
                })
                
                return {
                    "success": True,
                    "results": results,
                    "execution_time_ms": execution_time_ms,
                    "commands_count": len(commands)
                }
        
        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Redis transaction execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "commands_count": len(commands)
            }

    def execute_batch_commands(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple commands in a pipeline without transaction"""
        start_time = datetime.now()
        
        try:
            with self.client.pipeline() as pipe:
                for cmd in commands:
                    command = cmd["command"]
                    args = cmd.get("args", [])
                    
                    if args:
                        getattr(pipe, command.lower())(*args)
                    else:
                        getattr(pipe, command.lower())()
                
                results = pipe.execute()
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                self.obs.log_info(f"Redis batch commands executed successfully", {
                    "commands_count": len(commands),
                    "execution_time_ms": execution_time_ms
                })
                
                return {
                    "success": True,
                    "results": results,
                    "execution_time_ms": execution_time_ms,
                    "commands_count": len(commands)
                }
        
        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Redis batch commands execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "commands_count": len(commands)
            }


class RedisPubSubManager:
    def __init__(self, client: Redis):
        self.client = client
        self.obs = ObservabilityClient(service_name="redis-pubsub-manager")
        self.pubsub = None

    def subscribe_to_channels(self, channels: List[str]) -> bool:
        try:
            self.pubsub = self.client.pubsub()
            self.pubsub.subscribe(*channels)
            
            self.obs.log_info(f"Subscribed to Redis channels: {channels}")
            return True
        
        except Exception as e:
            self.obs.log_error(f"Failed to subscribe to channels: {e}")
            return False

    def publish_message(self, channel: str, message: str) -> bool:
        try:
            result = self.client.publish(channel, message)
            
            self.obs.log_info(f"Published message to channel {channel}", {
                "subscribers": result
            })
            return True
        
        except Exception as e:
            self.obs.log_error(f"Failed to publish message: {e}")
            return False

    def listen_for_messages(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        messages = []
        
        try:
            if self.pubsub:
                message = self.pubsub.get_message(timeout=timeout)
                if message:
                    messages.append({
                        "channel": message['channel'],
                        "type": message['type'],
                        "data": message['data'],
                        "pattern": message.get('pattern')
                    })
        except Exception as e:
            self.obs.log_error(f"Failed to listen for messages: {e}")
        
        return messages

    def close(self):
        try:
            if self.pubsub:
                self.pubsub.close()
                self.obs.log_info("Redis pubsub connection closed")
        except Exception as e:
            self.obs.log_error(f"Failed to close pubsub connection: {e}")
