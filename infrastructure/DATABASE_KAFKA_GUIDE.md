# Database & Kafka Infrastructure Guide

Complete guide for MongoDB, Kafka, and Next.js web app integration with testing and troubleshooting instructions.

## Prerequisites
1. **Temporal Server**: Running on `localhost:7233`
2. **Python Environment**: Activate virtual environment
3. **Project Root**: `/home/j/live/dinesh/llm-chatbot-python`

```bash
source .venv/bin/activate
temporal workflow list --limit 1
```

---

## MongoDB + Mongo Express

### Start MongoDB Service

**Terminal 1: Start Worker**
```bash
cd /home/j/live/dinesh/llm-chatbot-python
source .venv/bin/activate
python infrastructure/orchestrator/workers/kafka_mango_database_worker.py
```

**Terminal 2: Trigger Workflow**
```bash
source .venv/bin/activate
cd /home/j/live/dinesh/llm-chatbot-python
python infrastructure/orchestrator/trigger/common/kafka_database_start.py
```

**Service Details:**
- Traefik: Reverse proxy (automatically started)
- MongoDB: `localhost:27017`
- Mongo Express: `http://scaibu.mongoexpress` or `http://localhost:8081`
- Kafka: `localhost:9092`
- Credentials: `admin` / `MongoExpressPassword123!`

**Run E2E Test:**
```bash
python infrastructure/orchestrator/trigger/common/kafka_database_start.py test
```

**Verify MongoDB:**
```bash
docker ps | grep mongo
python infrastructure/database/examples/client_impl.py
```

### MongoDB Database Schema

**Messages Collection (Chat)**
```typescript
{
  _id: ObjectId,
  conversationId: string,
  text: string,
  sender: "me" | "other",
  author: string,
  avatar: string,
  time: string,
  createdAt: Date
}
```

**Discussions Collection (Group Chat)**
```typescript
{
  _id: ObjectId,
  author: string,
  avatar: string,
  time: string,
  content: string,
  upvotes: number,
  downvotes: number,
  userVote: "up" | "down" | null,
  replies: Discussion[],
  createdAt: Date
}
```

---

## Kafka Messaging

### Start Kafka Services

**Terminal 1: Start Kafka Worker**
```bash
cd /home/j/live/dinesh/llm-chatbot-python
source .venv/bin/activate
python infrastructure/orchestrator/workers/kafka_messaging_worker.py
```

**Worker Details:**
- Queue: `kafka-messaging-queue`
- Workflows: Producer, Consumer, Topic Management, E2E Messaging
- Activities: 25+ Kafka operations
- Max Concurrency: 10

**Terminal 2: Trigger Kafka E2E Test**
```bash
source .venv/bin/activate
cd /home/j/live/dinesh/llm-chatbot-python

python - << 'EOF'
import asyncio
from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

class KafkaE2ETest(PipelineExecutor):
    pass

async def main():
    config = WorkflowConfig(
        service_name="kafka-e2e-test",
        workflow_name="KafkaE2EMessagingWorkflow",
        task_queue="kafka-messaging-queue",
        params={
            "topic_name": "test-topic",
            "test_messages_count": 10,
            "num_partitions": 3,
            "instance_id": 0,
            "cleanup": True
        }
    )
    pipeline = KafkaE2ETest(config=config)
    await pipeline.run_pipeline()

asyncio.run(main())
EOF
```

### Kafka UI

**Access:** `http://localhost:8080` or `http://scaibu.kafka-ui`

**Start Kafka UI** (if not running):
```bash
docker-compose -f infrastructure/orchestrator/config/docker/kafka-ui-dynamic-docker.yaml up -d
```

---

## Next.js Web Application

### Project Structure
```
service/llm_chat_web/
├── app/
│   ├── api/
│   │   ├── chat/route.ts
│   │   └── group-chat/route.ts
│   └── dashboard/
│       ├── chat/page.tsx
│       └── group-chat/page.tsx
├── database/
│   ├── services/
│   │   ├── chat-service.ts
│   │   └── group-chat-service.ts
│   └── mongo-client.ts
└── utils/
    └── api/
        ├── chat-client.ts
        └── group-chat-client.ts
```

### MongoDB Configuration

**Create `.env.local`** in `service/llm_chat_web/`:
```bash
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=chatbot
MONGODB_USERNAME=admin
MONGODB_PASSWORD=MongoPassword123!
```

### Start Next.js App

```bash
cd /home/j/live/dinesh/llm-chatbot-python/service/llm_chat_web
npm run dev
```

**Access:** `http://localhost:3000/dashboard/group-chat`

**Expected Results:**
- ✅ No authentication errors in logs
- ✅ Discussions load successfully
- ✅ Can create new discussions
- ✅ Data persists after page refresh

---

## Test MongoDB Client

```python
import asyncio
from infrastructure.database.client.mongodb_client import MongoDBClient, MongoDBConfig

async def test_mongodb():
    config = MongoDBConfig(
        host="localhost",
        port=27017,
        username="admin",
        password="MongoPassword123!",
        database="test_db"
    )
    
    client = MongoDBClient(config)
    await client.connect()
    
    doc_id = await client.insert_one("test_collection", {"message": "Hello MongoDB!"})
    print(f"Inserted document: {doc_id}")
    
    docs = await client.find_many("test_collection", {}, limit=10)
    print(f"Found {len(docs)} documents")
    
    await client.disconnect()

asyncio.run(test_mongodb())
```

---

## Test Kafka Producer

