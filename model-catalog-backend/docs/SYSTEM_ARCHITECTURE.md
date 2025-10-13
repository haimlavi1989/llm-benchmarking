# System Architecture

## High-Level System Design

The LLM Benchmarking Platform is a comprehensive system designed for large-scale AI model performance testing and cataloging. The platform handles thousands of test combinations across different hardware configurations, creating an accurate and up-to-date model catalog with 900+ configurations per model.

The system follows a cloud-native microservices architecture with clear separation of concerns and horizontal scalability, optimized for handling the complex benchmarking matrix across multiple dimensions.

### Core Components

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web UI]
        API_Client[API Clients]
    end
    
    subgraph "API Gateway"
        LB[Load Balancer]
        Ingress[Kubernetes Ingress]
    end
    
    subgraph "Application Layer"
        API[Model Catalog API]
        Auth[Authentication Service]
        Cache[Redis Cache]
    end
    
    subgraph "Business Logic Layer"
        ModelSvc[Model Service]
        BenchmarkSvc[Benchmark Service]
        RecSvc[Recommendation Service]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        TS[(TimescaleDB)]
        Redis[(Redis)]
    end
    
    subgraph "Infrastructure Layer"
        K8s[Kubernetes Cluster]
        GPU[GPU Nodes]
        Spot[Spot Instances]
    end
    
    UI --> LB
    API_Client --> LB
    LB --> Ingress
    Ingress --> API
    API --> Auth
    API --> Cache
    API --> ModelSvc
    API --> BenchmarkSvc
    API --> RecSvc
    ModelSvc --> PG
    BenchmarkSvc --> TS
    RecSvc --> Redis
    K8s --> GPU
    GPU --> Spot
```

## Request Flow Architecture

### Recommendation Request Flow

```mermaid
sequenceDiagram
    participant Client as Client/UI
    participant Gateway as API Gateway
    participant Auth as Auth Middleware
    participant RecommendAPI as /recommend Endpoint
    participant Cache as Redis Cache
    participant ModelService as Model Service
    participant TOPSIS as TOPSIS Algorithm
    participant VRAM as VRAM Calculator
    participant GPU as GPU Matcher
    participant ModelRepo as Model Repository
    participant BenchRepo as Benchmark Repository
    participant DB as PostgreSQL
    participant TimescaleDB as TimescaleDB

    Client->>Gateway: POST /api/v1/recommend
    Note over Client,Gateway: Request: {use_case, constraints, sla}
    
    Gateway->>Auth: Validate Request
    Auth-->>Gateway: ✓ Authorized
    
    Gateway->>RecommendAPI: Forward Request
    
    RecommendAPI->>RecommendAPI: Parse & Validate Input
    Note over RecommendAPI: use_case: "chatbot"<br/>load: {rps: 30, tokens: 512}<br/>sla: {latency_p90: 300ms}
    
    RecommendAPI->>Cache: Check Cache Key
    Note over Cache: Key: recommend:chatbot:30rps:300ms
    
    alt Cache Hit
        Cache-->>RecommendAPI: Return Cached Results
        RecommendAPI-->>Client: 200 OK (50ms)
    else Cache Miss
        Cache-->>RecommendAPI: Cache Miss
        
        RecommendAPI->>ModelService: recommend_models(params)
        
        par Parallel Data Fetching
            ModelService->>ModelRepo: get_models_by_use_case("chatbot")
            ModelRepo->>DB: SELECT * FROM models WHERE...
            DB-->>ModelRepo: Models List
            ModelRepo-->>ModelService: [Model1, Model2, ...]
        and
            ModelService->>BenchRepo: get_benchmarks(model_ids)
            BenchRepo->>TimescaleDB: SELECT * FROM benchmarks WHERE...
            TimescaleDB-->>BenchRepo: Benchmark Results
            BenchRepo-->>ModelService: [Benchmark Data]
        end
        
        ModelService->>ModelService: Merge Models + Benchmarks
        
        par Apply Algorithms
            ModelService->>TOPSIS: calculate_scores(data, weights)
            Note over TOPSIS: Normalize metrics<br/>Apply weights<br/>Calculate distances<br/>Compute scores
            TOPSIS-->>ModelService: Ranked Models
        and
            ModelService->>VRAM: calculate_requirements(models)
            Note over VRAM: Formula: (params × bits/8) × 1.2
            VRAM-->>ModelService: VRAM Requirements
        and
            ModelService->>GPU: match_hardware(vram, constraints)
            Note over GPU: Match to: A100, H100, L4<br/>Consider spot availability
            GPU-->>ModelService: GPU Configurations
        end
        
        ModelService->>ModelService: Filter by SLA Constraints
        Note over ModelService: Filter: latency_p90 <= 300ms<br/>Filter: accuracy >= threshold
        
        ModelService->>ModelService: Sort by Composite Score
        Note over ModelService: Top 10 Results
        
        ModelService-->>RecommendAPI: Recommendation Results
        
        RecommendAPI->>Cache: Store in Cache (TTL: 5min)
        Note over Cache: Key: recommend:chatbot:30rps:300ms<br/>Value: [Results JSON]
        
        RecommendAPI->>RecommendAPI: Format Response
        Note over RecommendAPI: {<br/>  models: [...],<br/>  metadata: {...}<br/>}
        
        RecommendAPI-->>Client: 200 OK (180ms)
    end
    
    Note over Client: Display Model Cards:<br/>- Qwen2.5-7B (4×H100)<br/>- Llama-3.1-8B (4×H100)<br/>- Mistral-7B-v0.3 (2×H100)
