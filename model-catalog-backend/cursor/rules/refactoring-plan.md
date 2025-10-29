# Argo Workflows Refactoring - Implementation Plan (v2)

## Context
Documentation showed `benchmark_configs` table but code didn't implement it.
Caused confusion - now implementing as documented.

**Key Issue:** Matrix generation in Argo workflow creates 9,000+ configs as JSON,
exceeding Argo's 1MB output limit. Solution: Store matrix in database instead.

## Phase 0: Pre-Migration Setup (1h)

### 1. Verify Alembic Setup
```bash
# Create versions directory if missing
mkdir -p alembic/versions

# Check alembic configuration
alembic current

# Verify database connection in alembic.ini
# Ensure: sqlalchemy.url points to correct database
```

### 2. Create Initial Migration (if none exists)
```bash
# Generate migration for existing models
alembic revision --autogenerate -m "initial_schema"

# Review migration file in alembic/versions/
# Verify it includes: models, model_versions, hardware_configs, 
#                     inference_frameworks, benchmark_results, etc.

# Test on dev database
alembic upgrade head

# Verify tables created
psql -d model_catalog -c "\dt"
```

## Phase 1: Database (2h)

### 1.1 Create BenchmarkConfig Model
- File: `src/models/benchmark_config.py`
- Table: `benchmark_configs`
- Key fields: model_version_id, hardware_config_id, framework_id, workload_type, batch_size, sequence_length, status, priority
- Status values: pending, running, completed, failed
- Critical index: idx_benchmark_config_status_priority for workflow queries

### 1.2 Update BenchmarkResult Model
- Add: `config_id` FK to `benchmark_configs` (nullable for backward compatibility)
- Add: relationship to BenchmarkConfig

### 1.3 Create Migration
```bash
alembic revision --autogenerate -m "add_benchmark_configs_table"
alembic upgrade head
```

### 1.4 Create Seed Script
- File: `scripts/db/seed_benchmark_data.py`
- Populate: hardware_configs (~20 rows)
- Populate: inference_frameworks (3 rows: vLLM, TGI, LMDeploy)
- Populate: use_case_taxonomy (~10 rows)

### 1.5 Verification
```bash
python scripts/db/seed_benchmark_data.py

# Verify counts
SELECT COUNT(*) FROM hardware_configs;      -- ~20
SELECT COUNT(*) FROM inference_frameworks;  -- 3
SELECT COUNT(*) FROM use_case_taxonomy;     -- ~10
```

## Phase 2: Services & APIs (3h)

### 2.1 Create BenchmarkConfig Repository
- File: `src/repositories/benchmark_config_repository.py`
- Methods:
  - `get_pending_batch()` - Atomic SELECT FOR UPDATE SKIP LOCKED
  - `mark_completed()` - Update status to completed
  - `mark_failed()` - Update status with error message
  - `reset_stale_running()` - Spot instance recovery
  - `get_progress_stats()` - Progress tracking

### 2.2 Create Workflow API Routes
- File: `src/api/v1/routes/workflow.py`
- Endpoints:
  - `POST /api/v1/workflow/configs/get-batch` - Fetch pending configs
  - `POST /api/v1/workflow/configs/{id}/status` - Update config status
  - `GET /api/v1/workflow/progress/{model-version-id}` - Get progress
  - `POST /api/v1/workflow/maintenance/reset-stale` - Reset stale configs

### 2.3 Integration Tests
- File: `tests/integration/test_workflow_api.py`
- Tests: get_pending_batch, update_status, progress_stats

## Phase 3: Workflow Scripts (2h)

### 3.1 Create Matrix Population Script
- File: `scripts/workflows/populate_matrix.py`
- Generates: 9,000+ benchmark_configs for a model_version
- Cartesian product: hardware × framework × workload × batch_size × sequence_length
- Priority assignment: chatbot + batch_size=1 gets highest priority

### 3.2 Update Argo Workflow
- File: `configs/argo/benchmark-workflow-v2.yaml`
- Changes:
  - Replace matrix generation with API call to get-batch
  - Add populate-matrix step
  - Add batch loop with check-pending
  - Use database for orchestration instead of workflow parameters

### 3.3 Spot Instance Recovery
- File: `configs/argo/spot-handler.yaml`
- CronJob running every 30min
- Calls: `/api/v1/workflow/maintenance/reset-stale`

## Phase 4: Documentation (1h)

### 4.1 Fix DATABASE.md
- Remove: Misleading partitioning section (lines 295-333)
- Add: Proper benchmark_configs schema documentation
- Add: Workflow integration explanation

### 4.2 Update context-layer.md
- Mark task as completed
- Document key decisions and files changed

### 4.3 Create Argo README
- File: `configs/argo/README.md`
- Contents:
  - Architecture diagram
  - How to trigger workflow
  - Monitoring queries
  - Troubleshooting guide

## Rollback Plan

### If Phase 2+ fails:
```bash
# Revert to workflow v1
kubectl apply -f configs/argo/benchmark-workflow.yaml
```

### If Phase 1 fails:
```bash
# Downgrade migration
alembic downgrade -1

# Verify table removed
psql -d model_catalog -c "\dt benchmark_configs"
```

## Key Design Decisions

### 1. Race Condition Prevention
Use `SELECT FOR UPDATE SKIP LOCKED` in get_pending_batch():
- Multiple workflow pods can safely fetch configs
- Each config assigned to exactly one pod
- No duplicate work

### 2. Spot Instance Recovery
- Configs stuck in 'running' > 2 hours → reset to 'pending'
- Automatic retry via workflow loop
- No data loss

### 3. Priority-Based Processing
- chatbot + batch_size=1: priority 100 (high)
- Other workloads: priority 200-1000 (lower)
- Workflow fetches by priority ascending

### 4. Backward Compatibility
- `config_id` in benchmark_results is nullable
- Existing results continue working
- New results link to configs

## Estimated Timeline

- **Phase 0**: 1h (setup)
- **Phase 1**: 2h (database)
- **Phase 2**: 3h (services/APIs)
- **Phase 3**: 2h (workflow)
- **Phase 4**: 1h (documentation)
- **Total**: 9h

## Next Steps

Start Phase 0:
```bash
cd model-catalog-backend
mkdir -p alembic/versions  # ✅ DONE
# Continue with alembic setup verification...
```
