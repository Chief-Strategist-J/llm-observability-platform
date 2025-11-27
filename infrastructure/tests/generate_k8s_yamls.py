#!/usr/bin/env python3

import os
from pathlib import Path

K8S_DIR = Path(__file__).parent.parent / "orchestrator" / "config" / "kubernete"

SERVICES = {
    "mongodb": {
        "image": "mongo:8.0",
        "port": 27017,
        "memory_limit": "1Gi",
        "memory_request": "512Mi",
        "cpu_limit": "1",
        "cpu_request": "500m",
        "env": [
            {"name": "MONGO_INITDB_ROOT_USERNAME", "value": "admin"},
            {"name": "MONGO_INITDB_ROOT_PASSWORD", "value": "MongoPassword123!"},
            {"name": "MONGO_INITDB_DATABASE", "value": "admin"},
        ],
        "command": ["mongod", "--auth", "--bind_ip_all", "--wiredTigerCacheSizeGB", "0.5"],
        "healthcheck": {
            "command": ["mongosh", "--quiet", "--port", "27017", "--eval", "db.adminCommand('ping')", "--username", "admin", "--password", "MongoPassword123!", "--authenticationDatabase", "admin"],
            "initial_delay": 40,
            "period": 30
        },
        "volume": True
    },
    "grafana": {
        "image": "grafana/grafana:latest",
        "port": 3000,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [
            {"name": "GF_SECURITY_ADMIN_USER", "value": "admin"},
            {"name": "GF_SECURITY_ADMIN_PASSWORD", "value": "SuperSecret123!"},
            {"name": "GF_USERS_ALLOW_SIGN_UP", "value": "false"},
            {"name": "GF_SERVER_HTTP_PORT", "value": "3000"},
        ],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"],
            "initial_delay": 20,
            "period": 30
        },
        "volume": True
    },
    "prometheus": {
        "image": "prom/prometheus:latest",
        "port": 9090,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "command": [
            "--config.file=/etc/prometheus/prometheus.yml",
            "--storage.tsdb.path=/prometheus",
            "--web.console.libraries=/usr/share/prometheus/console_libraries",
            "--web.console.templates=/usr/share/prometheus/consoles"
        ],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"],
            "initial_delay": 30,
            "period": 30
        },
        "volume": True
    },
    "loki": {
        "image": "grafana/loki:latest",
        "port": 3100,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "command": ["-config.file=/etc/loki/local-config.yaml"],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3100/ready"],
            "initial_delay": 30,
            "period": 30
        },
        "volume": True
    },
    "tempo": {
        "image": "grafana/tempo:latest",
        "port": 3200,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "command": ["-config.file=/etc/tempo.yaml"],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3200/ready"],
            "initial_delay": 30,
            "period": 30
        },
        "volume": True
    },
    "jaeger": {
        "image": "jaegertracing/all-in-one:latest",
        "port": 16686,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:14269"],
            "initial_delay": 30,
            "period": 30
        },
        "volume": False
    },
    "alertmanager": {
        "image": "prom/alertmanager:latest",
        "port": 9093,
        "memory_limit": "128Mi",
        "memory_request": "64Mi",
        "cpu_limit": "300m",
        "cpu_request": "150m",
        "env": [],
        "command": [
            "--config.file=/etc/alertmanager/alertmanager_config.yaml",
            "--storage.path=/alertmanager"
        ],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9093/-/healthy"],
            "initial_delay": 40,
            "period": 30
        },
        "volume": True
    },
    "kafka": {
        "image": "apache/kafka:4.1.1",
        "port": 9092,
        "memory_limit": "1Gi",
        "memory_request": "512Mi",
        "cpu_limit": "1",
        "cpu_request": "500m",
        "env": [
            {"name": "KAFKA_PROCESS_ROLES", "value": "broker,controller"},
            {"name": "CLUSTER_ID", "value": "MkU3OEVBNTcwNTJENDM2Qk"},
        ],
        "healthcheck": {
            "command": ["/opt/kafka/bin/kafka-broker-api-versions.sh", "--bootstrap-server", "localhost:9092"],
            "initial_delay": 60,
            "period": 30
        },
        "volume": True
    },
    "qdrant": {
        "image": "qdrant/qdrant:latest",
        "port": 6333,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:6333/healthz"],
            "initial_delay": 20,
            "period": 30
        },
        "volume": True
    },
    "neo4j": {
        "image": "neo4j:latest",
        "port": 7474,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [
            {"name": "NEO4J_AUTH", "value": "neo4j/password"}
        ],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:7474"],
            "initial_delay": 40,
            "period": 30
        },
        "volume": True
    },
    "mongoexpress": {
        "image": "mongo-express:latest",
        "port": 8081,
        "memory_limit": "256Mi",
        "memory_request": "128Mi",
        "cpu_limit": "300m",
        "cpu_request": "150m",
        "env": [
            {"name": "ME_CONFIG_MONGODB_ADMINUSERNAME", "value": "admin"},
            {"name": "ME_CONFIG_MONGODB_ADMINPASSWORD", "value": "MongoPassword123!"},
        ],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8081"],
            "initial_delay": 20,
            "period": 30
        },
        "volume": False
    },
    "promtail": {
        "image": "grafana/promtail:latest",
        "port": 9080,
        "memory_limit": "256Mi",
        "memory_request": "128Mi",
        "cpu_limit": "300m",
        "cpu_request": "150m",
        "env": [],
        "command": ["-config.file=/etc/promtail/config.yml"],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9080/ready"],
            "initial_delay": 20,
            "period": 30
        },
        "volume": False
    },
    "otel-collector": {
        "image": "otel/opentelemetry-collector:latest",
        "port": 4318,
        "memory_limit": "512Mi",
        "memory_request": "256Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "command": ["--config=/etc/otel-collector-config.yaml"],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:13133"],
            "initial_delay": 20,
            "period": 30
        },
        "volume": False
    },
    "traefik": {
        "image": "traefik:v3.5",
        "port": 80,
        "memory_limit": "256Mi",
        "memory_request": "128Mi",
        "cpu_limit": "500m",
        "cpu_request": "250m",
        "env": [],
        "command": [
            "--providers.docker=true",
            "--api.dashboard=true",
            "--api.insecure=true",
            "--entrypoints.web.address=:80"
        ],
        "healthcheck": {
            "command": ["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80/api/overview"],
            "initial_delay": 20,
            "period": 30
        },
        "volume": False
    },
}

