# Deployment Guide

## Overview

This guide covers various deployment options for the Distributed Trace Analysis Engine (DTAE), from local development to production Kubernetes deployments.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| Memory | 4 GB | 8+ GB |
| Storage | 10 GB | 50+ GB SSD |
| Network | 100 Mbps | 1 Gbps |

### Software Dependencies

- **Rust**: 1.70+ (2024 edition)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+ (for web UI development)
- **Kubernetes**: 1.24+ (for production deployment)

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/distributed-trace-analysis-engine.git
cd distributed-trace-analysis-engine

# Build the Rust server
cargo build --release

# Start the server
./target/release/dtae-server

# In another terminal, start the web UI
cd web
npm install
npm start
```

### Docker Compose (Full Stack)

```bash
# Start the complete observability stack
docker compose up -d

# Verify all services are running
docker compose ps

# View logs
docker compose logs -f dtae-server
```

Access points:
- **DTAE API**: http://localhost:8090
- **Web UI**: http://localhost:3000
- **Jaeger UI**: http://localhost:16686
- **OTel Collector**: http://localhost:4318 (HTTP), http://localhost:4317 (gRPC)

## Deployment Options

### 1. Standalone Docker Deployment

#### Build Image

```bash
# Build optimized image
docker build -t dtae-server:latest .

# Build with specific tag
docker build -t dtae-server:v1.0.0 .
```

#### Run Container

```bash
# Basic deployment
docker run -d \
  --name dtae-server \
  -p 8090:8090 \
  -e DTAE_BIND_ADDR=0.0.0.0:8090 \
  -e RUST_LOG=info \
  dtae-server:latest

# Production deployment with limits
docker run -d \
  --name dtae-server \
  --restart unless-stopped \
  -p 8090:8090 \
  --memory=4g \
  --cpus=2 \
  -e DTAE_BIND_ADDR=0.0.0.0:8090 \
  -e RUST_LOG=info \
  -v dtae-data:/app/data \
  dtae-server:latest
```

#### Docker Compose (Standalone)

```yaml
version: '3.8'

services:
  dtae-server:
    build: .
    ports:
      - "8090:8090"
    environment:
      - DTAE_BIND_ADDR=0.0.0.0:8090
      - RUST_LOG=info
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
    volumes:
      - dtae-data:/app/data

  dtae-web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8090/api/v1
    depends_on:
      - dtae-server
    restart: unless-stopped

volumes:
  dtae-data:
```

### 2. Kubernetes Deployment

#### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dtae
```

#### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dtae-config
  namespace: dtae
data:
  DTAE_BIND_ADDR: "0.0.0.0:8090"
  RUST_LOG: "info"
  ASSEMBLY_WINDOW_DURATION_NS: "30000000000"
  ASSEMBLY_ORPHAN_TIMEOUT_NS: "60000000000"
  CLUSTERING_MIN_CLUSTER_SIZE: "50"
  CLUSTERING_MIN_SAMPLES: "10"
  LATENCY_SIGMA_MULTIPLIER: "3.0"
```

#### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dtae-server
  namespace: dtae
  labels:
    app: dtae-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dtae-server
  template:
    metadata:
      labels:
        app: dtae-server
    spec:
      containers:
      - name: dtae-server
        image: dtae-server:v1.0.0
        ports:
        - containerPort: 8090
        envFrom:
        - configMapRef:
            name: dtae-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8090
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8090
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: dtae-service
  namespace: dtae
spec:
  selector:
    app: dtae-server
  ports:
  - protocol: TCP
    port: 8090
    targetPort: 8090
  type: ClusterIP
```

#### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dtae-ingress
  namespace: dtae
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: dtae.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dtae-service
            port:
              number: 8090
```

### 3. Helm Chart

#### Chart Structure

```
helm/dtae/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── ingress.yaml
└── charts/
    └── otel-collector/
```

#### values.yaml

```yaml
# Default values for DTAE
replicaCount: 2

image:
  repository: dtae-server
  tag: "v1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8090

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: dtae.example.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 2
    memory: 4Gi
  requests:
    cpu: 1
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

config:
  assembly:
    windowDurationNs: "30000000000"
    orphanTimeoutNs: "60000000000"
  clustering:
    minClusterSize: "50"
    minSamples: "10"
  anomalyDetection:
    latencySigmaMultiplier: "3.0"
    latencyEwmaLambda: "0.99"
```

#### Deploy with Helm

```bash
# Install
helm install dtae ./helm/dtae

# Upgrade
helm upgrade dtae ./helm/dtae

# Uninstall
helm uninstall dtae
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DTAE_BIND_ADDR` | `0.0.0.0:8090` | Server bind address |
| `RUST_LOG` | `info` | Logging level |
| `ASSEMBLY_WINDOW_DURATION_NS` | `30000000000` | Assembly window (30s) |
| `ASSEMBLY_ORPHAN_TIMEOUT_NS` | `60000000000` | Orphan timeout (60s) |
| `CLUSTERING_MIN_CLUSTER_SIZE` | `50` | Minimum cluster size |
| `CLUSTERING_MIN_SAMPLES` | `10` | Core distance samples |
| `LATENCY_SIGMA_MULTIPLIER` | `3.0` | Latency anomaly sensitivity |
| `LATENCY_EWMA_LAMBDA` | `0.99` | Baseline adaptation rate |

### Configuration File

For complex deployments, use a configuration file:

```yaml
# config/dtae.yaml
server:
  bind_addr: "0.0.0.0:8090"
  
assembly:
  window_duration_ns: 30000000000
  orphan_timeout_ns: 60000000000

clustering:
  min_cluster_size: 50
  min_samples: 10
  distance_threshold: 2.0

