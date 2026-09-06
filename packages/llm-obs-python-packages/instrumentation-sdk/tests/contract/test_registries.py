import unittest
import yaml
import os

class TestRegistries(unittest.TestCase):
    """
    Contract tests for the Instrumentation SDK registries.
    Ensures that Topics and Events are consistently defined and linked.
    """
    def setUp(self):
        # Paths are relative to the package root where tests are executed
        self.topics_path = "contracts/registries/topics.yaml"
        self.events_path = "contracts/registries/events.yaml"
        self.base_dir = "."

    def test_topic_registry_integrity(self):
        """Verify that topics.yaml is valid and unique."""
        self.assertTrue(os.path.exists(self.topics_path))
        with open(self.topics_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.assertIn('topics', config)
        topic_names = set()
        for topic in config['topics']:
            name = topic.get('name')
            self.assertIsNotNone(name)
            self.assertNotIn(name, topic_names)
            topic_names.add(name)

            self.assertIn('partitions', topic)
            self.assertIn('replication_factor', topic)
            self.assertIn('description', topic)
            self.assertGreater(topic['partitions'], 0)
            
            # DLQ topics must be single-partition for ordering and simplicity
            if name.endswith('.dlq'):
                self.assertEqual(topic['partitions'], 1)

    def test_event_registry_integrity(self):
        """Verify that events.yaml maps to valid topics and existing schemas."""
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
            self.assertIsNotNone(name)
            self.assertNotIn(name, event_names)
            event_names.add(name)

            self.assertIn('topic', event)
            self.assertIn('schema_path', event)
            self.assertIn('description', event)
            
            # Event topic must be defined in topics.yaml
            self.assertIn(event['topic'], registered_topics)
            
            # Schema path must exist and be within contracts directory
            full_schema_path = os.path.join(self.base_dir, event['schema_path'])
            self.assertTrue(os.path.exists(full_schema_path))
            
            self.assertTrue(event['schema_path'].startswith('contracts/'))

if __name__ == "__main__":
    unittest.main()
