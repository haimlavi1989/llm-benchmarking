# Kubernetes & Helm Deployment Configuration

Configuration files for deploying the Model Catalog API to Kubernetes.

## 📁 Structure

```
configs/
├── kubernetes/          # Raw Kubernetes manifests
│   ├── 01-namespace.yaml
│   ├── 02-configmap.yaml
│   ├── 03-secrets.yaml
│   ├── 04-deployment.yaml
│   ├── 05-service.yaml
│   └── 06-ingress.yaml
│
└── helm/               # Helm chart
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        ├── configmap.yaml
        ├── secret.yaml
        ├── serviceaccount.yaml
        └── hpa.yaml
```

---

## 🚀 Quick Start

### Option 1: Using kubectl (Raw Manifests)

```bash
# Apply in order
kubectl apply -f configs/kubernetes/01-namespace.yaml
kubectl apply -f configs/kubernetes/02-configmap.yaml
kubectl apply -f configs/kubernetes/03-secrets.yaml
kubectl apply -f configs/kubernetes/04-deployment.yaml
kubectl apply -f configs/kubernetes/05-service.yaml
kubectl apply -f configs/kubernetes/06-ingress.yaml

# Or apply all at once
kubectl apply -f configs/kubernetes/ --recursive
```

### Option 2: Using Helm (Recommended)

```bash
# Install chart
helm install model-catalog ./configs/helm

# Or with custom values
helm install model-catalog ./configs/helm \
  --set image.tag=v1.0.0 \
  --set replicaCount=5

# Upgrade
helm upgrade model-catalog ./configs/helm

# Uninstall
helm uninstall model-catalog
```

---

## 🔧 Configuration

### Environment Variables

Set in `02-configmap.yaml` or Helm `values.yaml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | Model Catalog Backend |
| `DEBUG` | Debug mode | false |
| `DATABASE_HOST` | PostgreSQL host | postgresql.data-storage.svc.cluster.local |
| `DATABASE_PORT` | PostgreSQL port | 5432 |
| `DATABASE_NAME` | Database name | model_catalog |
| `REDIS_HOST` | Redis host | redis.model-catalog.svc.cluster.local |
| `WORKERS` | Number of workers | 4 |
| `LOG_LEVEL` | Logging level | info |

### Secrets

⚠️ **IMPORTANT**: Change default values in production!

Set in `03-secrets.yaml` or Helm `values.yaml`:

```yaml
secrets:
  databaseUser: "model_catalog_user"
  databasePassword: "CHANGE_ME_IN_PRODUCTION"
  secretKey: "CHANGE_ME_IN_PRODUCTION_USE_STRONG_KEY"
  redisPassword: "CHANGE_ME_IN_PRODUCTION"
```

**Production Recommendation**: Use [External Secrets Operator](https://external-secrets.io/)

---

## 📊 Resource Requirements

### Per Pod

- **Requests**: 1 CPU, 2Gi RAM
- **Limits**: 2 CPU, 4Gi RAM

### Cluster Total (3 replicas)

- **CPU**: 3-6 cores
- **Memory**: 6-12 GB
- **Storage**: Minimal (stateless app)

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 75
  targetMemoryUtilizationPercentage: 80
```

---

## 🏥 Health Checks

### Liveness Probe
```yaml
httpGet:
  path: /api/v1/health
  port: 8000
initialDelaySeconds: 30
periodSeconds: 10
timeoutSeconds: 5
failureThreshold: 3
```

### Readiness Probe
```yaml
httpGet:
  path: /api/v1/health
  port: 8000
initialDelaySeconds: 10
periodSeconds: 5
timeoutSeconds: 3
failureThreshold: 3
```

### Startup Probe
```yaml
httpGet:
  path: /api/v1/health
  port: 8000
periodSeconds: 10
failureThreshold: 30  # 5 minute startup window
```

---

## 🔐 Security

### Pod Security

- ✅ Non-root user (UID 1000)
- ✅ Read-only root filesystem
- ✅ No privilege escalation
- ✅ Drop all capabilities

### Network Security

- ✅ NetworkPolicy (default deny)
- ✅ TLS/SSL encryption
- ✅ Rate limiting (100 RPS)
- ✅ Connection limits (50 concurrent)

---

## 🌐 Ingress

### Configuration

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.model-catalog.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: model-catalog-tls
      hosts:
        - api.model-catalog.example.com
```

### Annotations

- SSL redirect
- Rate limiting: 100 RPS
- Connection limit: 50
- Auto TLS with cert-manager

---

## 📈 Monitoring

### Prometheus Metrics

Annotations added to pods:

```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8000"
prometheus.io/path: "/metrics"
```

### Grafana Dashboards

Import dashboard templates from `../docs/monitoring/`

---

## 🔄 Deployment Strategies

### Rolling Update (Default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### Blue/Green Deployment

```bash
# Deploy new version
helm install model-catalog-green ./configs/helm \
  --set image.tag=v2.0.0

# Switch traffic
kubectl patch service model-catalog-api \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Cleanup old version
helm uninstall model-catalog-blue
```

---

## 🛠️ Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n model-catalog
kubectl describe pod <pod-name> -n model-catalog
kubectl logs <pod-name> -n model-catalog
```

### Check Resources

```bash
kubectl top pods -n model-catalog
kubectl top nodes
```

### Debug Container

```bash
kubectl exec -it <pod-name> -n model-catalog -- /bin/sh
```

### Check Configuration

```bash
kubectl get configmap model-catalog-config -n model-catalog -o yaml
kubectl get secret model-catalog-secrets -n model-catalog -o yaml
```

---

## 📝 Common Operations

### Scale Deployment

```bash
kubectl scale deployment model-catalog-api -n model-catalog --replicas=5
```

### Update Image

```bash
kubectl set image deployment/model-catalog-api \
  api=model-catalog-api:v1.0.1 \
  -n model-catalog
```

### Rollback Deployment

```bash
kubectl rollout undo deployment/model-catalog-api -n model-catalog
```

### View Rollout History

```bash
kubectl rollout history deployment/model-catalog-api -n model-catalog
```

---

## 🔗 Related Documentation

- [API Documentation](../docs/API.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Infrastructure](../docs/INFRASTRUCTURE.md)
- [Kubernetes Deployment Diagram](../docs/diagrams/kubernetes-deployment.md)

---

## ⚙️ Helm Values Override Examples

### Development

```yaml
# values-dev.yaml
replicaCount: 1
config:
  debug: "true"
  logLevel: "debug"
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi
autoscaling:
  enabled: false
```

```bash
helm install model-catalog ./configs/helm -f values-dev.yaml
```

### Production

```yaml
# values-prod.yaml
replicaCount: 5
config:
  debug: "false"
  logLevel: "warning"
resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    cpu: 4000m
    memory: 8Gi
autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
```

```bash
helm install model-catalog ./configs/helm -f values-prod.yaml
```

---

## 📦 Building Docker Image

```bash
# Build image
docker build -t model-catalog-api:latest .

# Tag for registry
docker tag model-catalog-api:latest \
  your-registry.com/model-catalog-api:v1.0.0

# Push to registry
docker push your-registry.com/model-catalog-api:v1.0.0
```

---

## ✅ Validation

### Lint Helm Chart

```bash
helm lint ./configs/helm
```

### Dry Run

```bash
helm install model-catalog ./configs/helm --dry-run --debug
```

### Validate Kubernetes Manifests

```bash
kubectl apply --dry-run=client -f configs/kubernetes/
```

---

**🚀 Ready for deployment!**

