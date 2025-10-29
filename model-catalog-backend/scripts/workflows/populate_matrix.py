"""Populate benchmark_configs matrix for a model version."""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.models import (
    BenchmarkConfig, ModelVersion, HardwareConfig,
    InferenceFramework
)
from src.repositories.benchmark_config_repository import BenchmarkConfigRepository


# Configuration matrix dimensions
WORKLOAD_TYPES = [
    "chatbot",              # Interactive, latency-sensitive
    "summarization",        # Batch-friendly, throughput-focused
    "qa",                   # Accuracy-critical
    "code-generation",      # Mixed requirements
    "creative-writing"      # Quality-focused
]

BATCH_SIZES = [1, 2, 4, 8]           # Inference batch sizes
SEQUENCE_LENGTHS = [1024, 2048, 4096]  # Context lengths


def calculate_priority(workload: str, batch_size: int, sequence_length: int) -> int:
    """
    Calculate priority for a config.
    
    Lower number = higher priority (runs first).
    
    Priority Rules:
    - Chatbot + batch_size=1 + short context: Highest (100-110)
    - Interactive workloads: High (200-300)
    - Batch workloads: Medium (400-600)
    - Long context: Lower priority (+100)
    
    Args:
        workload: Workload type
        batch_size: Batch size
        sequence_length: Context length
        
    Returns:
        Priority value (100-1000)
    """
    base_priority = {
        "chatbot": 100,
        "qa": 200,
        "code-generation": 300,
        "creative-writing": 400,
        "summarization": 500
    }.get(workload, 600)
    
    # Penalize larger batch sizes (less priority)
    batch_penalty = (batch_size - 1) * 10
    
    # Penalize longer contexts (less priority)
    seq_penalty = {
        1024: 0,
        2048: 20,
        4096: 40,
        8192: 60
    }.get(sequence_length, 80)
    
    return base_priority + batch_penalty + seq_penalty


