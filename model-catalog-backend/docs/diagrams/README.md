# Architecture Diagrams

This directory contains all system architecture diagrams in Mermaid format for easy version control and rendering.

## Diagram Files

### System Architecture
- `system-overview.md` - High-level system design
- `request-flow.md` - API request flow diagrams
- `deployment-architecture.md` - Kubernetes deployment structure

### Database Architecture
- `database-schema.md` - Entity Relationship Diagrams
- `data-flow.md` - Data flow and caching strategies
- `partitioning-strategy.md` - Database partitioning approach

### Pipeline Architecture
- `benchmarking-pipeline.md` - Argo Workflows pipeline flow
- `spot-instance-handling.md` - Spot instance interruption handling
- `optimization-algorithms.md` - TOPSIS and Pareto optimization flows

### Infrastructure
- `kubernetes-deployment.md` - K8s namespace and resource allocation
- `monitoring-architecture.md` - Observability and monitoring setup
- `security-architecture.md` - Network policies and security controls

## Rendering Diagrams

These diagrams can be rendered in:
- GitHub (native Mermaid support)
- VS Code (with Mermaid extension)
- GitLab (native Mermaid support)
- Documentation sites (with Mermaid plugins)

## Updating Diagrams

When updating diagrams:
1. Modify the Mermaid code in the respective `.md` files
2. Test rendering in your preferred environment
3. Commit changes to version control
4. Update references in main documentation files
