import unittest
import yaml
import os

class TestRegistries(unittest.TestCase):
    def setUp(self):
        self.base_dir = "packages/python/instrumentation-sdk"
        self.topics_path = os.path.join(self.base_dir, "contracts/registries/topics.yaml")
        self.events_path = os.path.join(self.base_dir, "contracts/registries/events.yaml")

    def test_topic_registry_integrity(self):
        """Verify that the topics.yaml is well-formed and follows architectural rules."""
        self.assertTrue(os.path.exists(self.topics_path))
        with open(self.topics_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.assertIn('topics', config)
        topic_names = set()
        for topic in config['topics']:
            name = topic.get('name')
            self.assertIsNotNone(name, "Topic name must not be null")
            self.assertNotIn(name, topic_names, f"Duplicate topic name detected: {name}")
            topic_names.add(name)

            self.assertIn('partitions', topic)
            self.assertIn('replication_factor', topic)
            self.assertIn('description', topic, f"Topic {name} is missing a description")
            self.assertGreater(topic['partitions'], 0)
            
            # Architectural rule: DLQ topics should have exactly 1 partition to preserve ordering
            if name.endswith('.dlq'):
                self.assertEqual(topic['partitions'], 1, f"DLQ topic {name} must have exactly 1 partition")

    def test_event_registry_integrity(self):
        """Verify that the events.yaml points to valid topics and existing schemas."""
        self.assertTrue(os.path.exists(self.events_path))
        self.assertTrue(os.path.exists(self.topics_path))
        
        with open(self.events_path, 'r') as f:
            event_config = yaml.safe_load(f)
        with open(self.topics_path, 'r') as f:
            topic_config = yaml.safe_load(f)
            
        registered_topics = {t['name'] for t in topic_config['topics']}
        event_names = set()
        
        self.assertIn('events', event_config)
        for event in event_config['events']:
            name = event.get('name')
            self.assertIsNotNone(name, "Event name must not be null")
            self.assertNotIn(name, event_names, f"Duplicate event name detected: {name}")
            event_names.add(name)

            self.assertIn('topic', event)
            self.assertIn('schema_path', event)
            self.assertIn('description', event, f"Event {name} is missing a description")
            
            # Check that topic exists in topic registry
            self.assertIn(event['topic'], registered_topics, f"Event {name} points to unregistered topic {event['topic']}")
            
            # Check that schema file exists
            full_schema_path = os.path.join(self.base_dir, event['schema_path'])
            self.assertTrue(os.path.exists(full_schema_path), f"Schema not found for event {name} at {full_schema_path}")
            
            # Check schema path convention
            self.assertTrue(event['schema_path'].startswith('contracts/'), f"Schema path for {name} must be within contracts/ directory")

if __name__ == "__main__":
    unittest.main()