```

### General API Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant LB as Load Balancer
    participant API as Model Catalog API
    participant Cache as Redis Cache
    participant DB as PostgreSQL/TimescaleDB
    participant GPU as GPU Workloads
    
    Client->>LB: HTTP Request
    LB->>API: Forward Request
    API->>Cache: Check Cache
    
    alt Cache Hit
        Cache-->>API: Return Cached Data
        API-->>LB: Response (< 100ms)
    else Cache Miss
        API->>DB: Query Database
        DB-->>API: Return Data
        API->>Cache: Store in Cache
        API-->>LB: Response
    end
    
    LB-->>Client: Final Response
    
    Note over API,GPU: For Benchmarking Requests
    API->>GPU: Trigger Benchmark
    GPU-->>API: Benchmark Results
    API->>DB: Store Results
```

### Benchmarking Complexity and Test Matrix

The platform handles a complex test matrix with 900+ combinations per model across multiple dimensions:

### Test Matrix Dimensions

| Dimension | Examples | Description |
|-----------|----------|-------------|
| **Models & Versions** | GPT-4, Claude, Llama 3.1 | Different versions of language models |
| **Hardware Configs** | L4, A100-80GB, H100 | GPU types and counts (1, 2, 4, 8) |
| **Frameworks** | vLLM, TGI, LMDeploy | Different inference engines |
| **Quantization** | FP16, INT8, INT4 | Numerical precision levels |
| **Workload Patterns** | Concurrent requests, Batch sizes | Different usage scenarios |

### Performance Targets

- **P95 API Latency**: < 100ms
- **UI Filtering Response**: < 500ms
- **Cache Hit Ratio**: > 80%
- **Throughput**: 1,000-2,000 queries/hour
- **Batch Processing**: Hours/days for 9,000+ configurations
- **GPU Resource Allocation**: Dedicated full GPU per job (no resource sharing)
- **Spot Instance Utilization**: 60-90% cost savings with automatic recovery

## Security Architecture

### Network Segmentation

```mermaid
graph TB
    subgraph "Public Zone"
        Internet[Internet]
        LB[Load Balancer]
    end
    
    subgraph "DMZ"
        Ingress[Ingress Controller]
    end
    
    subgraph "Application Zone"
        API[API Pods]
        Auth[Auth Service]
    end
    
    subgraph "Data Zone"
        DB[Database Pods]
        Cache[Redis Pods]
    end
    
    subgraph "GPU Zone"
        GPU[GPU Workloads]
        Spot[Spot Instances]
    end
    
    Internet --> LB
    LB --> Ingress
    Ingress --> API
    API --> Auth
    API --> DB
    API --> Cache
    API --> GPU
    GPU --> Spot
```

### Security Controls

- **Pod Security Standards**: Restricted policy enforcement
- **NetworkPolicy**: Default deny-all with explicit allow rules
- **External Secrets Operator**: Credential management
- **Network Isolation**: Separate namespaces for each component
- **TLS Encryption**: All internal and external communications

## Scalability Architecture

### Horizontal Scaling Strategy

```mermaid
graph LR
    subgraph "Auto Scaling"
        HPA[Horizontal Pod Autoscaler]
        VPA[Vertical Pod Autoscaler]
        CA[Cluster Autoscaler]
    end
    
    subgraph "Resource Management"
        Requests[Resource Requests]
        Limits[Resource Limits]
        QoS[Quality of Service]
    end
    
    subgraph "Spot Instance Strategy"
        Spot[Spot Instances]
        Interruption[Interruption Handler]
        Checkpoint[Checkpoint/Resume]
    end
    
    HPA --> Requests
    VPA --> Limits
    CA --> Spot
    Spot --> Interruption
    Interruption --> Checkpoint
```

### Cost Optimization

- **Spot Instances**: 60-90% cost savings on GPU workloads
- **Resource Optimization**: Right-sized containers
- **Efficient Caching**: Reduced database load
- **Batch Processing**: Optimal resource utilization