def generate_deployment(name, config):
    port = config["port"]
    env_vars = "\n".join([f"        - name: {e['name']}\n          value: \"{e['value']}\"" for e in config.get("env", [])])
    command =  ""
    if "command" in config:
        cmd_lines = "\n".join([f"        - {c}" for c in config["command"]])
        command = f"\n        command:\n{cmd_lines}"
    
    healthcheck = ""
    if "healthcheck" in config:
        hc = config["healthcheck"]
        cmd_lines = "\n".join([f"            - {c}" for c in hc["command"]])
        healthcheck = f"""
        livenessProbe:
          exec:
            command:
{cmd_lines}
          initialDelaySeconds: {hc['initial_delay']}
          periodSeconds: {hc['period']}
          timeoutSeconds: 10
        readinessProbe:
          exec:
            command:
{cmd_lines}
          initialDelaySeconds: {max(5, hc['initial_delay'] // 2)}
          periodSeconds: 10"""
    
    volume_mount = ""
    volume = ""
    if config.get("volume"):
        volume_mount = f"""
        volumeMounts:
        - name: {name}-data
          mountPath: /data"""
        volume = f"""
      volumes:
      - name: {name}-data
        persistentVolumeClaim:
          claimName: {name}-pvc-${{INSTANCE_ID}}"""
    
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}-${{INSTANCE_ID}}
  labels:
    app: {name}
    instance: "${{INSTANCE_ID}}"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
      instance: "${{INSTANCE_ID}}"
  template:
    metadata:
      labels:
        app: {name}
        instance: "${{INSTANCE_ID}}"
    spec:
      containers:
      - name: {name}
        image: {config['image']}
        ports:
        - containerPort: {port}
          name: {name}{command}
{env_vars}
        resources:
          limits:
            memory: {config['memory_limit']}
            cpu: {config['cpu_limit']}
          requests:
            memory: {config['memory_request']}
            cpu: {config['cpu_request']}{healthcheck}{volume_mount}{volume}
"""

def generate_service(name, config):
    port = config["port"]
    return f"""apiVersion: v1
kind: Service
metadata:
  name: {name}-${{INSTANCE_ID}}
  labels:
    app: {name}
    instance: "${{INSTANCE_ID}}"
spec:
  type: ClusterIP
  ports:
  - port: {port}
    targetPort: {port}
    protocol: TCP
    name: {name}
  selector:
    app: {name}
    instance: "${{INSTANCE_ID}}"
"""

def main():
    print("Generating Kubernetes YAML files...")
    
    for service_name, config in SERVICES.items():
        deployment_file = K8S_DIR / f"{service_name}-dynamic-k8s-deployment.yaml"
        service_file = K8S_DIR / f"{service_name}-dynamic-k8s-service.yaml"
        
        deployment_content = generate_deployment(service_name, config)
        service_content = generate_service(service_name, config)
        
        with open(deployment_file, 'w') as f:
            f.write(deployment_content)
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"  ✓ Created {service_name} deployment and service")
    
    print(f"\n✓ Generated {len(SERVICES)} deployments and {len(SERVICES)} services")

if __name__ == "__main__":
    main()
