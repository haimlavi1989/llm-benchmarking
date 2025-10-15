-- TimescaleDB Initialization Script
-- Creates hypertables, compression policies, and continuous aggregates
-- for optimal time-series performance

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Convert benchmark_results table to hypertable
-- Partition by benchmark_date with 1-day chunks
SELECT create_hypertable(
    'benchmark_results',
    'benchmark_date',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add compression policy
-- Compress chunks older than 7 days to save storage
SELECT add_compression_policy(
    'benchmark_results',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add data retention policy
-- Automatically drop chunks older than 90 days
SELECT add_retention_policy(
    'benchmark_results',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_benchmark_results_ttft_throughput
    ON benchmark_results (ttft_p90_ms, throughput_tokens_sec, benchmark_date DESC);

CREATE INDEX IF NOT EXISTS idx_benchmark_results_workload
    ON benchmark_results (workload_type, benchmark_date DESC);

-- Create continuous aggregate for daily model statistics
-- This automatically updates every hour
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_model_stats_view
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', benchmark_date) AS stats_date,
    model_version_id,
    AVG(accuracy_score) AS avg_accuracy,
    AVG(throughput_tokens_sec) AS avg_throughput,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY ttft_p90_ms) AS p95_latency_ms,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY ttft_p90_ms) AS p50_latency_ms,
    AVG(gpu_utilization_pct) AS avg_gpu_utilization,
    AVG(memory_used_gb) AS avg_memory_used,
    COUNT(*) AS total_benchmarks
FROM benchmark_results
WHERE accuracy_score IS NOT NULL
GROUP BY stats_date, model_version_id;

-- Create refresh policy for continuous aggregate
-- Refresh data every hour
SELECT add_continuous_aggregate_policy(
    'daily_model_stats_view',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create materialized view for top performing configurations
CREATE MATERIALIZED VIEW IF NOT EXISTS top_performing_configs AS
SELECT 
    br.model_version_id,
    br.hardware_config_id,
    br.framework_id,
    br.workload_type,
    AVG(br.throughput_tokens_sec) AS avg_throughput,
    AVG(br.ttft_p90_ms) AS avg_latency_p90,
    AVG(br.accuracy_score) AS avg_accuracy,
    COUNT(*) AS benchmark_count
FROM benchmark_results br
WHERE br.benchmark_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 
    br.model_version_id,
    br.hardware_config_id,
    br.framework_id,
    br.workload_type
HAVING COUNT(*) >= 3  -- At least 3 benchmarks
ORDER BY avg_throughput DESC;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_top_configs_throughput
    ON top_performing_configs (avg_throughput DESC);

-- Refresh policy for top_performing_configs (manual for now)
-- REFRESH MATERIALIZED VIEW top_performing_configs;

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO model_catalog_user;
-- GRANT SELECT ON daily_model_stats_view TO model_catalog_user;
-- GRANT SELECT ON top_performing_configs TO model_catalog_user;

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialization complete!';
    RAISE NOTICE 'Hypertable created: benchmark_results';
    RAISE NOTICE 'Compression policy: 7 days';
    RAISE NOTICE 'Retention policy: 90 days';
    RAISE NOTICE 'Continuous aggregate: daily_model_stats_view';
END $$;

