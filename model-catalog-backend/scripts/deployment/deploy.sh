#!/bin/bash

# Deployment script for Model Catalog Backend

set -e

echo "🚀 Starting deployment..."

# Configuration
APP_NAME="model-catalog-backend"
DOCKER_IMAGE="model-catalog-backend:latest"
KUBERNETES_NAMESPACE="model-catalog"

# Check if required tools are installed
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed. Aborting." >&2; exit 1; }

# Build Docker image
echo "🔄 Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Tag image for registry (update with your registry)
# docker tag $DOCKER_IMAGE your-registry.com/$DOCKER_IMAGE
# docker push your-registry.com/$DOCKER_IMAGE

# Apply Kubernetes configurations
echo "🔄 Applying Kubernetes configurations..."
kubectl apply -f configs/kubernetes/namespace.yaml
kubectl apply -f configs/kubernetes/configmap.yaml
kubectl apply -f configs/kubernetes/secret.yaml
kubectl apply -f configs/kubernetes/deployment.yaml
kubectl apply -f configs/kubernetes/service.yaml
kubectl apply -f configs/kubernetes/ingress.yaml

# Wait for deployment to be ready
echo "🔄 Waiting for deployment to be ready..."
kubectl rollout status deployment/$APP_NAME -n $KUBERNETES_NAMESPACE

# Get service URL
echo "🔄 Getting service URL..."
SERVICE_URL=$(kubectl get service $APP_NAME -n $KUBERNETES_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(kubectl get service $APP_NAME -n $KUBERNETES_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

echo "🎉 Deployment completed successfully!"
echo "📡 Service URL: http://$SERVICE_URL"
echo "📚 API Documentation: http://$SERVICE_URL/docs"
