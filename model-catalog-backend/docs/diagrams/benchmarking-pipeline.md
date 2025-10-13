# Benchmarking Pipeline Flow

## Complete Argo Workflows Pipeline

```mermaid
graph TB
    subgraph "Pipeline Initiation"
        Trigger[Pipeline Trigger<br/>Manual/Scheduled]
        ConfigGen[Configuration Generator<br/>9,000+ Configs]
        Queue[Job Queue<br/>Priority-based]
    end
    
    subgraph "Environment Setup"
        NodeAlloc[Node Allocation<br/>GPU Resources]
        ModelDownload[Model Download<br/>Registry/Artifacts]
        EnvSetup[Environment Setup<br/>Dependencies]
        Checkpoint[Checkpoint Check<br/>Resume Logic]
    end
    
    subgraph "Benchmark Execution"
        TGI[TGI Benchmark<br/>Text Generation]
        vLLM[vLLM Benchmark<br/>Large Language Models]
        LMDeploy[LMDeploy Benchmark<br/>Optimized Inference]
        Metrics[Metrics Collection<br/>Performance Data]
    end
    
    subgraph "Data Processing"
        Validation[Result Validation<br/>Data Quality]
        Aggregation[Metrics Aggregation<br/>Statistical Analysis]
        Storage[Result Storage<br/>TimescaleDB]
        Cache[Cache Update<br/>Redis]
    end
    
    subgraph "Analysis & Optimization"
        TOPSIS[TOPSIS Algorithm<br/>Multi-criteria Analysis]
        Pareto[Pareto Optimization<br/>Frontier Analysis]
        Ranking[Solution Ranking<br/>Best Configurations]
        Recommendations[Generate Recommendations<br/>User-specific]
    end
    
    subgraph "Completion & Cleanup"
        Notification[Completion Notification<br/>Slack/Email]
        Cleanup[Resource Cleanup<br/>GPU Release]
        Archive[Archive Results<br/>Long-term Storage]
        Report[Generate Reports<br/>Analytics Dashboard]
    end
    
    %% Flow connections
    Trigger --> ConfigGen
    ConfigGen --> Queue
    Queue --> NodeAlloc
    
    NodeAlloc --> ModelDownload
    ModelDownload --> EnvSetup
    EnvSetup --> Checkpoint
    
    Checkpoint --> TGI
    Checkpoint --> vLLM
    Checkpoint --> LMDeploy
    
    TGI --> Metrics
    vLLM --> Metrics
    LMDeploy --> Metrics
    
    Metrics --> Validation
    Validation --> Aggregation
    Aggregation --> Storage
    Storage --> Cache
    
    Cache --> TOPSIS
    Cache --> Pareto
    TOPSIS --> Ranking
    Pareto --> Ranking
    Ranking --> Recommendations
    
    Recommendations --> Notification
    Notification --> Cleanup
    Cleanup --> Archive
    Archive --> Report
```

## Spot Instance Interruption Handling

```mermaid
stateDiagram-v2
    [*] --> Running : Pipeline Started
    
    Running --> Checkpointing : Interruption Warning (2 min)
    Checkpointing --> Paused : State Saved
    Paused --> Resuming : New Instance Available
    Resuming --> Running : State Restored
    
    Running --> Completed : Normal Completion
    Running --> Failed : Error Occurred
    Failed --> Retrying : Auto Retry (3 attempts)
    Retrying --> Running : Retry Successful
    Retrying --> Failed : Max Retries Reached
    
    Completed --> [*] : Pipeline Success
    Failed --> [*] : Pipeline Failed
    
    note right of Checkpointing
        Save current progress
        Model state
        Intermediate results
        Configuration data
    end note
    
    note right of Resuming
        Restore from checkpoint
        Validate state
        Continue from last position
    end note
```

## Multi-Criteria Optimization Flow

