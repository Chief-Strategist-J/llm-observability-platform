import unittest
import yaml
import os

class TestRegistries(unittest.TestCase):
    def setUp(self):
        self.base_dir = "packages/python/instrumentation-sdk"
        self.topics_path = os.path.join(self.base_dir, "contracts/registries/topics.yaml")
        self.events_path = os.path.join(self.base_dir, "contracts/registries/events.yaml")

    def test_topic_registry_integrity(self):
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
            
            if name.endswith('.dlq'):
                self.assertEqual(topic['partitions'], 1)

    def test_event_registry_integrity(self):
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
            
            self.assertIn(event['topic'], registered_topics)
            
            full_schema_path = os.path.join(self.base_dir, event['schema_path'])
            self.assertTrue(os.path.exists(full_schema_path))
            
            self.assertTrue(event['schema_path'].startswith('contracts/'))

if __name__ == "__main__":
    unittest.main()
