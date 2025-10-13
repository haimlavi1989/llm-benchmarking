# Database Architecture

## Database Schema (ERD)

### Core Entities

```mermaid
erDiagram
    MODELS ||--o{ BENCHMARK_RESULTS : "has many"
    MODELS ||--o{ MODEL_VERSIONS : "has many"
    MODELS ||--o{ MODEL_USE_CASES : "belongs to"
    HARDWARE_CONFIGS ||--o{ BENCHMARK_RESULTS : "used in"
    INFERENCE_FRAMEWORKS ||--o{ BENCHMARK_RESULTS : "tested with"
    USE_CASE_TAXONOMY ||--o{ MODEL_USE_CASES : "categorizes"
    MODEL_VERSIONS ||--o{ BENCHMARK_RESULTS : "benchmarked"

    MODELS {
        uuid id PK
        string name UK "unique, indexed"
        string architecture "e.g., llama, gpt, mistral"
        bigint parameters "e.g., 7B, 13B, 70B"
        string base_model "parent model if fine-tuned"
        jsonb metadata "flexible model info"
        text_array tags "searchable tags"
        timestamp created_at
        timestamp updated_at
    }

    MODEL_VERSIONS {
        uuid id PK
        uuid model_id FK
        string version "e.g., v1.0, v2.1"
        string quantization "fp32, fp16, int8, int4"
        int quantization_bits "4, 8, 16, 32"
        string format "gguf, gptq, awq, safetensors"
        string artifact_uri "storage location"
        jsonb model_config "technical specs"
        float vram_requirement_gb "calculated VRAM"
        timestamp created_at
    }

    HARDWARE_CONFIGS {
        uuid id PK
        string gpu_type "A100-80GB, H100, L4"
        int gpu_count "1, 2, 4, 8"
        int vram_per_gpu_gb "24, 40, 80"
        int total_vram_gb "calculated"
        float cost_per_hour_usd "pricing"
        string cloud_provider "aws, gcp, azure"
        string instance_type "p4d.24xlarge, etc"
        boolean spot_available "true/false"
        jsonb specs "detailed hardware info"
        timestamp created_at
    }

    INFERENCE_FRAMEWORKS {
        uuid id PK
        string name "vLLM, TGI, LMDeploy"
        string version "v0.5.0"
        jsonb capabilities "features supported"
        boolean supports_quantization
        boolean supports_streaming
        jsonb config_template "default config"
        timestamp created_at
    }

    BENCHMARK_RESULTS {
        uuid id PK
        uuid model_version_id FK "indexed"
        uuid hardware_config_id FK "indexed"
        uuid framework_id FK "indexed"
        date benchmark_date "partitioned by date"
        string workload_type "chatbot, summarization"
        int batch_size
        int sequence_length
        float ttft_p50_ms "time to first token"
        float ttft_p90_ms "indexed for SLA queries"
        float ttft_p99_ms
        float tpot_p50_ms "time per output token"
        float tpot_p90_ms
        float tpot_p99_ms
        float throughput_tokens_sec "indexed"
        float rps_sustained "requests per second"
        float accuracy_score "task-specific"
        float gpu_utilization_pct
        float memory_used_gb
        jsonb detailed_metrics "raw data"
        timestamp created_at
    }

    USE_CASE_TAXONOMY {
        uuid id PK
        string category "text-generation, qa, etc"
        string subcategory "chatbot, creative-writing"
        string pipeline_tag "HuggingFace standard"
        jsonb characteristics "typical requirements"
        jsonb default_weights "ranking weights"
        timestamp created_at
    }

    MODEL_USE_CASES {
        uuid id PK
        uuid model_id FK "indexed"
        uuid use_case_id FK "indexed"
        float suitability_score "0.0 to 1.0"
        boolean recommended "pre-computed flag"
        int priority "ranking order"
        jsonb performance_summary "quick stats"
        timestamp created_at
    }

    DAILY_MODEL_STATS {
        uuid id PK
        uuid model_id FK "indexed"
        date stats_date "partitioned"
        float avg_accuracy
        float avg_throughput
        float p95_latency_ms
        int total_benchmarks
        jsonb aggregated_metrics "materialized view data"
        timestamp updated_at
    }

    MODEL_RANKINGS {
        uuid id PK
        uuid model_id FK
        string use_case_category
        float composite_score "TOPSIS/Pareto result"
        int rank_position "1, 2, 3..."
        jsonb score_breakdown "per criterion"
        timestamp calculated_at
        timestamp expires_at "cache TTL"
    }
```

## Schema Design Overview

### Entity Relationships

The database schema is designed around the core entities that support the LLM benchmarking platform with large-scale performance testing across 900+ configurations per model:

