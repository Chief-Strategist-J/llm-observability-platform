from locust import HttpUser, task, between
import json
import random


class MessagingAPIUser(HttpUser):
    wait_time = between(0, 0)
    
    def on_start(self):
        self.event_ids = []
        self.topic = "test-topic"
        self.consumer_group = "test-consumer-group"
        self.schema_id = 1
        self.subject = "test-subject"
    
    @task(3)
    def save_event(self):
        payload = {
            "topic": self.topic,
            "partition": 0,
            "offset": random.randint(1, 1000000),
            "key": f"key-{random.randint(1, 1000)}",
            "value": f"value-{random.randint(1, 1000)}",
            "timestamp": None,
            "headers": {"header1": "value1"}
        }
        with self.client.post("/api/v1/database/events", json=payload) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "event_id" in data:
                        self.event_ids.append(data["event_id"])
                        if len(self.event_ids) > 100:
                            self.event_ids.pop(0)
                except Exception:
                    pass
    
    @task(2)
    def get_event(self):
        eid = random.choice(self.event_ids) if self.event_ids else "test-event-123"
        self.client.get(f"/api/v1/database/events/{eid}")
    
    @task(2)
    def get_events_by_topic(self):
        with self.client.get(f"/api/v1/database/events?topic={self.topic}&limit=10&offset=0", catch_response=True) as response:
            if response.status_code == 200 or response.status_code == 404:
                response.success()
    
    @task(1)
    def save_events_batch(self):
        payload = {
            "events": [
                {
                    "topic": self.topic,
                    "partition": 0,
                    "offset": random.randint(1, 10000),
                    "key": f"key-{i}",
                    "value": f"value-{i}"
                }
                for i in range(5)
            ]
        }
        self.client.post("/api/v1/database/events/batch", json=payload)
    
    @task(1)
    def save_consumer_offset(self):
        payload = {
            "consumer_group": self.consumer_group,
            "topic": self.topic,
            "partition": 0,
            "offset": random.randint(1, 1000000)
        }
        with self.client.post("/api/v1/database/consumer-offsets", json=payload) as response:
            if response.status_code == 200:
                self.offset_saved = True
    
    @task(1)
    def get_consumer_offset(self):
        if getattr(self, 'offset_saved', False):
            self.client.get(f"/api/v1/database/consumer-offsets/{self.consumer_group}/{self.topic}/0")
        else:
            with self.client.get(f"/api/v1/database/consumer-offsets/{self.consumer_group}/{self.topic}/0", catch_response=True) as response:
                if response.status_code == 404:
                    response.success()
    
    @task(2)
    def register_schema(self):
        payload = {
            "subject": f"{self.subject}-{random.randint(1, 100)}",
            "schema": '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}',
            "schema_type": "AVRO"
        }
        self.client.post("/api/v1/schema-registry/schemas", json=payload)
    
    @task(2)
    def get_schema(self):
        self.client.get(f"/api/v1/schema-registry/schemas/{self.schema_id}")
    
    @task(1)
    def get_schema_by_subject(self):
        self.client.get(f"/api/v1/schema-registry/subjects/{self.subject}/latest")
    
    @task(1)
    def check_compatibility(self):
        payload = {
            "subject": self.subject,
            "schema": '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}',
            "schema_type": "AVRO"
        }
        self.client.post("/api/v1/schema-registry/compatibility", json=payload)
    
    @task(1)
    def serialize(self):
        payload = {
            "subject": self.subject,
            "data": {"id": random.randint(1, 100)},
            "schema_id": self.schema_id
        }
        self.client.post("/api/v1/schema-registry/serialize", json=payload)
    
    @task(1)
    def deserialize(self):
        import base64
        payload = {
            "data": base64.b64encode(b"test-data").decode('utf-8'),
            "schema_id": self.schema_id
        }
        self.client.post("/api/v1/schema-registry/deserialize", json=payload)
    
    @task(2)
    def process_record(self):
        payload = {
            "topic": self.topic,
            "partition": 0,
            "offset": random.randint(1, 10000),
            "key": f"key-{random.randint(1, 100)}",
            "value": f"value-{random.randint(1, 100)}",
            "timestamp": 1234567890,
            "headers": {}
        }
        self.client.post("/api/v1/event-handler/process-record", json=payload)
    
    @task(1)
    def process_records_batch(self):
        payload = {
            "records": [
                {
                    "topic": self.topic,
                    "partition": 0,
                    "offset": random.randint(1, 10000),
                    "key": f"key-{i}",
                    "value": f"value-{i}",
                    "timestamp": 1234567890,
                    "headers": {}
                }
                for i in range(5)
            ]
        }
        self.client.post("/api/v1/event-handler/process-records-batch", json=payload)
    
    @task(1)
    def get_events_by_topic_handler(self):
        with self.client.get(f"/api/v1/event-handler/events?topic={self.topic}&limit=10&offset=0", catch_response=True) as response:
            if response.status_code == 200 or response.status_code == 404:
                response.success()
    
    @task(1)
    def produce_message(self):
        payload = {
            "topic": self.topic,
            "key": f"key-{random.randint(1, 100)}",
            "value": f"value-{random.randint(1, 100)}",
            "partition": 0,
            "headers": {}
        }
        self.client.post("/api/v1/producer/produce", json=payload)
    
    @task(1)
    def list_topics_producer(self):
        self.client.get("/api/v1/producer/topics")
    
    @task(1)
    def consume_messages(self):
        payload = {
            "topic": self.topic,
            "consumer_group": self.consumer_group,
            "partition": 0,
            "max_messages": 10,
            "timeout_ms": 1000
        }
        self.client.post("/api/v1/consumer/consume", json=payload)
    
    @task(1)
    def commit_offset(self):
        payload = {
            "consumer_group": self.consumer_group,
            "topic": self.topic,
            "partition": 0,
            "offset": random.randint(1, 10000)
        }
        self.client.post("/api/v1/consumer/offsets", json=payload)
    
    @task(1)
    def get_broker_metadata(self):
        self.client.get("/api/v1/broker/metadata")
    
    @task(1)
    def list_brokers(self):
        self.client.get("/api/v1/broker/brokers")
    
    @task(1)
    def list_topics_broker(self):
        self.client.get("/api/v1/broker/topics")
    
    @task(1)
    def get_consumer_groups(self):
        self.client.get("/api/v1/broker/consumer-groups")
    
    @task(1)
    def get_cluster_config(self):
        self.client.get("/api/v1/broker/config")