anomaly_detection:
  latency:
    sigma_multiplier: 3.0
    ewma_lambda: 0.99
  structural:
    window_size: 1000
    alpha: 0.05
  error_propagation:
    enabled: true

storage:
  type: "memory" # or "postgres", "redis"
  
logging:
  level: "info"
  format: "json"
```

## Production Considerations

### 1. High Availability

#### Multi-Region Deployment

```yaml
# Example: Multi-region Kubernetes deployment
apiVersion: v1
kind: Service
metadata:
  name: dtae-service-global
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  selector:
    app: dtae-server
  ports:
  - port: 8090
    targetPort: 8090
```

#### State Management

For production, consider persistent storage:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dtae-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
```

### 2. Monitoring and Observability

#### Prometheus Metrics

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: dtae-metrics
  namespace: dtae
spec:
  selector:
    matchLabels:
      app: dtae-server
  endpoints:
  - port: metrics
    interval: 30s
```

#### Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8090
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8090
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### 3. Security

#### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dtae-network-policy
  namespace: dtae
spec:
  podSelector:
    matchLabels:
      app: dtae-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: otel-collector
    ports:
    - protocol: TCP
      port: 8090
```

#### RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dtae-service-account
  namespace: dtae

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dtae-role
  namespace: dtae
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dtae-role-binding
  namespace: dtae
subjects:
- kind: ServiceAccount
  name: dtae-service-account
  namespace: dtae
roleRef:
  kind: Role
  name: dtae-role
  apiGroup: rbac.authorization.k8s.io
```

### 4. Scaling

#### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dtae-hpa
  namespace: dtae
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dtae-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Vertical Pod Autoscaler

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: dtae-vpa
  namespace: dtae
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dtae-server
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: dtae-server
      maxAllowed:
        cpu: 4
        memory: 8Gi
      minAllowed:
        cpu: 0.5
        memory: 1Gi
```

## Integration with Observability Stack

### OpenTelemetry Collector Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:

exporters:
  # Send to DTAE for analysis
  http:
    endpoint: http://dtae-service:8090/api/v1/spans/otlp
    headers:
      Content-Type: application/json
  
  # Send to Tempo for storage
  otlphttp:
    endpoint: http://tempo:3200
  
  # Send to Jaeger for visualization
  otlp:
    endpoint: jaeger-collector:4317

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [http, otlphttp, otlp]
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "DTAE Overview",
    "panels": [
      {
        "title": "Traces Processed",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dtae_traces_processed_total[5m])"
          }
        ]
      },
      {
        "title": "Anomaly Detection Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dtae_anomalies_detected_total[5m])"
          }
        ]
      },
      {
        "title": "Cluster Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "dtae_cluster_size"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms**: Container OOM kills, high memory consumption

**Solutions**:
- Reduce assembly window duration
- Decrease clustering min_cluster_size
- Implement trace sampling
- Add more memory resources

#### 2. Slow Processing

**Symptoms**: High latency in trace analysis

**Solutions**:
- Increase CPU allocation
- Optimize feature extraction
- Use more efficient clustering algorithms
- Implement parallel processing

#### 3. Connection Issues

**Symptoms**: Failed connections from collectors

**Solutions**:
- Check network policies
- Verify service endpoints
- Ensure proper port configuration
- Check firewall rules

### Debug Commands

```bash
# Check pod status
kubectl get pods -n dtae

# View logs
kubectl logs -f deployment/dtae-server -n dtae

# Check resource usage
kubectl top pods -n dtae

# Debug connectivity
kubectl exec -it deployment/dtae-server -n dtae -- curl localhost:8090/health

# Check events
kubectl get events -n dtae --sort-by='.lastTimestamp'
```

## Performance Tuning

### Memory Optimization

```yaml
# Environment variables for memory tuning
environment:
  - TOKIO_WORKER_THREADS=4
  - RAYON_NUM_THREADS=4
  - MALLOC_CONF=dirty_decay_ms:1000,muzzy_decay_ms:1000
```

### CPU Optimization

```yaml
# CPU pinning for high-performance deployments
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: dtae-server
    resources:
      requests:
        cpu: "2"
      limits:
        cpu: "4"
    env:
    - name: RAYON_NUM_THREADS
      value: "4"
```

### Network Optimization

```yaml
# Tune network parameters
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: dtae-server
    env:
    - name: TOKIO_NET_WORKER_THREADS
      value: "2"
    - name: AXUM_KEEP_ALIVE
      value: "75"
```

## Backup and Recovery

### Data Backup

```bash
# Export configuration
kubectl get configmap dtae-config -n dtae -o yaml > dtae-config-backup.yaml

# Export deployment
kubectl get deployment dtae-server -n dtae -o yaml > dtae-deployment-backup.yaml
```

### Disaster Recovery

```bash
# Restore from backup
kubectl apply -f dtae-config-backup.yaml
kubectl apply -f dtae-deployment-backup.yaml

# Verify restoration
kubectl rollout status deployment/dtae-server -n dtae
```

## Migration Guide

### Version Upgrades

```bash
# Backup current version
kubectl get deployment dtae-server -n dtae -o yaml > dtae-v1.0.0.yaml

# Upgrade to new version
helm upgrade dtae ./helm/dtae --set image.tag=v1.1.0

# Verify upgrade
kubectl rollout status deployment/dtae-server -n dtae
```

### Configuration Migration

```bash
# Extract current config
kubectl get configmap dtae-config -n dtae -o yaml > current-config.yaml

# Apply new config
kubectl apply -f new-config.yaml

# Restart pods to pick up new config
kubectl rollout restart deployment/dtae-server -n dtae
```