#### **Core Entities**
- **MODELS**: Base model information (GPT-4, Claude, Llama 3.1, etc.)
- **MODEL_VERSIONS**: Specific quantizations (FP16, INT8, INT4) and formats
- **HARDWARE_CONFIGS**: GPU configurations (L4, A100-80GB, H100) with pricing
- **INFERENCE_FRAMEWORKS**: vLLM, TGI, LMDeploy framework capabilities
- **BENCHMARK_RESULTS**: Time-series performance data from 900+ test combinations
- **USE_CASE_TAXONOMY**: Standardized use case categorization

#### **Performance Optimization Entities**
- **MODEL_USE_CASES**: Pre-computed model-use case suitability
- **DAILY_MODEL_STATS**: Materialized view for fast aggregations
- **MODEL_RANKINGS**: Cached TOPSIS/Pareto optimization results

### Key Design Decisions

#### **1. Normalized Model Structure**
- **MODELS** table stores base model information
- **MODEL_VERSIONS** handles different quantizations (FP16, INT8, INT4, AWQ)
- **VRAM calculation** formula: `(params × bits/8) × 1.2` stored per version
- **Artifact URI** points to storage location (S3, HuggingFace Hub)

#### **2. Time-Series Benchmark Data**
- **BENCHMARK_RESULTS** partitioned by date for TimescaleDB optimization
- **Percentile metrics** (P50, P90, P99) for SLA compliance
- **Indexed fields** for fast filtering: `ttft_p90_ms`, `throughput_tokens_sec`
- **Workload types** standardize benchmarking scenarios

#### **3. Use Case Taxonomy**
- **HuggingFace pipeline tags** for interoperability
- **Default weights** for TOPSIS algorithm
- **Characteristics** define typical requirements per use case

#### **4. Performance Optimization**
- **Pre-computed rankings** with TTL for cache invalidation
- **Materialized views** for daily aggregations
- **Indexed foreign keys** for fast joins

## Database Design Principles

### Performance Optimization

```mermaid
graph TB
    subgraph "Query Optimization"
        Indexes[Strategic Indexing]
        Partitions[Table Partitioning]
        Views[Materialized Views]
        Cache[Query Cache]
    end
    
    subgraph "Data Distribution"
        Sharding[Horizontal Sharding]
        Replication[Read Replicas]
        Archiving[Data Archiving]
    end
    
    subgraph "Time-Series Data"
        TimescaleDB[TimescaleDB]
        Compression[Compression]
        Retention[Retention Policies]
    end
    
    Indexes --> Performance
    Partitions --> Performance
    Views --> Performance
    Cache --> Performance
    TimescaleDB --> Performance
```

### Indexing Strategy

```sql
-- Performance-critical indexes for recommendation queries
CREATE INDEX idx_benchmark_results_model_hardware_framework 
ON benchmark_results (model_version_id, hardware_config_id, framework_id, benchmark_date DESC);

CREATE INDEX idx_benchmark_results_latency_sla 
ON benchmark_results (ttft_p90_ms, throughput_tokens_sec) 
WHERE ttft_p90_ms <= 300; -- SLA threshold

CREATE INDEX idx_models_use_cases_suitability 
ON model_use_cases (model_id, use_case_id, suitability_score DESC);

CREATE INDEX idx_model_rankings_use_case 
ON model_rankings (use_case_category, composite_score DESC, calculated_at DESC);

-- Time-series optimization indexes
CREATE INDEX idx_benchmark_results_date_workload 
ON benchmark_results (benchmark_date, workload_type);

CREATE INDEX idx_daily_stats_model_date 
ON daily_model_stats (model_id, stats_date DESC);

-- Hardware configuration indexes
CREATE INDEX idx_hardware_configs_vram_cost 
ON hardware_configs (total_vram_gb, cost_per_hour_usd, spot_available);

-- Model version indexes
CREATE INDEX idx_model_versions_vram_quantization 
ON model_versions (vram_requirement_gb, quantization_bits, format);

-- Partial indexes for active/recommended data
CREATE INDEX idx_recommended_models 
ON model_use_cases (model_id, recommended) WHERE recommended = true;

CREATE INDEX idx_active_rankings 
ON model_rankings (use_case_category, rank_position) 
WHERE expires_at > NOW();
```

## Data Flow Architecture

### Write Path

```mermaid
sequenceDiagram
    participant API as API Layer
    participant Cache as Redis Cache
    participant PG as PostgreSQL
    participant TS as TimescaleDB
    participant Queue as Message Queue
    
    API->>Cache: Invalidate Cache
    API->>PG: Write Transactional Data
    API->>Queue: Publish Event
    Queue->>TS: Write Time-Series Data
    TS->>Cache: Update Cache
```

