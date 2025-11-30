# Kubernetes Infrastructure Setup

## Prerequisites

Before deploying services to Kubernetes, ensure you have the following installed:

### Required Tools

1. **kubectl** - Kubernetes command-line tool
   ```bash
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   kubectl version --client
   ```

2. **Kubernetes Cluster** - One of:
   - **Minikube** (Local development)
     ```bash
     curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
     sudo install minikube-linux-amd64 /usr/local/bin/minikube
     minikube start
     ```
   - **Kind** (Kubernetes in Docker)
     ```bash
     curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
     chmod +x ./kind
     sudo mv ./kind /usr/local/bin/kind
     kind create cluster
     ```
   - **K3s** (Lightweight production)
   - **EKS/GKE/AKS** (Cloud platforms)

3. **Python Dependencies**
   ```bash
   pip install -r infrastructure/requirements-k8s.txt
   ```

### Traefik CRD Installation

Install Traefik Custom Resource Definitions before deploying services:

```bash
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.5/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
```

Or use the bundled CRDs (included in this repo).

## Installation Steps

### 1. Install Traefik with RBAC

```bash
cd infrastructure/orchestrator/config/kubernete

kubectl apply -f traefik-rbac.yaml
kubectl apply -f traefik-dynamic-k8s-deployment.yaml
kubectl apply -f traefik-dynamic-k8s-service.yaml
```

### 2. Install Middleware

```bash
kubectl apply -f ingress/traefik-middleware.yaml
```

### 3. Deploy Services

Deploy any service with its deployment, service, and optional ingress:

```bash
kubectl apply -f grafana-dynamic-k8s-deployment.yaml
kubectl apply -f grafana-dynamic-k8s-service.yaml
kubectl apply -f ingress/grafana-ingress.yaml
```

### 4. Optional: Configure HPA

For autoscaling services:

```bash
kubectl apply -f hpa/grafana-hpa.yaml
```

### 5. Optional: ConfigMaps and Secrets

```bash
kubectl apply -f configmaps/grafana-configmap.yaml
```

## Environment Variables

Set required environment variables before deployment:

```bash
export INSTANCE_ID=0
export NAMESPACE=default
export GRAFANA_ADMIN_USER=admin
export GRAFANA_ADMIN_PASSWORD=SuperSecret123!
export GRAFANA_MEMORY_LIMIT=512Mi
export GRAFANA_CPU_LIMIT=0.5
export GRAFANA_MEMORY_RESERVATION=256Mi
```

Or use an `.env` file (rendered automatically by BaseKubernetesActivity).

## Verification

### Check Pod Status

```bash
kubectl get pods -n default -l instance=0
kubectl describe pod -n default -l app=grafana,instance=0
```

### Check IngressRoutes

```bash
kubectl get ingressroutes -n default
kubectl describe ingressroute grafana-0
```

### Access Services

1. **Port Forward** (for local access):
   ```bash
   kubectl port-forward -n default svc/grafana-0 3000:3000
   ```

2. **LoadBalancer** (if Traefik service is LoadBalancer type):
   - Get external IP: `kubectl get svc traefik-0`
   - Access via browser: `http://<EXTERNAL-IP>` with Host header set

3. **Ingress** (with proper DNS/hosts file):
   ```bash
   echo "127.0.0.1 grafana-0.localhost" | sudo tee -a /etc/hosts
   ```

## Testing

Run the comprehensive test suite:

```bash
cd infrastructure
pytest tests/units/kubernetes_tests/ -v

pytest tests/units/kubernetes_tests/ -m integration -v
```

## Switching from Docker to Kubernetes

To switch an activity from Docker to Kubernetes, change the manager:

```python
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager

GRAFANA_DEPLOYMENT = Path(__file__).parent.parent.parent / "config" / "kubernete" / "grafana-dynamic-k8s-deployment.yaml"
GRAFANA_SERVICE = Path(__file__).parent.parent.parent / "config" / "kubernete" / "grafana-dynamic-k8s-service.yaml"

@activity.defn(name="start_grafana_k8s_activity")
async def start_grafana_k8s_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    
    manager = YAMLKubernetesManager(
        yaml_paths=[str(GRAFANA_DEPLOYMENT), str(GRAFANA_SERVICE)],
        instance_id=instance_id,
        namespace="default"
    )
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "grafana",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }
```

The interface is identical to `YAMLContainerManager`!

## Troubleshooting

### Pods Not Starting

```bash
kubectl logs -n default -l app=grafana,instance=0
kubectl describe pod -n default -l app=grafana,instance=0
```

### IngressRoute Not Working

```bash
kubectl logs -n default -l app=traefik
kubectl describe ingressroute grafana-0
```

### Permission Errors

Ensure RBAC is properly configured:

```bash
kubectl get serviceaccount traefik-0
kubectl get clusterrole traefik-0
kubectl get clusterrolebinding traefik-0
```