async def populate_matrix(
    model_version_id: UUID,
    session: AsyncSession,
    dry_run: bool = False
) -> int:
    """
    Generate full benchmark matrix for a model version.
    
    Creates configs for every combination of:
    - Hardware configs (L4, A100, H100, multi-GPU, etc.)
    - Inference frameworks (vLLM, TGI, LMDeploy)
    - Workload types (chatbot, summarization, etc.)
    - Batch sizes (1, 2, 4, 8)
    - Sequence lengths (1024, 2048, 4096)
    
    Args:
        model_version_id: Model version UUID
        session: Database session
        dry_run: If True, only count configs without creating
        
    Returns:
        Number of configs created
    """
    
    # Verify model version exists
    result = await session.execute(
        select(ModelVersion).where(ModelVersion.id == model_version_id)
    )
    model_version = result.scalar_one_or_none()
    
    if not model_version:
        print(f"❌ Model version {model_version_id} not found")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"📊 Benchmark Matrix Population")
    print(f"{'='*70}\n")
    print(f"Model Version ID: {model_version_id}")
    print(f"Quantization: {model_version.quantization}")
    print(f"Format: {model_version.format}")
    print(f"VRAM Requirement: {model_version.vram_requirement_gb:.2f} GB")
    print(f"\n{'='*70}\n")
    
    # Fetch all hardware configs
    hw_result = await session.execute(select(HardwareConfig))
    hardware_configs = hw_result.scalars().all()
    print(f"🔧 Hardware Configs: {len(hardware_configs)}")
    
    # Filter hardware by VRAM requirement (model must fit)
    vram_needed = model_version.vram_requirement_gb
    compatible_hardware = [
        hw for hw in hardware_configs 
        if hw.total_vram_gb >= vram_needed
    ]
    print(f"   Compatible (VRAM >= {vram_needed:.1f}GB): {len(compatible_hardware)}")
    
    if not compatible_hardware:
        print(f"\n❌ No compatible hardware found for this model!")
        print(f"   Model requires: {vram_needed:.1f}GB VRAM")
        print(f"   Max available: {max(hw.total_vram_gb for hw in hardware_configs):.1f}GB")
        sys.exit(1)
    
    # Fetch all frameworks
    fw_result = await session.execute(select(InferenceFramework))
    frameworks = fw_result.scalars().all()
    print(f"🚀 Inference Frameworks: {len(frameworks)}")
    
    # Calculate expected matrix size
    expected_count = (
        len(compatible_hardware) * 
        len(frameworks) * 
        len(WORKLOAD_TYPES) * 
        len(BATCH_SIZES) * 
        len(SEQUENCE_LENGTHS)
    )
    
    print(f"\n📈 Matrix Dimensions:")
    print(f"   Hardware:        {len(compatible_hardware)}")
    print(f"   Frameworks:      {len(frameworks)}")
    print(f"   Workloads:       {len(WORKLOAD_TYPES)}")
    print(f"   Batch Sizes:     {len(BATCH_SIZES)}")
    print(f"   Seq Lengths:     {len(SEQUENCE_LENGTHS)}")
    print(f"   {'─'*50}")
    print(f"   Expected Total:  {expected_count:,} configs")
    
    if dry_run:
        print(f"\n🏁 DRY RUN - No configs created")
        print(f"{'='*70}\n")
        return expected_count
    
    # Generate cartesian product
    print(f"\n⚙️  Generating configs...")
    configs = []
    
    for hw in compatible_hardware:
        for fw in frameworks:
            for workload in WORKLOAD_TYPES:
                for batch_size in BATCH_SIZES:
                    for seq_len in SEQUENCE_LENGTHS:
                        priority = calculate_priority(workload, batch_size, seq_len)
                        
                        config = BenchmarkConfig(
                            model_version_id=model_version_id,
                            hardware_config_id=hw.id,
                            framework_id=fw.id,
                            workload_type=workload,
                            batch_size=batch_size,
                            sequence_length=seq_len,
                            status='pending',
                            priority=priority
                        )
                        configs.append(config)
    
    # Bulk insert using repository
    print(f"💾 Inserting {len(configs):,} configs into database...")
    repo = BenchmarkConfigRepository(session)
    count = await repo.bulk_create_configs(configs)
    
    print(f"\n✅ Successfully created {count:,} benchmark configurations!")
    
    # Show priority distribution
    priority_ranges = {
        "Highest (100-199)": len([c for c in configs if 100 <= c.priority < 200]),
        "High (200-299)": len([c for c in configs if 200 <= c.priority < 300]),
        "Medium (300-499)": len([c for c in configs if 300 <= c.priority < 500]),
        "Low (500+)": len([c for c in configs if c.priority >= 500])
    }
    
    print(f"\n📊 Priority Distribution:")
    for range_name, count in priority_ranges.items():
        pct = (count / len(configs) * 100) if configs else 0
        print(f"   {range_name}: {count:,} ({pct:.1f}%)")
    
    print(f"\n{'='*70}\n")
    
    return count


async def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python populate_matrix.py <model_version_id> [--dry-run]")
        print("\nExamples:")
        print("  python populate_matrix.py 123e4567-e89b-12d3-a456-426614174000")
        print("  python populate_matrix.py 123e4567-e89b-12d3-a456-426614174000 --dry-run")
        sys.exit(1)
    
    model_version_id = UUID(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            count = await populate_matrix(model_version_id, session, dry_run=dry_run)
            
            if not dry_run:
                # Show next steps
                print("🎯 Next Steps:")
                print(f"   1. Trigger Argo workflow:")
                print(f"      argo submit benchmark-workflow-v2.yaml \\")
                print(f"        -p model-version-id=\"{model_version_id}\"")
                print(f"\n   2. Monitor progress:")
                print(f"      curl http://api:8000/api/v1/workflow/progress/{model_version_id}")
                print(f"\n   3. Watch workflow:")
                print(f"      argo watch model-benchmark-pipeline-v2-xxxxx")
                print()
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())