### Read Path

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as API Layer
    participant Cache as Redis Cache
    participant PG as PostgreSQL
    participant TS as TimescaleDB
    
    Client->>API: Request Data
    API->>Cache: Check Cache
    
    alt Cache Hit (>80% target)
        Cache-->>API: Return Data
    else Cache Miss
        API->>PG: Query Database
        PG-->>API: Return Data
        API->>Cache: Store in Cache
    end
    
    API-->>Client: Return Response
```

## Data Partitioning Strategy

### Time-Based Partitioning

```sql
-- TimescaleDB hypertables for time-series data
CREATE TABLE benchmark_results (
    id UUID PRIMARY KEY,
    config_id UUID REFERENCES benchmark_configs(id),
    latency_ms DECIMAL,
    throughput_tps DECIMAL,
    memory_usage_gb DECIMAL,
    benchmarked_at TIMESTAMPTZ NOT NULL
);

-- Create hypertable with 1-day chunks
SELECT create_hypertable('benchmark_results', 'benchmarked_at', 
    chunk_time_interval => INTERVAL '1 day');
```

### Horizontal Partitioning

```sql
-- Partition by model framework
CREATE TABLE benchmark_configs (
    id UUID,
    model_id UUID,
    hardware_id UUID,
    framework VARCHAR(50),
    -- other columns
) PARTITION BY HASH (model_id);

-- Create partitions for each framework
CREATE TABLE benchmark_configs_llama PARTITION OF benchmark_configs
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE benchmark_configs_gpt PARTITION OF benchmark_configs
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
```

## Caching Strategy

### Redis Cache Layers

```mermaid
graph TB
    subgraph "L1 Cache - Application"
        AppCache[In-Memory Cache]
        TTL1[TTL: 5 minutes]
    end
    
    subgraph "L2 Cache - Redis"
        RedisCache[Redis Cluster]
        TTL2[TTL: 1 hour]
        Eviction[LRU Eviction]
    end
    
    subgraph "L3 Cache - Database"
        QueryCache[Query Cache]
        Materialized[Materialized Views]
    end
    
    AppCache --> RedisCache
    RedisCache --> QueryCache
    TTL1 --> AppCache
    TTL2 --> RedisCache
    Eviction --> RedisCache
```

### Cache Key Strategy

```python
# Cache key patterns
CACHE_KEYS = {
    "model_details": "model:{model_id}:details",
    "benchmark_results": "benchmark:{model_id}:{hardware_id}:results",
    "recommendations": "rec:{user_id}:{use_case}:recommendations",
    "hardware_list": "hardware:list:active",
    "model_metrics": "metrics:model:{model_id}:aggregated"
}

# Cache TTL configuration
CACHE_TTL = {
    "model_details": 3600,  # 1 hour
    "benchmark_results": 1800,  # 30 minutes
    "recommendations": 900,  # 15 minutes
    "hardware_list": 7200,  # 2 hours
    "model_metrics": 600  # 10 minutes
}
```

## Data Consistency

### Eventual Consistency Model

```mermaid
graph LR
    subgraph "Strong Consistency"
        User[User Data]
        Auth[Authentication]
        Config[Configuration]
    end
    
    subgraph "Eventual Consistency"
        Metrics[Benchmark Metrics]
        Cache[Cache Data]
        Analytics[Analytics Data]
    end
    
    User --> Strong
    Auth --> Strong
    Config --> Strong
    Metrics --> Eventual
    Cache --> Eventual
    Analytics --> Eventual
```

## Backup & Recovery

### Backup Strategy

```mermaid
graph TB
    subgraph "Backup Types"
        Full[Full Backup<br/>Daily]
        Incremental[Incremental<br/>Hourly]
        Logical[Logical Export<br/>Weekly]
    end
    
    subgraph "Storage"
        S3[S3 Storage]
        Glacier[Glacier Archive]
        Local[Local Storage]
    end
    
    subgraph "Recovery"
        PITR[Point-in-Time Recovery]
        CrossRegion[Cross-Region Backup]
        TestRestore[Test Restores]
    end
    
    Full --> S3
    Incremental --> S3
    Logical --> Glacier
    S3 --> PITR
    Glacier --> CrossRegion
    Local --> TestRestore
```

### Recovery Time Objectives

- **RTO (Recovery Time)**: < 4 hours
- **RPO (Recovery Point)**: < 1 hour
- **Backup Retention**: 30 days full, 1 year incremental
- **Cross-Region Replication**: Real-time for critical data
