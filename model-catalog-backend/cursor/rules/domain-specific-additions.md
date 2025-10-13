# Domain Knowledge
Add your specific domain rules here:

## [Example: E-commerce]
- Always consider cart abandonment in checkout flows
- Payment flows must be PCI-DSS compliant
- Inventory checks before order confirmation
- Consider international currencies and taxes

## [Example: Healthcare]
- PHI must be encrypted at rest and in transit
- Audit logs required for all data access
- HIPAA compliance checklist must be reviewed
- No PHI in logs or error messages

## [Your Domain: AI Model Benchmarking & Cataloging]
- Cost & Reliability: Must use Spot Instances (GPU subscription) to achieve 60-90% cost savings
- Preemption Handling: Implement Checkpoint/Resume mechanism using Argo Workflows and Node Termination Handler to handle Spot Instance evictions automatically and fault-tolerantly
- Benchmarking Integrity: No GPU sharing/MIG during benchmark runs to ensure consistent and deterministic performance measurements
- Data Freshness Strategy: System operates in Batch processing model (benchmark runs take hours/days), not real-time. Use Smart Caching and Materialized Views to maintain optimal data freshness for decisions
- Performance Filtering: API response time for filtering and complex queries must be under 500ms, with P95 target under 100ms
- Caching Target: Redis Cache layer must achieve Hit Ratio above 80% to maintain high performance
- Selection Logic: Implement Multi-Criteria Optimization algorithms (such as TOPSIS or Pareto optimization) for model selection, balancing metrics like accuracy, latency, throughput, and cost according to use-case defined weights
- Resource Allocation: Deterministic VRAM calculation required to optimally match hardware (GPU count, GPU type) to model requirements (parameters, quantization)
- Security Baseline: Enforce Pod Security Standards (restricted) in Kubernetes and implement NetworkPolicy for micro-segmentation (default deny-all)
- Secrets Management: All credentials and keys must be managed through External Secrets Operator (or similar solution), not stored as regular Kubernetes Secrets
- Benchmarking Coverage: Ensure Pipeline (Argo Workflows) generates and runs all 9,000+ configurations (model, hardware, framework, quantization) required for comprehensive coverage
