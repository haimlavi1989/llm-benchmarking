# Recommendation System Flow

## Complete Recommendation Request Flow

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

## Performance Targets by Flow Stage

```mermaid
graph TB
    subgraph "Response Time Breakdown"
        Auth[Auth Validation<br/>< 5ms]
        Cache[Cache Lookup<br/>< 2ms]
        DataFetch[Data Fetching<br/>< 50ms]
        Algorithm[Algorithm Processing<br/>< 80ms]
        Filtering[Filtering & Sorting<br/>< 10ms]
        Response[Response Formatting<br/>< 5ms]
    end
    
    subgraph "Performance Targets"
        CacheHit[Cache Hit Response<br/>< 50ms Total]
        CacheMiss[Cache Miss Response<br/>< 180ms Total]
        P95Target[P95 Latency<br/>< 100ms]
    end
    
    Auth --> Cache
    Cache --> DataFetch
    DataFetch --> Algorithm
    Algorithm --> Filtering
    Filtering --> Response
    
    CacheHit --> P95Target
    CacheMiss --> P95Target
```

## Cache Strategy for Recommendations

```mermaid
graph TB
    subgraph "Cache Key Strategy"
        UseCase[Use Case<br/>chatbot, summarization]
        Load[Load Profile<br/>rps, tokens, batch_size]
        SLA[SLA Requirements<br/>latency, accuracy]
        Key[Cache Key<br/>recommend:{use_case}:{load}:{sla}]
    end
    
    subgraph "Cache TTL Strategy"
        Hot[Hot Data<br/>TTL: 5 minutes<br/>High frequency requests]
        Warm[Warm Data<br/>TTL: 30 minutes<br/>Medium frequency]
        Cold[Cold Data<br/>TTL: 2 hours<br/>Low frequency]
    end
    
    subgraph "Cache Invalidation"
        ModelUpdate[Model Updates<br/>Invalidate model cache]
        BenchmarkUpdate[New Benchmarks<br/>Invalidate recommendations]
        ConfigUpdate[Config Changes<br/>Invalidate all]
    end
    
    UseCase --> Key
    Load --> Key
    SLA --> Key
    
    Key --> Hot
    Key --> Warm
    Key --> Cold
    
    ModelUpdate --> ConfigUpdate
    BenchmarkUpdate --> ConfigUpdate
```

## Error Handling Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Service
    participant DB
    participant Cache
    
    Client->>API: POST /recommend
    
    alt Valid Request
        API->>Service: Process Request
        Service->>DB: Query Data
        
        alt DB Success
            DB-->>Service: Return Data
            Service->>Cache: Store Results
            Service-->>API: Success Response
            API-->>Client: 200 OK
        else DB Error
            DB-->>Service: Error
            Service->>Cache: Check Fallback Data
            
            alt Cache Has Data
                Cache-->>Service: Stale Data
                Service-->>API: Stale Response + Warning
                API-->>Client: 200 OK (Stale)
            else No Fallback
                Service-->>API: Error Response
                API-->>Client: 500 Error
            end
        end
    else Invalid Request
        API-->>Client: 400 Bad Request
    end
```

## Resource Optimization Flow

```mermaid
graph TB
    subgraph "VRAM Calculation"
        Params[Model Parameters<br/>7B, 13B, 70B]
        Quantization[Quantization<br/>FP16, INT8, INT4, AWQ]
        Formula[VRAM Formula<br/>(params × bits/8) × 1.2]
        VRAM[VRAM Requirements<br/>GB]
    end
    
    subgraph "GPU Matching"
        GPU[Available GPUs<br/>A100, H100, L4, V100]
        Spot[Spot Availability<br/>Cost optimization]
        Match[Hardware Match<br/>VRAM + Compute]
    end
    
    subgraph "Cost Optimization"
        SpotCost[Spot Instance Cost<br/>60-90% savings]
        ReservedCost[Reserved Instance Cost<br/>Predictable pricing]
        TotalCost[Total Cost of Ownership<br/>TCO calculation]
    end
    
    Params --> Formula
    Quantization --> Formula
    Formula --> VRAM
    
    VRAM --> Match
    GPU --> Match
    Spot --> Match
    
    Match --> SpotCost
    Match --> ReservedCost
    SpotCost --> TotalCost
    ReservedCost --> TotalCost
```