```python
import asyncio
from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

class KafkaProducerTest(PipelineExecutor):
    pass

async def main():
    config = WorkflowConfig(
        service_name="kafka-producer-test",
        workflow_name="KafkaProducerWorkflow",
        task_queue="kafka-messaging-queue",
        params={
            "messages": [
                {"topic": "test-topic", "value": "Message 1", "key": "key-1"},
                {"topic": "test-topic", "value": "Message 2", "key": "key-2"},
                {"topic": "test-topic", "value": "Message 3", "key": "key-3"}
            ],
            "bootstrap_servers": ["localhost:9092"],
            "flush": True
        }
    )
    pipeline = KafkaProducerTest(config=config)
    await pipeline.run_pipeline()

asyncio.run(main())
```

---

## Verification Commands

### Check Running Workflows
```bash
temporal workflow list
temporal workflow describe -w <workflow_id>
temporal workflow show -w <workflow_id>
```

### Check Docker Containers
```bash
docker ps | grep -E 'mongo|neo4j|qdrant|redis|kafka'
docker logs <container_name>
docker inspect <container_name> | grep -A 10 Health
```

### Check Ports
```bash
netstat -tuln | grep -E '27017|8081|7687|7474|6333|6379|9092|8080'
lsof -i :27017
lsof -i :9092
lsof -i :8080
```

---

## Troubleshooting

### Mongo Express Not Reachable

**Issue:** `http://scaibu.mongoexpress` not accessible

**Solution:**
1. Restart the Mongo Express container to pick up new Traefik labels:
```bash
docker restart mongoexpress-instance-0
```

2. Verify Traefik routing:
```bash
docker logs traefik | grep mongoexpress
```

3. Check container is running:
```bash
docker ps | grep mongoexpress
```

4. Alternative access: `http://localhost:8081`

### MongoDB Connection Refused

**Error:** `ECONNREFUSED 127.0.0.1:27017`

**Solution:**
1. Check if MongoDB is running: `docker ps | grep mongo`
2. Start MongoDB workflow: `python infrastructure/orchestrator/trigger/common/kafka_database_start.py`
3. Wait 30 seconds for container startup
4. Verify: `docker logs <mongo_container_id>`

### Kafka Not Available

**Error:** `NoBrokersAvailable`

**Solution:**
```bash
docker ps | grep kafka
docker logs <kafka_container_id>
docker restart <kafka_container_id>
sleep 10
docker exec <kafka_container_id> kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### Worker Not Responding

**Error:** `No worker available`

**Solution:**
1. Ensure Temporal server is running
2. Check worker logs for errors
3. Restart the worker
4. Verify queue name matches trigger

### Port Already in Use

**Solution:**
```bash
lsof -i :<port_number>
kill -9 <PID>
```

---

## Workflow Execution Order

The `KafkaMangoDBDatabaseWorkflow` executes activities in this order:

1. **Stop**: Traefik → Kafka → MongoDB → Mongo Express
2. **Delete**: Traefik → Kafka → MongoDB → Mongo Express
3. **Start**: Traefik → Kafka → MongoDB → Mongo Express

This ensures clean teardown and restart without port conflicts or stale containers.

---

## File Locations

### Workers
- `infrastructure/orchestrator/workers/database_pipeline_worker.py`
- `infrastructure/orchestrator/workers/kafka_messaging_worker.py`
- `infrastructure/orchestrator/workers/kafka_mango_database_worker.py`

### Triggers
- `infrastructure/orchestrator/trigger/common/database_pipeline_start.py`
- `infrastructure/orchestrator/trigger/common/kafka_database_start.py` (database setup & E2E test)

### Client Examples
- `infrastructure/database/client/mongodb_client.py`
- `infrastructure/database/client/neo4j_client.py`
- `infrastructure/database/client/redis_client.py`
- `infrastructure/database/client/qdrant_client.py`
- `infrastructure/database/examples/client_impl.py`

### Configuration
- `infrastructure/orchestrator/config/port_registry.yaml`
- `infrastructure/orchestrator/.env`
- `infrastructure/orchestrator/config/docker/`

---

## Complete E2E Test

```bash
python infrastructure/orchestrator/workers/kafka_mango_database_worker.py

python infrastructure/orchestrator/workers/kafka_messaging_worker.py

python infrastructure/orchestrator/trigger/common/kafka_database_start.py

python - << 'EOF'
import asyncio
from infrastructure.orchestrator.base.base_pipeline import WorkflowConfig, PipelineExecutor

class E2ETest(PipelineExecutor):
    pass

async def main():
    config = WorkflowConfig(
        service_name="e2e-kafka-test",
        workflow_name="KafkaE2EMessagingWorkflow",
        task_queue="kafka-messaging-queue",
        params={
            "topic_name": "e2e-test-topic",
            "test_messages_count": 100,
            "num_partitions": 3,
            "instance_id": 0,
            "cleanup": True
        }
    )
    await E2ETest(config=config).run_pipeline()

asyncio.run(main())
EOF
```

**Verify:** `http://localhost:8080`

---

## Success Indicators

- ✅ Workers start without errors
- ✅ Workflows execute successfully in Temporal UI
- ✅ Docker containers are running and healthy
- ✅ Ports are accessible (MongoDB: 27017, Kafka: 9092)
- ✅ Data can be written and read from databases
- ✅ Kafka messages are produced and consumed
- ✅ LogQL structured logs appear in worker output
- ✅ Mongo Express accessible at `http://scaibu.mongoexpress`
- ✅ Next.js app persists data to MongoDB
