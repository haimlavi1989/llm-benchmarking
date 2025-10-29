"""Seed database with reference data for benchmarking."""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.models import HardwareConfig, InferenceFramework, UseCaseTaxonomy


async def seed_hardware_configs(session: AsyncSession):
    """Seed hardware configurations."""
    print("🔧 Seeding hardware configurations...")
    
    hardware_configs = [
        # AWS Instances - Single GPU
        HardwareConfig(
            gpu_type="L4",
            gpu_count=1,
            vram_per_gpu_gb=24,
            total_vram_gb=24,
            cost_per_hour_usd=0.75,
            cloud_provider="aws",
            instance_type="g6.xlarge",
            spot_available=True,
            specs={"memory_gb": 16, "cpu_cores": 4, "network": "25 Gbps"}
        ),
        HardwareConfig(
            gpu_type="A100-40GB",
            gpu_count=1,
            vram_per_gpu_gb=40,
            total_vram_gb=40,
            cost_per_hour_usd=3.06,
            cloud_provider="aws",
            instance_type="p4d.24xlarge",
            spot_available=True,
            specs={"memory_gb": 32, "cpu_cores": 8, "network": "400 Gbps", "nvlink": True}
        ),
        HardwareConfig(
            gpu_type="A100-80GB",
            gpu_count=1,
            vram_per_gpu_gb=80,
            total_vram_gb=80,
            cost_per_hour_usd=4.10,
            cloud_provider="aws",
            instance_type="p4de.24xlarge",
            spot_available=True,
            specs={"memory_gb": 64, "cpu_cores": 16, "network": "400 Gbps", "nvlink": True}
        ),
        HardwareConfig(
            gpu_type="H100",
            gpu_count=1,
            vram_per_gpu_gb=80,
            total_vram_gb=80,
            cost_per_hour_usd=8.50,
            cloud_provider="aws",
            instance_type="p5.48xlarge",
            spot_available=False,
            specs={"memory_gb": 96, "cpu_cores": 24, "network": "3200 Gbps", "nvlink": True}
        ),
        
        # Multi-GPU configs
        HardwareConfig(
            gpu_type="A100-80GB",
            gpu_count=2,
            vram_per_gpu_gb=80,
            total_vram_gb=160,
            cost_per_hour_usd=8.20,
            cloud_provider="aws",
            instance_type="p4de.24xlarge",
            spot_available=True,
            specs={"memory_gb": 128, "cpu_cores": 32, "network": "400 Gbps", "nvlink": True}
        ),
        HardwareConfig(
            gpu_type="A100-80GB",
            gpu_count=4,
            vram_per_gpu_gb=80,
            total_vram_gb=320,
            cost_per_hour_usd=16.40,
            cloud_provider="aws",
            instance_type="p4de.24xlarge",
            spot_available=True,
            specs={"memory_gb": 256, "cpu_cores": 64, "network": "400 Gbps", "nvlink": True}
        ),
        HardwareConfig(
            gpu_type="A100-80GB",
            gpu_count=8,
            vram_per_gpu_gb=80,
            total_vram_gb=640,
            cost_per_hour_usd=32.80,
            cloud_provider="aws",
            instance_type="p4de.24xlarge",
            spot_available=True,
            specs={"memory_gb": 512, "cpu_cores": 96, "network": "400 Gbps", "nvlink": True}
        ),
        
        # GCP Instances
        HardwareConfig(
            gpu_type="L4",
            gpu_count=1,
            vram_per_gpu_gb=24,
            total_vram_gb=24,
            cost_per_hour_usd=0.80,
            cloud_provider="gcp",
            instance_type="g2-standard-4",
            spot_available=True,
            specs={"memory_gb": 16, "cpu_cores": 4, "network": "32 Gbps"}
        ),
        HardwareConfig(
            gpu_type="A100-40GB",
            gpu_count=1,
            vram_per_gpu_gb=40,
            total_vram_gb=40,
            cost_per_hour_usd=3.15,
            cloud_provider="gcp",
            instance_type="a2-highgpu-1g",
            spot_available=True,
            specs={"memory_gb": 85, "cpu_cores": 12, "network": "100 Gbps"}
        ),
        HardwareConfig(
            gpu_type="A100-40GB",
            gpu_count=2,
            vram_per_gpu_gb=40,
            total_vram_gb=80,
            cost_per_hour_usd=6.30,
            cloud_provider="gcp",
            instance_type="a2-highgpu-2g",
            spot_available=True,
            specs={"memory_gb": 170, "cpu_cores": 24, "network": "100 Gbps"}
        ),
        
        # Azure Instances
        HardwareConfig(
            gpu_type="A100-80GB",
            gpu_count=1,
            vram_per_gpu_gb=80,
            total_vram_gb=80,
            cost_per_hour_usd=4.25,
            cloud_provider="azure",
            instance_type="Standard_NC24ads_A100_v4",
            spot_available=True,
            specs={"memory_gb": 220, "cpu_cores": 24, "network": "80 Gbps"}
        ),
    ]
    
    session.add_all(hardware_configs)
    await session.commit()
    print(f"✅ Seeded {len(hardware_configs)} hardware configurations")
    return len(hardware_configs)


