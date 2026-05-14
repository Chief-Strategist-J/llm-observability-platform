import unittest
import yaml
import subprocess
import os

class TestKafkaProvisioning(unittest.TestCase):
    def setUp(self):
        self.topics_file = "packages/python/instrumentation-sdk/contracts/registries/topics.yaml"
        self.kafka_container = "docker-kafka-1"
        self.bootstrap_server = "kafka:29092"
        
        if not os.path.exists(self.topics_file):
            self.fail(f"Registry file not found at {self.topics_file}")
            
        with open(self.topics_file, 'r') as f:
            self.registry = yaml.safe_load(f)

    def _run_kafka_cmd(self, args):
        cmd = ["docker", "exec", self.kafka_container] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_live_topics_match_registry(self):
        result = self._run_kafka_cmd(["kafka-topics", "--list", "--bootstrap-server", self.bootstrap_server])
        
        if result.returncode != 0:
            self.skipTest(f"Kafka container not accessible or not running: {result.stderr}")
            
        actual_topics = set(result.stdout.strip().split('\n'))
        
        for topic in self.registry['topics']:
            name = topic['name']
            with self.subTest(topic=name):
                self.assertIn(name, actual_topics, f"Topic '{name}' exists in registry but was not found in Kafka")

    def test_topic_partition_integrity(self):
        for topic in self.registry['topics']:
            name = topic['name']
            expected_partitions = topic['partitions']
            
            result = self._run_kafka_cmd([
                "kafka-topics", "--describe", 
                "--topic", name, 
                "--bootstrap-server", self.bootstrap_server
            ])
            
            if result.returncode == 0:
                with self.subTest(topic=name):
                    self.assertIn(f"PartitionCount: {expected_partitions}", result.stdout, 
                                 f"Topic {name} has incorrect partition count. Expected {expected_partitions}.")

if __name__ == "__main__":
    unittest.main()