```mermaid
graph TB
    subgraph "Data Collection"
        BenchResults[Benchmark Results<br/>Latency, Accuracy, Cost]
        UserPrefs[User Preferences<br/>Weight Configuration]
        Constraints[Constraints<br/>Hardware Limits]
    end
    
    subgraph "TOPSIS Processing"
        Normalize[Normalize Data<br/>Min-Max Scaling]
        Weighted[Apply Weights<br/>User Preferences]
        Ideal[Calculate Ideal Solution<br/>Best Performance]
        AntiIdeal[Calculate Anti-Ideal<br/>Worst Performance]
        Distance[Calculate Distances<br/>Euclidean Distance]
        Score[Calculate TOPSIS Score<br/>Relative Closeness]
    end
    
    subgraph "Pareto Processing"
        Objectives[Define Objectives<br/>Multi-objective Space]
        Dominance[Check Dominance<br/>Pareto Optimality]
        Front[Build Pareto Front<br/>Non-dominated Solutions]
        Ranking[Rank Solutions<br/>NSGA-II Algorithm]
    end
    
    subgraph "Recommendation Generation"
        Combine[Combine Results<br/>TOPSIS + Pareto]
        Filter[Apply Filters<br/>User Constraints]
        Rank[Final Ranking<br/>Weighted Score]
        Recommend[Generate Recommendations<br/>Top N Solutions]
    end
    
    %% TOPSIS flow
    BenchResults --> Normalize
    UserPrefs --> Weighted
    Normalize --> Weighted
    Weighted --> Ideal
    Weighted --> AntiIdeal
    Ideal --> Distance
    AntiIdeal --> Distance
    Distance --> Score
    
    %% Pareto flow
    BenchResults --> Objectives
    Objectives --> Dominance
    Dominance --> Front
    Front --> Ranking
    
    %% Combination flow
    Score --> Combine
    Ranking --> Combine
    Constraints --> Filter
    Combine --> Filter
    Filter --> Rank
    Rank --> Recommend
```

## Configuration Matrix Generation

```mermaid
graph TB
    subgraph "Model Variants"
        Models[50+ Models<br/>LLaMA, GPT, Mistral]
        Quantizations[Quantization Types<br/>FP16, INT8, INT4, AWQ]
        Frameworks[Inference Frameworks<br/>TGI, vLLM, LMDeploy]
    end
    
    subgraph "Hardware Configurations"
        GPU[GPU Types<br/>A100, H100, V100]
        Memory[Memory Configs<br/>40GB, 80GB, 160GB]
        Compute[Compute Configs<br/>Single, Multi-GPU]
    end
    
    subgraph "Benchmark Parameters"
        BatchSize[Batch Sizes<br/>1, 4, 8, 16, 32]
        SeqLength[Sequence Lengths<br/>512, 1024, 2048, 4096]
        Precision[Precision Types<br/>FP32, FP16, INT8, INT4]
    end
    
    subgraph "Configuration Matrix"
        Matrix[Total Configurations<br/>9,000+ Combinations]
        Validation[Configuration Validation<br/>Compatibility Check]
        Priority[Priority Assignment<br/>Critical Path First]
        Queue[Job Queue<br/>Batch Processing]
    end
    
    %% Matrix generation
    Models --> Matrix
    Quantizations --> Matrix
    Frameworks --> Matrix
    GPU --> Matrix
    Memory --> Matrix
    Compute --> Matrix
    BatchSize --> Matrix
    SeqLength --> Matrix
    Precision --> Matrix
    
    %% Validation and queuing
    Matrix --> Validation
    Validation --> Priority
    Priority --> Queue
```

## Resource Allocation Strategy

```mermaid
graph TB
    subgraph "Resource Discovery"
        NodeDiscovery[Node Discovery<br/>GPU Availability]
        ResourceCheck[Resource Check<br/>Memory, Compute]
        AffinityCheck[Affinity Check<br/>Node Preferences]
    end
    
    subgraph "Allocation Strategy"
        BinPacking[Bin Packing<br/>Optimal Utilization]
        PriorityClass[Priority Classes<br/>High, Medium, Low]
        NodeAffinity[Node Affinity<br/>GPU Type Matching]
        AntiAffinity[Anti-Affinity<br/>Spread Workloads]
    end
    
    subgraph "Cost Optimization"
        SpotSelection[Spot Instance Selection<br/>Cost vs Availability]
        PreemptionRisk[Preemption Risk Assessment<br/>Instance Type Analysis]
        CostCalculation[Cost Calculation<br/>Total Cost of Ownership]
    end
    
    subgraph "Monitoring & Adjustment"
        Utilization[Utilization Monitoring<br/>Real-time Metrics]
        Scaling[Auto Scaling<br/>Dynamic Adjustment]
        Rebalancing[Load Rebalancing<br/>Optimal Distribution]
    end
    
    %% Allocation flow
    NodeDiscovery --> ResourceCheck
    ResourceCheck --> AffinityCheck
    AffinityCheck --> BinPacking
    
    BinPacking --> PriorityClass
    PriorityClass --> NodeAffinity
    NodeAffinity --> AntiAffinity
    
    AntiAffinity --> SpotSelection
    SpotSelection --> PreemptionRisk
    PreemptionRisk --> CostCalculation
    
    CostCalculation --> Utilization
    Utilization --> Scaling
    Scaling --> Rebalancing
```