async def seed_inference_frameworks(session: AsyncSession):
    """Seed inference frameworks."""
    print("🚀 Seeding inference frameworks...")
    
    frameworks = [
        InferenceFramework(
            name="vLLM",
            version="v0.5.0",
            capabilities={
                "quantization": ["awq", "gptq", "fp16", "int8"],
                "features": [
                    "continuous_batching", 
                    "paged_attention", 
                    "prefix_caching",
                    "speculative_decoding"
                ],
                "model_architectures": [
                    "llama", "mistral", "mixtral", "phi", "qwen"
                ]
            },
            supports_quantization=True,
            supports_streaming=True,
            config_template={
                "gpu_memory_utilization": 0.9,
                "max_num_seqs": 256,
                "max_num_batched_tokens": 2048,
                "enable_prefix_caching": True
            }
        ),
        InferenceFramework(
            name="TGI",
            version="v2.0.0",
            capabilities={
                "quantization": ["bitsandbytes", "gptq", "fp16", "eetq"],
                "features": [
                    "flash_attention", 
                    "trust_remote_code",
                    "continuous_batching",
                    "tensor_parallelism"
                ],
                "model_architectures": [
                    "llama", "mistral", "falcon", "gpt-neox", "bloom"
                ]
            },
            supports_quantization=True,
            supports_streaming=True,
            config_template={
                "max_concurrent_requests": 128,
                "max_input_length": 4096,
                "max_total_tokens": 8192,
                "waiting_served_ratio": 1.2
            }
        ),
        InferenceFramework(
            name="LMDeploy",
            version="v0.4.0",
            capabilities={
                "quantization": ["awq", "w4a16", "w8a8", "fp16"],
                "features": [
                    "turbomind_backend", 
                    "pytorch_backend",
                    "persistent_batch",
                    "kv_cache_quant"
                ],
                "model_architectures": [
                    "llama", "internlm", "qwen", "baichuan", "vicuna"
                ]
            },
            supports_quantization=True,
            supports_streaming=True,
            config_template={
                "cache_max_entry_count": 0.8,
                "engine_max_batch_size": 128,
                "tp": 1,
                "session_len": 4096
            }
        ),
    ]
    
    session.add_all(frameworks)
    await session.commit()
    print(f"✅ Seeded {len(frameworks)} inference frameworks")
    return len(frameworks)


