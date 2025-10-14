# LLM Benchmarking Platform - Model Catalog Backend

A comprehensive Python backend service for large-scale AI model performance testing and cataloging. This platform performs thousands of test combinations across different hardware configurations to create an accurate and up-to-date model catalog with 9,000+ configurations per model.

## Project Objectives

The LLM Benchmarking Platform addresses the central challenge of handling thousands of different test configurations to provide:

- **Large-scale Performance Testing**: Comprehensive benchmarking across multiple dimensions
- **Accurate Model Catalog**: Up-to-date performance data for informed decision making
- **Cost Optimization**: 60-90% savings through spot instance utilization
- **Multi-Criteria Optimization**: TOPSIS and Pareto algorithms for model selection
- **Real-time Recommendations**: Sub-100ms API responses with intelligent caching

## Project Structure

```
model-catalog-backend/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routes/
│   │   │   └── responses/
│   │   ├── middleware/
│   │   └── dependencies/
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── schemas/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── scripts/
│   ├── db/
│   └── deployment/
└── configs/
    ├── kubernetes/
    ├── helm/
    └── docker/
```

## Benchmarking Complexity and Test Matrix

The platform handles a complex test matrix with 9,000+ combinations per model across multiple dimensions:

### Test Matrix Dimensions

| Dimension | Examples | Description |
|-----------|----------|-------------|
| **Models & Versions** | GPT-4, Claude, Llama 3.1 | Different versions of language models |
| **Hardware Configs** | L4, A100-80GB, H100 | GPU types and counts (1, 2, 4, 8) |
| **Frameworks** | vLLM, TGI, LMDeploy | Different inference engines |
| **Quantization** | FP16, INT8, INT4 | Numerical precision levels |
| **Workload Patterns** | Concurrent requests, Batch sizes | Different usage scenarios |

### Key Features

- **Large-Scale Testing**: 9,000+ test combinations per model
- **Multi-Framework Support**: vLLM, TGI, LMDeploy inference engines
- **Hardware Diversity**: L4, A100-80GB, H100 GPU configurations
- **Quantization Support**: FP16, INT8, INT4 precision levels
- **Spot Instance Optimization**: 60-90% cost savings
- **Real-time Recommendations**: Sub-100ms API responses
- **Comprehensive Metrics**: TTFT, TPOT, throughput, accuracy tracking
- **Automated Pipeline**: Argo Workflows with checkpoint/resume
- **Monitoring**: Prometheus/Grafana with DCGM GPU metrics

## Quick Start

### Prerequisites

- **Python 3.8+** - Backend development
- **PostgreSQL** - Primary transactional database
- **TimescaleDB** - Time-series benchmark data
- **Redis** - High-performance caching layer
- **Kubernetes** - Container orchestration
- **GPU Support** - NVIDIA GPU Operator for GPU workloads
- **Argo Workflows** - Pipeline automation
- **Docker** - Containerization (optional for local development)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd model-catalog-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .[dev]
```

4. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Using Docker

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

This will start both the application and PostgreSQL database.

## Automation Infrastructure and Workflow

The benchmarking process is managed using Argo Workflows in a Kubernetes environment with full automation of all process stages.

### Main Pipeline Stages

1. **Trigger and Model Validation** - Process initiation and model availability check. If needed, retrieval from HuggingFace and metadata validation
2. **Matrix Generation** - Building the complete test matrix of 9,000+ configurations
3. **Splitting and Parallel Execution** - Division into batches (typically 100 configurations per batch) with parallel execution
4. **GPU Resource Allocation** - Dedicated allocation of full GPU to each job (no resource sharing)
5. **Benchmark Execution** - Model loading, inference engine initialization, warmup runs, and execution of 100-500 actual requests
6. **Results Collection** - Measurement and storage of metrics in TimescaleDB for later analysis

### Infrastructure Characteristics

The infrastructure is built on a Kubernetes cluster with GPU scheduling support:

- **NVIDIA GPU Operator** - GPU resource management and exposure to pods
- **Device Plugin** - Enables GPU access for workloads
- **Spot Instance Management** - 60-90% cost savings with automatic recovery
- **Checkpoint/Resume** - Fault tolerance for spot instance interruptions
- **Monitoring Stack** - Prometheus, Grafana, and DCGM exporter for comprehensive observability

## Development

### Code Quality

The project uses several tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

Run all quality checks:
```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

### Testing

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Documentation

### API Documentation
Once the application is running, you can access:

- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

### System Architecture
Comprehensive system documentation:

- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Complete project overview and objectives
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)** - High-level system design and request flows
- **[Infrastructure](docs/INFRASTRUCTURE.md)** - Kubernetes deployment and infrastructure details
- **[Database Architecture](docs/DATABASE.md)** - Database schema, ERD, and data flow
- **[Pipeline Architecture](docs/PIPELINES.md)** - Argo Workflows and benchmarking pipelines
- **[Architecture Diagrams](docs/diagrams/)** - Visual system diagrams in Mermaid format
  - [System Overview](docs/diagrams/system-overview.md) - High-level architecture
  - [Recommendation Flow](docs/diagrams/recommendation-flow.md) - Detailed recommendation request flow
  - [Benchmarking Pipeline](docs/diagrams/benchmarking-pipeline.md) - Argo Workflows pipeline
  - [Kubernetes Deployment](docs/diagrams/kubernetes-deployment.md) - Complete cluster architecture

## Architecture

This project follows clean architecture principles with clear separation of concerns:

- **API Layer** (`src/api/`) - Handles HTTP requests and responses
- **Core Layer** (`src/core/`) - Business logic and configuration
- **Models Layer** (`src/models/`) - Database models and ORM definitions
- **Repositories Layer** (`src/repositories/`) - Data access abstraction
- **Services Layer** (`src/services/`) - Business logic implementation
- **Schemas Layer** (`src/schemas/`) - Request/response validation

### Key Features

- **Performance Optimized**: P95 API latency <100ms, Redis cache hit ratio >80%
- **Spot Instance Ready**: Built-in checkpoint/resume for 60-90% cost savings
- **Multi-Criteria Optimization**: TOPSIS and Pareto algorithms for model selection
- **Kubernetes Native**: Full K8s deployment with namespace isolation
- **Observability**: Prometheus/Grafana monitoring with distributed tracing
- **Large-Scale Testing**: 9,000+ configurations per model across multiple dimensions
- **Multi-Framework Support**: vLLM, TGI, LMDeploy inference engines
- **Comprehensive Metrics**: TTFT, TPOT, throughput, accuracy, GPU utilization tracking
- **Automated Pipeline**: Argo Workflows with full automation and fault tolerance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
