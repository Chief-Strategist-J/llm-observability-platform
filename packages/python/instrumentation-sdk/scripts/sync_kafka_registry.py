import yaml
import subprocess
import sys
import os

def run_command(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)
    return result.returncode

def main():
    # Paths are relative to the package root
    topics_file = "contracts/registries/topics.yaml"
    bootstrap_server = os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:9094")
    
    if not os.path.exists(topics_file):
        print(f"Error: Registry file not found at {topics_file}")
        sys.exit(1)

    with open(topics_file, 'r') as f:
        config = yaml.safe_load(f)

    print(f"Syncing {len(config['topics'])} topics from registry...")

    for topic in config['topics']:
        name = topic['name']
        partitions = str(topic['partitions'])
        replication = str(topic['replication_factor'])
        
        # Build kafka-topics command
        # We assume this script runs inside a container with kafka-topics installed
        # or we use docker exec if running from host (but here we'll assume container)
        cmd = [
            "kafka-topics",
            "--create",
            "--if-not-exists",
            "--bootstrap-server", bootstrap_server,
            "--topic", name,
            "--partitions", partitions,
            "--replication-factor", replication,
            "--config", f"cleanup.policy={topic.get('cleanup_policy', 'delete')}"
        ]
        
        run_command(cmd)

    print("Kafka registry sync completed.")

if __name__ == "__main__":
    main()