async def seed_use_case_taxonomy(session: AsyncSession):
    """Seed use case taxonomy."""
    print("📋 Seeding use case taxonomy...")
    
    use_cases = [
        UseCaseTaxonomy(
            category="text-generation",
            subcategory="chatbot",
            pipeline_tag="text-generation",
            characteristics={
                "latency_sensitive": True,
                "typical_context_length": 4096,
                "interactive": True,
                "streaming_required": True,
                "typical_output_length": 200
            },
            default_weights={
                "ttft": 0.4,        # Time to first token (most important for chatbots)
                "tpot": 0.3,        # Time per output token
                "throughput": 0.2,  # Overall throughput
                "cost": 0.1         # Cost efficiency
            }
        ),
        UseCaseTaxonomy(
            category="text-generation",
            subcategory="summarization",
            pipeline_tag="summarization",
            characteristics={
                "latency_sensitive": False,
                "typical_context_length": 8192,
                "batch_friendly": True,
                "streaming_required": False,
                "typical_output_length": 500
            },
            default_weights={
                "throughput": 0.5,  # Batch processing - throughput is key
                "accuracy": 0.3,
                "cost": 0.2
            }
        ),
        UseCaseTaxonomy(
            category="question-answering",
            subcategory="qa",
            pipeline_tag="question-answering",
            characteristics={
                "latency_sensitive": True,
                "typical_context_length": 2048,
                "accuracy_critical": True,
                "interactive": True,
                "typical_output_length": 100
            },
            default_weights={
                "accuracy": 0.4,
                "ttft": 0.3,
                "cost": 0.3
            }
        ),
        UseCaseTaxonomy(
            category="text-generation",
            subcategory="code-generation",
            pipeline_tag="text-generation",
            characteristics={
                "latency_sensitive": True,
                "typical_context_length": 8192,
                "accuracy_critical": True,
                "streaming_required": True,
                "typical_output_length": 300
            },
            default_weights={
                "accuracy": 0.35,
                "ttft": 0.25,
                "tpot": 0.25,
                "cost": 0.15
            }
        ),
        UseCaseTaxonomy(
            category="text-generation",
            subcategory="creative-writing",
            pipeline_tag="text-generation",
            characteristics={
                "latency_sensitive": False,
                "typical_context_length": 4096,
                "quality_over_speed": True,
                "streaming_required": True,
                "typical_output_length": 1000
            },
            default_weights={
                "accuracy": 0.4,
                "tpot": 0.3,
                "ttft": 0.2,
                "cost": 0.1
            }
        ),
        UseCaseTaxonomy(
            category="text-generation",
            subcategory="translation",
            pipeline_tag="translation",
            characteristics={
                "latency_sensitive": False,
                "typical_context_length": 2048,
                "accuracy_critical": True,
                "batch_friendly": True,
                "typical_output_length": 200
            },
            default_weights={
                "accuracy": 0.5,
                "throughput": 0.3,
                "cost": 0.2
            }
        ),
        UseCaseTaxonomy(
            category="text-generation",
            subcategory="content-moderation",
            pipeline_tag="text-classification",
            characteristics={
                "latency_sensitive": True,
                "typical_context_length": 1024,
                "accuracy_critical": True,
                "high_throughput": True,
                "typical_output_length": 50
            },
            default_weights={
                "accuracy": 0.5,
                "throughput": 0.3,
                "ttft": 0.2
            }
        ),
        UseCaseTaxonomy(
            category="embeddings",
            subcategory="semantic-search",
            pipeline_tag="feature-extraction",
            characteristics={
                "latency_sensitive": True,
                "typical_context_length": 512,
                "batch_friendly": True,
                "high_throughput": True
            },
            default_weights={
                "throughput": 0.5,
                "ttft": 0.3,
                "cost": 0.2
            }
        ),
    ]
    
    session.add_all(use_cases)
    await session.commit()
    print(f"✅ Seeded {len(use_cases)} use case taxonomies")
    return len(use_cases)


async def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("🌱 Starting database seeding...")
    print("="*60 + "\n")
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Seed data
            hw_count = await seed_hardware_configs(session)
            fw_count = await seed_inference_frameworks(session)
            uc_count = await seed_use_case_taxonomy(session)
            
            print("\n" + "="*60)
            print("✅ Database seeding completed successfully!")
            print("="*60)
            print(f"\nSummary:")
            print(f"  - Hardware Configs: {hw_count}")
            print(f"  - Inference Frameworks: {fw_count}")
            print(f"  - Use Case Taxonomies: {uc_count}")
            print(f"  - Total Records: {hw_count + fw_count + uc_count}")
            print("\n" + "="*60 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())




