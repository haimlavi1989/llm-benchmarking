# Infrastructure Architecture

## Kubernetes Deployment Architecture

### Complete Cluster Architecture

For the detailed Kubernetes deployment architecture with all components, resource allocations, and network flows, see: **[Kubernetes Deployment Diagram](diagrams/kubernetes-deployment.md)**

### Namespace Structure

```mermaid
graph TB
    subgraph "model-catalog namespace"
        API[Model Catalog API]
        Auth[Authentication Service]
        Cache[Redis Cache]
        HPA[Horizontal Pod Autoscaler]
    end
    
    subgraph "data-storage namespace"
        PG[(PostgreSQL Primary + Replicas)]
        TS[(TimescaleDB)]
        Backup[Backup Jobs]
        PVC[Persistent Volumes]
    end
    
    subgraph "gpu-workloads namespace"
        TGI[TGI Inference]
        LMDeploy[LMDeploy]
        vLLM[vLLM]
        Benchmark[Benchmark Jobs]
        SpotHandler[Spot Termination Handler]
    end
    
    subgraph "monitoring namespace"
        Prometheus[Prometheus]
        Grafana[Grafana]
        Jaeger[Jaeger]
        DCGM[DCGM Exporter]
        AlertManager[Alert Manager]
    end
    
    subgraph "argocd namespace"
        ArgoCD[Argo CD]
        ArgoWF[Argo Workflows]
        ArgoEvents[Argo Events]
        GitRepo[Git Repository]
    end
    
    subgraph "gpu-operator namespace"
        GPUOp[NVIDIA GPU Operator]
        DevicePlugin[Device Plugin]
    end
    
    API --> PG
    API --> TS
    API --> Cache
    HPA -.-> API
    Benchmark --> TGI
    Benchmark --> LMDeploy
    Benchmark --> vLLM
    SpotHandler -.-> Benchmark
    Prometheus --> DCGM
    ArgoWF --> Benchmark
    GPUOp --> DevicePlugin
```

### Resource Allocation

```mermaid
graph LR
    subgraph "CPU Nodes"
        CPU1[CPU Node 1]
        CPU2[CPU Node 2]
        CPU3[CPU Node 3]
    end
    
    subgraph "GPU Nodes"
        GPU1[GPU Node 1<br/>A100 80GB]
        GPU2[GPU Node 2<br/>A100 80GB]
        GPU3[GPU Node 3<br/>H100 80GB]
    end
    
    subgraph "Spot Instances"
        Spot1[Spot GPU 1]
        Spot2[Spot GPU 2]
        Spot3[Spot GPU 3]
    end
    
    CPU1 --> API
    CPU2 --> Cache
    CPU3 --> DB
    GPU1 --> TGI
    GPU2 --> vLLM
    GPU3 --> LMDeploy
    Spot1 --> Benchmark
    Spot2 --> Benchmark
    Spot3 --> Benchmark
```

## Service Mesh Architecture

### Istio Configuration

```yaml
# Traffic Management
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: model-catalog
spec:
  hosts:
  - model-catalog
  http:
  - match:
    - uri:
        prefix: /api/v1/models
    route:
    - destination:
        host: model-catalog
        subset: v1
    fault:
      delay:
        percentage:
          value: 0.1
        fixedDelay: 5s
  - match:
    - uri:
        prefix: /api/v1/benchmarks
    route:
    - destination:
        host: model-catalog
        subset: v2
```

### Circuit Breaker Pattern

```mermaid
graph TB
    subgraph "Circuit Breaker States"
        Closed[Closed<br/>Normal Operation]
        Open[Open<br/>Fail Fast]
        HalfOpen[Half-Open<br/>Test Requests]
    end
    
    Closed -->|Failure Threshold| Open
    Open -->|Timeout| HalfOpen
    HalfOpen -->|Success| Closed
    HalfOpen -->|Failure| Open
```

## Spot Instance Management

### Interruption Handling

```mermaid
sequenceDiagram
    participant K8s as Kubernetes
    participant Node as GPU Node
    participant Handler as Termination Handler
    participant Argo as Argo Workflows
    participant Checkpoint as Checkpoint Store
    
    Node->>Handler: Interruption Warning (2 min)
    Handler->>Argo: Pause Workflows
    Handler->>Checkpoint: Save State
    Handler->>K8s: Drain Node
    Node->>Handler: Node Terminated
    
    Note over Argo: Later Resume
    Argo->>Checkpoint: Restore State
    Argo->>K8s: Resume on New Node
    K8s->>Argo: Continue Workflow
```

### Fault Tolerance Strategy

- **Preemption Detection**: AWS/GCP interruption warnings
- **Graceful Shutdown**: 2-minute warning window
- **State Persistence**: Checkpoint critical data
- **Automatic Recovery**: Resume on new spot instances
- **Cost Optimization**: 60-90% savings with minimal disruption

## Monitoring & Observability

### Prometheus Metrics

```yaml
# Custom Metrics
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: model-catalog-metrics
spec:
  selector:
    matchLabels:
      app: model-catalog-backend
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Grafana Dashboards

- **API Performance**: Response times, error rates, throughput
- **GPU Utilization**: Memory usage, compute utilization
- **Cache Performance**: Hit ratio, eviction rates
- **Cost Tracking**: Spot instance savings, resource costs

## Network Policies

### Micro-segmentation

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: model-catalog-netpol
spec:
  podSelector:
    matchLabels:
      app: model-catalog-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: data-storage
    ports:
    - protocol: TCP
      port: 5432
```

## Disaster Recovery

### Backup Strategy

- **Database Backups**: Daily automated backups to S3
- **Configuration Backups**: GitOps with ArgoCD
- **State Backups**: Checkpoint data in persistent storage
- **Recovery Time**: < 4 hours for full system recovery
- **Recovery Point**: < 1 hour data loss maximum
