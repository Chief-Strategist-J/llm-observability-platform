// MongoDB initialization script
db = db.getSiblingDB('kafka_events');

// Create collections
db.createCollection('events');
db.createCollection('consumer_offsets');

// Create indexes for events collection
db.events.createIndex({ "event_id": 1 }, { unique: true });
db.events.createIndex({ "topic": 1, "partition": 1, "offset": 1 }, { unique: true });
db.events.createIndex({ "topic": 1 });
db.events.createIndex({ "processed": 1 });
db.events.createIndex({ "timestamp": 1 });

// Create indexes for consumer_offsets collection
db.consumer_offsets.createIndex({ "consumer_group": 1, "topic": 1, "partition": 1 }, { unique: true });
db.consumer_offsets.createIndex({ "consumer_group": 1 });

// Insert sample data (optional)
db.events.insertOne({
  event_id: "sample-event-1",
  topic: "test-topic",
  partition: 0,
  offset: 0,
  key: "test-key",
  value: { message: "Sample event", timestamp: new Date() },
  timestamp: new Date(),
  headers: {},
  processed: false,
  created_at: new Date(),
  updated_at: new Date()
});

print("MongoDB initialization completed successfully");
