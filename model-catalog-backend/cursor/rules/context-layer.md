# Project Context Template

## Current Project
- Name: AI Model Benchmarking & Catalog Platform
- Tech Stack: Python (Backend), FastAPI, SQLAlchemy, Pydantic, PostgreSQL, TimescaleDB, Redis, Kubernetes, Argo Workflows, Argo CD, vLLM, TGI, LMDeploy, Prometheus, Grafana, DCGM Exporter
- Architecture: Cloud-Native Microservices/Layered, Kubernetes deployment with separate namespaces (model-catalog, data-storage, gpu-workloads, monitoring, argocd)

## Active Sprint
- Goal: Implementation of performance optimization and recommendation layer (deploy Redis HA, achieve cache hit ratio >80%, implement TOPSIS/Pareto algorithm, integrate TGI and LMDeploy)
- Blockers: Handling Spot Instance interruptions, ensuring P95 API latency under 100ms
- Deadline: [24/10/2025]

## Code Standards
- Style: Type Hints throughout, Pydantic Models for API schemas, detailed Docstrings
- Testing: pytest-asyncio, AsyncMock for external service simulation (DB, Redis, Inference), automated testing pipeline
- Patterns: Repository Pattern (data access abstraction), Protocol-based Interfaces (inference engines), Dependency Injection (flexibility and testability)

## Known Constraints
- Performance: UI filtering <500ms, P95 API latency <100ms, 1,000-2,000 queries/hour throughput, batch processing for benchmarks (hours/days for 9,000+ configs per model)
- Browser support: Chrome/Firefox/Safari last 2 versions
- Budget: Spot Instances required for GPU (60-90% cost savings), $3,000-$6,500/month total including GPU Spot
- Compliance: NetworkPolicy and Pod Security Standards for isolation, External Secrets Operator for credential management

## Team Knowledge
- Strong in: Python (Backend), Kubernetes, Docker, Argo CD (GitOps), distributed systems, automation
- Learning: Go (infrastructure tooling), Argo Workflows, OpenTelemetry/Jaeger (Distributed Tracing)
- Avoid: GPU sharing/MIG for benchmarking (consistency), real-time data processing (batch mode only)
```