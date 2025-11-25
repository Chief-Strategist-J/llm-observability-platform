# Centralized Port Management System

## Overview

The orchestrator now uses a centralized port management system that:
- **Eliminates port conflicts** automatically
- **Supports multiple instances** of the same service running in parallel
- **Centralizes all port definitions** in one YAML file
- **Auto-allocates ports** based on instance ID
- **Provides developer-friendly** logging and error messages

## Architecture

### Port Registry (`dynamicconfig/port_registry.yaml`)
Centralized YAML file defining:
- Base ports for each service
- Instance increment (default 100)
- Max instances allowed
- Service-specific multi-port configurations

### Port Manager (`base/port_manager.py`)
Singleton class that:
- Loads port registry on first use
- Calculates ports using formula: `final_port = base_port + (instance_id * increment)`
- Validates instance IDs
- Logs all port allocations
- Checks port availability

## Port Allocation Formula

```
final_port = base_port + (instance_id * increment)
```

### Examples

**Kafka Broker:**
- Instance 0: `9092 + (0 * 100) = 9092`
- Instance 1: `9092 + (1 * 100) = 9192`
- Instance 2: `9092 + (2 * 100) = 9292`

**MongoDB:**
- Instance 0: `27017 + (0 * 100) = 27017`
- Instance 1: `27017 + (1 * 100) = 27117`
- Instance 2: `27017 + (2 * 100) = 27217`

**MongoExpress:**
- Instance 0: `8081 + (0 * 100) = 8081`
- Instance 1: `8081 + (1 * 100) = 8181`

## Usage

### Running Single Instance (Default)

```python
params = {}
await workflow.execute_activity(
    "start_kafka_activity",
    params,
    start_to_close_timeout=timeout
)
```

This will use instance_id=0 (default) and allocate base ports.

### Running Multiple Instances

```python
params_instance_0 = {"instance_id": 0}
params_instance_1 = {"instance_id": 1}
params_instance_2 = {"instance_id": 2}

await workflow.execute_activity(
    "start_kafka_activity",
    params_instance_0,  
    start_to_close_timeout=timeout
)

await workflow.execute_activity(
    "start_kafka_activity",
    params_instance_1,
    start_to_close_timeout=timeout
)

await workflow.execute_activity(
    "start_kafka_activity",
    params_instance_2,
    start_to_close_timeout=timeout
)
```

### Direct Python Usage

```python
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.activities.configurations_activity.kafka_activity import KafkaManager

pm = get_port_manager()

kafka_broker_port = pm.get_port("kafka", 0, "broker_port")
kafka_controller_port = pm.get_port("kafka", 0, "controller_port")

print(f"Kafka Instance 0: broker={kafka_broker_port}, controller={kafka_controller_port}")

kafka_manager_0 = KafkaManager(instance_id=0)
kafka_manager_0.run()

kafka_manager_1 = KafkaManager(instance_id=1)
kafka_manager_1.run()
```

## Service Containers

Each instance gets unique naming:

**Instance 0 (Default):**
- Container: `kafka-development`
- Volume: `kafka-data`
- Ports: `9092:9092`, `19093:19093`

**Instance 1:**
- Container: `kafka-development-1`
- Volume: `kafka-data-1`
- Ports: `9192:9192`, `19193:19193`

**Instance 2:**
- Container: `kafka-development-2`
- Volume: `kafka-data-2`
- Ports: `9292:9292`, `19293:19293`

## Port Registry Structure

```yaml
service_name:
  port: 9092                  # For single-port services
  broker_port: 9092           # For multi-port services
  controller_port: 19093
  instance_increment: 100     # Port increment per instance
  max_instances: 10           # Maximum recommended instances
```

## Adding New Services

### 1. Add to Port Registry

Edit `dynamicconfig/port_registry.yaml`:

```yaml
my_new_service:
  port: 10000
  instance_increment: 100
  max_instances: 5
```

### 2. Update Service Activity

```python
from infrastructure.orchestrator.base.port_manager import get_port_manager

class MyNewServiceManager(BaseService):
    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None):
        self.instance_id = instance_id
        port_manager = get_port_manager()
        
        service_port = port_manager.get_port("my_new_service", instance_id, "port")
        container_name = f"my-new-service-{instance_id}" if instance_id > 0 else "my-new-service"
        
        config = ContainerConfig(
            name=container_name,
            ports={8080: service_port},
            
        )
        
        extra_data = {"service_port": service_port, "instance_id": instance_id}
        super().__init__(config=config, extra=extra_data)
```

###3. Update Activity Functions

```python
@activity.defn
async def start_my_new_service_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    manager = MyNewServiceManager(instance_id=instance_id)
    manager.run()
    return True
```

## Port Registry (`dynamicconfig/port_registry.yaml`)

Current services and their base ports:

| Service | Base Port(s) | Increment | Max Instances |
|---------|--------------|-----------|---------------|
| Kafka | 9092, 19093 | 100 | 10 |
| MongoDB | 27017 | 100 | 10 |
| MongoExpress | 8081 | 100 | 10 |
| Redis | 6379 | 100 | 10 |
| Alertmanager | 9093 | 100 | 5 |
| Prometheus | 9090 | 100 | 5 |
| Grafana | 3000 | 100 | 5 |
| Loki | 3100 | 100 | 5 |
| Jaeger | 16686 | 100 | 5 |
| Neo4j | 7474, 7687 | 100 | 5 |
| Qdrant | 6333, 6334 | 100 | 5 |
| Traefik | 80, 31001-31003 | 100 | 3 |
| Promtail | 9080 | 100 | 5 |
| Temporal | 7233, 8080, 5432 | 100 | 3 |
| ArgoCD | 8080, 8081 | 100 | 3 |

## Benefits

1. **No Manual Port Management**: Ports are automatically calculated
2. **No Conflicts**: Each instance gets unique ports
3. **Centralized Configuration**: All port definitions in one place
4. **Developer Friendly**: Clear logs show which instance uses which ports
5. **Scalable**: Add new instances without touching code
6. **Future-Ready**: Easy to add environment-based offsets later

## Testing

```bash
cd /home/j/live/dinesh/llm-chatbot-python
python3 infrastructure/orchestrator/base/port_manager.py
```

This will run built-in tests showing:
- All available services
- Kafka multi-instance allocation
- MongoDB multi-instance allocation
- Neo4j multi-port allocation
- Complete port allocation summary

## Logs

All port allocations are logged:

```
port_manager_port_allocated service=kafka instance=0 type=broker_port port=9092 base=9092 increment=100
port_manager_port_allocated service=kafka instance=1 type=broker_port port=9192 base=9092 increment=100
port_manager_port_allocated service=mongodb instance=0 type=port port=27017 base=27017 increment=100
```

Service logs also show instance information:

```
kafka_manager_initialized instance=0 name=kafka-development bootstrap=localhost:9092 broker_port=9092 controller_port=19093
kafka_manager_initialized instance=1 name=kafka-development-1 bootstrap=localhost:9192 broker_port=9192 controller_port=19193
```
