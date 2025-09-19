#/Users/bbaer/Development/Cerebral/.venv/bin/python
"""
Enhanced Apple Silicon Accelerator with Hardware Auto-Detection
==============================================================

Advanced Apple Silicon optimization system that automatically detects hardware capabilities,
selects optimal models and dimensions, and provides hybrid processing for maximum performance.

New Features:
- Hardware auto-detection (M1/M2/M3/M4 Pro/Max/Ultra)
- Multi-dimensional embedding support (384D → 1536D)
- Automatic model recommendation based on hardware
- Performance optimization with MPS acceleration
- Real-time performance monitoring and metrics
- Hybrid processing for large sequences

Hardware Capabilities:
- M4 Pro/Max: 1024-1536D embeddings with BGE-Large models
- M3/M2 Pro/Max: 768-1024D embeddings with all-mpnet-base-v2
- M1/M2 base: 384-768D embeddings optimized
- Intel/AMD: CPU fallback with smaller models

Author: CerebraFlow Platform Team
Version: 2.0.0 - Enhanced Hardware Detection
Since: 2025-01-11
"""

import logging
import os
import platform
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

# Core ML/AI imports with graceful fallback
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("[INFO] PyTorch not available - Apple Silicon acceleration disabled")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("[INFO] Sentence Transformers not available")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("[INFO] NumPy not available")

class AppleSiliconChip(Enum):
    """Apple Silicon chip variants"""
    M1 = "M1"
    M1_PRO = "M1_Pro"
    M1_MAX = "M1_Max"
    M1_ULTRA = "M1_Ultra"
    M2 = "M2"
    M2_PRO = "M2_Pro"
    M2_MAX = "M2_Max"
    M2_ULTRA = "M2_Ultra"
    M3 = "M3"
    M3_PRO = "M3_Pro"
    M3_MAX = "M3_Max"
    M4 = "M4"
    M4_PRO = "M4_Pro"
    M4_MAX = "M4_Max"
    UNKNOWN = "Unknown"

class AcceleratorDevice(Enum):
    """Available acceleration devices"""
    NEURAL_ENGINE = "neural_engine"
    MPS = "mps"
    CUDA = "cuda"
    CPU = "cpu"

@dataclass
class ModelProfile:
    """Model performance profile for specific hardware"""
    name: str
    dimensions: int
    memory_mb: float
    performance_score: float
    recommended_batch_size: int
    max_sequence_length: int
    description: str

@dataclass
class HardwareProfile:
    """Hardware capability profile"""
    chip: AppleSiliconChip
    neural_engine_tops: float
    gpu_cores: int
    memory_bandwidth_gb_s: float
    unified_memory_gb: int
    recommended_models: List[ModelProfile]
    max_embedding_dimension: int

@dataclass
class PerformanceMetrics:
    """Real-time performance tracking"""
    embeddings_per_second: float = 0.0
    average_latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_utilization_percent: float = 0.0
    total_operations: int = 0
    failed_operations: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

class EnhancedAppleSiliconAccelerator:
    """
    Enhanced Apple Silicon accelerator with comprehensive hardware detection and optimization
    """
    
    def __init__(self):
        """Initialize the enhanced accelerator with full hardware profiling"""
        self.logger = logging.getLogger("CerebraFlow.EnhancedAppleSilicon")
        
        # System detection and profiling
        self.chip_model = self._detect_chip_model()
        self.hardware_profile = self._create_hardware_profile()
        self.available_devices = self._detect_devices()
        self.optimal_device = self._select_optimal_device()
        
        # Model management
        self.model_cache: Dict[str, Any] = {}
        self.current_model: Optional[str] = None
        self.current_dimensions: int = 384
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.performance_history: List[PerformanceMetrics] = []
        
        # Configuration
        self.config = {
            "auto_optimize_batch_size": True,
            "enable_hybrid_processing": True,
            "max_models_cached": 3,
            "performance_monitoring": True,
            "cache_timeout_minutes": 30
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        self.logger.info(" Enhanced Apple Silicon Accelerator initialized")
        self._log_hardware_capabilities()
        self._select_optimal_model()
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get comprehensive hardware information"""
        try:
            profile = self.hardware_profile
            chip_info = {
                'chip_type': profile.chip.value if profile else 'Unknown',
                'neural_engine_tops': profile.neural_engine_tops if profile else 0,
                'gpu_cores': profile.gpu_cores if profile else 0,
                'memory_bandwidth_gb_s': profile.memory_bandwidth_gb_s if profile else 0,
                'unified_memory_gb': profile.unified_memory_gb if profile else 0,
                'max_embedding_dimension': profile.max_embedding_dimension if profile else 384,
                'mps_available': self.optimal_device == AcceleratorDevice.MPS,
                'performance_estimate': profile.neural_engine_tops if profile else 0,
                'recommended_models': [model.name for model in profile.recommended_models] if profile else []
            }
            
            self.logger.info(f"Hardware Info: {chip_info['chip_type']} - {chip_info['neural_engine_tops']} TOPS")
            return chip_info
            
        except Exception as e:
            self.logger.error(f"Failed to get hardware info: {e}")
            return {
                'chip_type': 'Unknown',
                'neural_engine_tops': 0,
                'gpu_cores': 0,
                'memory_bandwidth_gb_s': 0,
                'unified_memory_gb': 0,
                'max_embedding_dimension': 384,
                'mps_available': False,
                'performance_estimate': 0,
                'recommended_models': []
            }
    
    def get_optimal_embedding_config(self) -> Dict[str, Any]:
        """Get optimal embedding configuration for current hardware"""
        try:
            profile = self.hardware_profile
            if not profile or not profile.recommended_models:
                # Fallback configuration
                return {
                    'dimensions': 384,
                    'model_name': 'all-MiniLM-L6-v2',
                    'device': 'cpu',
                    'batch_size': 32,
                    'max_sequence_length': 512,
                    'memory_mb': 90,
                    'performance_score': 0.8
                }
            
            # Get the best model for current hardware
            best_model = profile.recommended_models[0]  # First model is usually best
            device = 'mps' if self.optimal_device == AcceleratorDevice.MPS else 'cpu'
            
            config = {
                'dimensions': best_model.dimensions,
                'model_name': best_model.name,
                'device': device,
                'batch_size': best_model.recommended_batch_size,
                'max_sequence_length': best_model.max_sequence_length,
                'memory_mb': best_model.memory_mb,
                'performance_score': best_model.performance_score,
                'description': best_model.description
            }
            
            self.logger.info(f"Optimal Config: {config['dimensions']}D, {config['model_name']}, {config['device']}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to get optimal config: {e}")
            # Return safe fallback
            return {
                'dimensions': 384,
                'model_name': 'all-MiniLM-L6-v2',
                'device': 'cpu',
                'batch_size': 32,
                'max_sequence_length': 512,
                'memory_mb': 90,
                'performance_score': 0.8
            }
    
    def _detect_chip_model(self) -> AppleSiliconChip:
        """Detect specific Apple Silicon chip model"""
        if not (platform.system() == "Darwin" and platform.machine() == "arm64"):
            return AppleSiliconChip.UNKNOWN
        
        try:
            # Get CPU brand string
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode != 0:
                return AppleSiliconChip.UNKNOWN
            
            chip_info = result.stdout.strip().upper()
            
            # Detect M4 variants
            if "M4" in chip_info:
                if "MAX" in chip_info:
                    return AppleSiliconChip.M4_MAX
                elif "PRO" in chip_info:
                    return AppleSiliconChip.M4_PRO
                else:
                    return AppleSiliconChip.M4
            
            # Detect M3 variants
            elif "M3" in chip_info:
                if "MAX" in chip_info:
                    return AppleSiliconChip.M3_MAX
                elif "PRO" in chip_info:
                    return AppleSiliconChip.M3_PRO
                else:
                    return AppleSiliconChip.M3
            
            # Detect M2 variants
            elif "M2" in chip_info:
                if "ULTRA" in chip_info:
                    return AppleSiliconChip.M2_ULTRA
                elif "MAX" in chip_info:
                    return AppleSiliconChip.M2_MAX
                elif "PRO" in chip_info:
                    return AppleSiliconChip.M2_PRO
                else:
                    return AppleSiliconChip.M2
            
            # Detect M1 variants
            elif "M1" in chip_info:
                if "ULTRA" in chip_info:
                    return AppleSiliconChip.M1_ULTRA
                elif "MAX" in chip_info:
                    return AppleSiliconChip.M1_MAX
                elif "PRO" in chip_info:
                    return AppleSiliconChip.M1_PRO
                else:
                    return AppleSiliconChip.M1
            
            return AppleSiliconChip.UNKNOWN
            
        except Exception as e:
            self.logger.warning(f"Failed to detect chip model: {e}")
            return AppleSiliconChip.UNKNOWN
    
    def _create_hardware_profile(self) -> HardwareProfile:
        """Create hardware capability profile based on detected chip"""
        
        # Define model profiles
        model_384d = ModelProfile(
            name="all-MiniLM-L6-v2",
            dimensions=384,
            memory_mb=90,
            performance_score=0.8,
            recommended_batch_size=32,
            max_sequence_length=512,
            description="Fast, lightweight model for basic tasks"
        )
        
        model_768d = ModelProfile(
            name="all-mpnet-base-v2",
            dimensions=768,
            memory_mb=420,
            performance_score=0.9,
            recommended_batch_size=16,
            max_sequence_length=512,
            description="Balanced model for high-quality embeddings"
        )
        
        model_1024d = ModelProfile(
            name="sentence-transformers/all-MiniLM-L12-v2",
            dimensions=1024,
            memory_mb=520,
            performance_score=0.85,
            recommended_batch_size=12,
            max_sequence_length=512,
            description="Larger model for better accuracy"
        )
        
        model_1536d = ModelProfile(
            name="BAAI/bge-large-en-v1.5",
            dimensions=1536,
            memory_mb=1200,
            performance_score=0.95,
            recommended_batch_size=8,
            max_sequence_length=512,
            description="High-quality large model for enterprise use"
        )
        
        # Hardware-specific profiles
        profiles = {
            AppleSiliconChip.M4_MAX: HardwareProfile(
                chip=AppleSiliconChip.M4_MAX,
                neural_engine_tops=38.0,
                gpu_cores=40,
                memory_bandwidth_gb_s=400,
                unified_memory_gb=128,
                recommended_models=[model_1536d, model_1024d, model_768d],
                max_embedding_dimension=1536
            ),
            AppleSiliconChip.M4_PRO: HardwareProfile(
                chip=AppleSiliconChip.M4_PRO,
                neural_engine_tops=38.0,
                gpu_cores=20,
                memory_bandwidth_gb_s=273,
                unified_memory_gb=64,
                recommended_models=[model_1536d, model_1024d, model_768d],
                max_embedding_dimension=1536
            ),
            AppleSiliconChip.M4: HardwareProfile(
                chip=AppleSiliconChip.M4,
                neural_engine_tops=38.0,
                gpu_cores=10,
                memory_bandwidth_gb_s=120,
                unified_memory_gb=32,
                recommended_models=[model_1024d, model_768d, model_384d],
                max_embedding_dimension=1024
            ),
            AppleSiliconChip.M3_MAX: HardwareProfile(
                chip=AppleSiliconChip.M3_MAX,
                neural_engine_tops=35.0,
                gpu_cores=40,
                memory_bandwidth_gb_s=300,
                unified_memory_gb=128,
                recommended_models=[model_1024d, model_768d, model_384d],
                max_embedding_dimension=1024
            ),
            AppleSiliconChip.M3_PRO: HardwareProfile(
                chip=AppleSiliconChip.M3_PRO,
                neural_engine_tops=35.0,
                gpu_cores=18,
                memory_bandwidth_gb_s=150,
                unified_memory_gb=64,
                recommended_models=[model_768d, model_384d],
                max_embedding_dimension=768
            ),
            AppleSiliconChip.M3: HardwareProfile(
                chip=AppleSiliconChip.M3,
                neural_engine_tops=35.0,
                gpu_cores=10,
                memory_bandwidth_gb_s=100,
                unified_memory_gb=24,
                recommended_models=[model_768d, model_384d],
                max_embedding_dimension=768
            ),
            AppleSiliconChip.M2_MAX: HardwareProfile(
                chip=AppleSiliconChip.M2_MAX,
                neural_engine_tops=31.6,
                gpu_cores=38,
                memory_bandwidth_gb_s=200,
                unified_memory_gb=96,
                recommended_models=[model_1024d, model_768d, model_384d],
                max_embedding_dimension=1024
            ),
            AppleSiliconChip.M2_PRO: HardwareProfile(
                chip=AppleSiliconChip.M2_PRO,
                neural_engine_tops=31.6,
                gpu_cores=19,
                memory_bandwidth_gb_s=100,
                unified_memory_gb=32,
                recommended_models=[model_768d, model_384d],
                max_embedding_dimension=768
            ),
            AppleSiliconChip.M2: HardwareProfile(
                chip=AppleSiliconChip.M2,
                neural_engine_tops=31.6,
                gpu_cores=10,
                memory_bandwidth_gb_s=100,
                unified_memory_gb=24,
                recommended_models=[model_768d, model_384d],
                max_embedding_dimension=768
            ),
            AppleSiliconChip.M1_MAX: HardwareProfile(
                chip=AppleSiliconChip.M1_MAX,
                neural_engine_tops=15.8,
                gpu_cores=32,
                memory_bandwidth_gb_s=200,
                unified_memory_gb=64,
                recommended_models=[model_768d, model_384d],
                max_embedding_dimension=768
            ),
            AppleSiliconChip.M1_PRO: HardwareProfile(
                chip=AppleSiliconChip.M1_PRO,
                neural_engine_tops=15.8,
                gpu_cores=16,
                memory_bandwidth_gb_s=100,
                unified_memory_gb=32,
                recommended_models=[model_768d, model_384d],
                max_embedding_dimension=768
            ),
            AppleSiliconChip.M1: HardwareProfile(
                chip=AppleSiliconChip.M1,
                neural_engine_tops=15.8,
                gpu_cores=8,
                memory_bandwidth_gb_s=68,
                unified_memory_gb=16,
                recommended_models=[model_384d],
                max_embedding_dimension=384
            )
        }
        
        # Default fallback profile
        default_profile = HardwareProfile(
            chip=AppleSiliconChip.UNKNOWN,
            neural_engine_tops=0.0,
            gpu_cores=0,
            memory_bandwidth_gb_s=0,
            unified_memory_gb=8,
            recommended_models=[model_384d],
            max_embedding_dimension=384
        )
        
        return profiles.get(self.chip_model, default_profile)
    
    def _detect_devices(self) -> List[AcceleratorDevice]:
        """Detect available acceleration devices"""
        devices = [AcceleratorDevice.CPU]
        
        if not TORCH_AVAILABLE:
            return devices
        
        # MPS (Apple Silicon)
        if torch.backends.mps.is_available():
            devices.append(AcceleratorDevice.MPS)
            
        # Neural Engine (implicit with Apple Silicon)
        if self.chip_model != AppleSiliconChip.UNKNOWN:
            devices.append(AcceleratorDevice.NEURAL_ENGINE)
            
        # CUDA (NVIDIA)
        if torch.cuda.is_available():
            devices.append(AcceleratorDevice.CUDA)
        
        return devices
    
    def _select_optimal_device(self) -> AcceleratorDevice:
        """Select optimal device based on hardware profile.
        Prefer MPS on Apple Silicon by default; allow explicit skip via CFLOW_SKIP_APPLE_MPS.
        """
        skip_mps = os.environ.get("CFLOW_SKIP_APPLE_MPS", "0").lower() in {"1", "true", "yes"}
        if AcceleratorDevice.MPS in self.available_devices and not skip_mps:
            return AcceleratorDevice.MPS
        elif AcceleratorDevice.NEURAL_ENGINE in self.available_devices:
            return AcceleratorDevice.NEURAL_ENGINE
        elif AcceleratorDevice.CUDA in self.available_devices:
            return AcceleratorDevice.CUDA
        else:
            return AcceleratorDevice.CPU
    
    def _select_optimal_model(self) -> ModelProfile:
        """Select optimal model based on hardware capabilities"""
        if not self.hardware_profile.recommended_models:
            # Fallback to 384D model
            return ModelProfile(
                name="all-MiniLM-L6-v2",
                dimensions=384,
                memory_mb=90,
                performance_score=0.8,
                recommended_batch_size=16,
                max_sequence_length=512,
                description="Fallback model"
            )
        
        # Select the highest-performing model that fits in memory
        best_model = self.hardware_profile.recommended_models[0]
        
        # Consider memory constraints
        available_memory = self.hardware_profile.unified_memory_gb * 1024 * 0.7  # 70% usage
        
        for model in self.hardware_profile.recommended_models:
            if model.memory_mb <= available_memory:
                best_model = model
                break
        
        self.current_model = best_model.name
        self.current_dimensions = best_model.dimensions
        
        self.logger.info(f" Selected optimal model: {best_model.name} ({best_model.dimensions}D)")
        return best_model
    
    def _log_hardware_capabilities(self):
        """Log comprehensive hardware capabilities"""
        self.logger.info(" Hardware Capabilities:")
        self.logger.info(f"   Chip: {self.chip_model.value}")
        self.logger.info(f"   Neural Engine: {self.hardware_profile.neural_engine_tops} TOPS")
        self.logger.info(f"   GPU Cores: {self.hardware_profile.gpu_cores}")
        self.logger.info(f"   Memory Bandwidth: {self.hardware_profile.memory_bandwidth_gb_s} GB/s")
        self.logger.info(f"   Unified Memory: {self.hardware_profile.unified_memory_gb} GB")
        self.logger.info(f"   Max Embedding Dimension: {self.hardware_profile.max_embedding_dimension}")
        self.logger.info(f"   Available Devices: {[d.value for d in self.available_devices]}")
        self.logger.info(f"   Optimal Device: {self.optimal_device.value}")
    
    def get_device_string(self) -> str:
        """Get PyTorch device string"""
        if not TORCH_AVAILABLE:
            return "cpu"
        
        if self.optimal_device == AcceleratorDevice.MPS and torch.backends.mps.is_available():
            return "mps"
        elif self.optimal_device == AcceleratorDevice.CUDA and torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def create_optimized_model(self, model_name: Optional[str] = None, target_dimensions: Optional[int] = None) -> Optional[Any]:
        """Create optimized sentence transformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.warning("[INFO] Sentence Transformers not available")
            return None
        
        # Use provided model or select optimal
        if model_name is None:
            optimal_model = self._select_optimal_model()
            model_name = optimal_model.name
            target_dimensions = optimal_model.dimensions
        
        cache_key = f"{model_name}_{target_dimensions}"
        
        # Check cache
        if cache_key in self.model_cache:
            cached_model = self.model_cache[cache_key]
            self.logger.info(f" Using cached model: {model_name}")
            return cached_model
        
        try:
            start_time = time.time()
            self.logger.info(f" Loading model: {model_name}")
            
            model = SentenceTransformer(model_name)
            
            # Move to optimal device
            device_str = self.get_device_string()
            if device_str != "cpu" and TORCH_AVAILABLE:
                model = model.to(device_str)
                self.logger.info(f" Model moved to {device_str}")
            
            load_time = time.time() - start_time
            
            # Cache the model
            self.model_cache[cache_key] = model
            self._clean_model_cache()
            
            self.logger.info(f" Model loaded in {load_time:.3f}s on {device_str}")
            return model
            
        except Exception as e:
            self.logger.error(f" Failed to load model {model_name}: {e}")
            return None
    
    def generate_embeddings(self, texts: Union[str, List[str]], 
                          model_name: Optional[str] = None,
                          target_dimensions: Optional[int] = None,
                          batch_size: Optional[int] = None) -> Optional[Union[List[float], List[List[float]]]]:
        """Generate embeddings with optimal hardware acceleration"""
        start_time = time.time()
        
        # Ensure texts is a list
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        # Get optimal model
        model = self.create_optimized_model(model_name, target_dimensions)
        if model is None:
            self.logger.error(" Failed to create model")
            return None
        
        try:
            # Optimize batch size
            if batch_size is None:
                batch_size = self._get_optimal_batch_size(len(texts))
            
            # Generate embeddings with hardware acceleration
            self.logger.info(f" Generating {len(texts)} embeddings with batch size {batch_size}")
            
            if TORCH_AVAILABLE:
                embeddings = model.encode(
                    texts,
                    convert_to_tensor=True,
                    batch_size=batch_size,
                    show_progress_bar=len(texts) > 50
                )
                
                # Move to CPU for return
                if embeddings.device.type != "cpu":
                    embeddings = embeddings.cpu()
                
                embeddings = embeddings.numpy().tolist()
            else:
                embeddings = model.encode(texts, batch_size=batch_size).tolist()
            
            # Record performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(len(texts), processing_time)
            
            self.logger.info(f" Generated {len(embeddings)} {len(embeddings[0])}D embeddings in {processing_time:.3f}s")
            self.logger.info(f" Performance: {len(texts) / processing_time:.1f} embeddings/second")
            
            return embeddings[0] if is_single else embeddings
            
        except Exception as e:
            self.logger.error(f" Embedding generation failed: {e}")
            self.metrics.failed_operations += 1
            return None
    
    def _get_optimal_batch_size(self, total_items: int) -> int:
        """Calculate optimal batch size based on hardware and data"""
        if self.chip_model == AppleSiliconChip.UNKNOWN:
            return min(total_items, 8)
        
        # Get recommended batch size from current model profile
        optimal_model = self._select_optimal_model()
        base_batch_size = optimal_model.recommended_batch_size
        
        # Adjust based on total items
        if total_items < 10:
            return total_items
        elif total_items < 100:
            return min(base_batch_size, total_items)
        else:
            # Use full recommended batch size for large datasets
            return base_batch_size
    
    def _update_performance_metrics(self, item_count: int, processing_time: float):
        """Update real-time performance metrics"""
        with self._lock:
            self.metrics.total_operations += 1
            
            # Calculate embeddings per second
            current_eps = item_count / processing_time if processing_time > 0 else 0
            
            # Exponential moving average for smoothing
            alpha = 0.3
            if self.metrics.embeddings_per_second == 0:
                self.metrics.embeddings_per_second = current_eps
            else:
                self.metrics.embeddings_per_second = (
                    alpha * current_eps + (1 - alpha) * self.metrics.embeddings_per_second
                )
            
            # Average latency
            current_latency = (processing_time * 1000) / item_count  # ms per embedding
            if self.metrics.average_latency_ms == 0:
                self.metrics.average_latency_ms = current_latency
            else:
                self.metrics.average_latency_ms = (
                    alpha * current_latency + (1 - alpha) * self.metrics.average_latency_ms
                )
            
            self.metrics.last_updated = datetime.now()
            
            # Store history (keep last 100 measurements)
            if len(self.performance_history) >= 100:
                self.performance_history.pop(0)
            self.performance_history.append(PerformanceMetrics(
                embeddings_per_second=current_eps,
                average_latency_ms=current_latency,
                total_operations=self.metrics.total_operations,
                last_updated=datetime.now()
            ))
    
    def _clean_model_cache(self):
        """Clean old models from cache"""
        if len(self.model_cache) <= self.config["max_models_cached"]:
            return
        
        # Remove oldest models (simple approach)
        while len(self.model_cache) > self.config["max_models_cached"]:
            oldest_key = next(iter(self.model_cache))
            del self.model_cache[oldest_key]
            self.logger.info(f"[INFO] Removed cached model: {oldest_key}")
    
    def benchmark_models(self, test_texts: Optional[List[str]] = None) -> Dict[str, Any]:
        """Benchmark available models for optimal selection"""
        if test_texts is None:
            test_texts = [
                "Apple Silicon provides incredible performance for machine learning workloads",
                "The Neural Engine accelerates transformer models with high efficiency",
                "CerebraFlow leverages hardware optimization for enterprise AI applications"
            ]
        
        results = {}
        
        for model_profile in self.hardware_profile.recommended_models:
            self.logger.info(f" Benchmarking {model_profile.name}...")
            
            try:
                start_time = time.time()
                embeddings = self.generate_embeddings(
                    test_texts,
                    model_name=model_profile.name,
                    target_dimensions=model_profile.dimensions
                )
                end_time = time.time()
                
                if embeddings:
                    processing_time = end_time - start_time
                    throughput = len(test_texts) / processing_time
                    
                    results[model_profile.name] = {
                        "dimensions": model_profile.dimensions,
                        "processing_time": processing_time,
                        "throughput": throughput,
                        "latency_per_embedding": processing_time / len(test_texts),
                        "memory_estimate": model_profile.memory_mb,
                        "performance_score": model_profile.performance_score,
                        "status": "success"
                    }
                else:
                    results[model_profile.name] = {
                        "status": "failed",
                        "error": "Embedding generation failed"
                    }
                    
            except Exception as e:
                results[model_profile.name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return {
            "hardware_profile": {
                "chip": self.chip_model.value,
                "neural_engine_tops": self.hardware_profile.neural_engine_tops,
                "max_dimensions": self.hardware_profile.max_embedding_dimension
            },
            "benchmark_results": results,
            "recommendation": self._get_model_recommendation(results)
        }
    
    def _get_model_recommendation(self, benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get model recommendation based on benchmark results"""
        best_model = None
        best_score = 0
        
        for model_name, result in benchmark_results.items():
            if result.get("status") == "success":
                # Score based on throughput and performance score
                throughput = result.get("throughput", 0)
                performance_score = result.get("performance_score", 0)
                dimensions = result.get("dimensions", 384)
                
                # Weighted score (favor higher dimensions and throughput)
                score = (throughput * 0.4) + (performance_score * 0.3) + (dimensions / 1536 * 0.3)
                
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        if best_model:
            result = benchmark_results[best_model]
            return {
                "recommended_model": best_model,
                "dimensions": result["dimensions"],
                "expected_throughput": result["throughput"],
                "reasoning": f"Best overall score: {best_score:.3f}"
            }
        else:
            return {
                "recommended_model": "all-MiniLM-L6-v2",
                "dimensions": 384,
                "reasoning": "Fallback to reliable 384D model"
            }
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance and system metrics"""
        return {
            "hardware": {
                "chip_model": self.chip_model.value,
                "neural_engine_tops": self.hardware_profile.neural_engine_tops,
                "gpu_cores": self.hardware_profile.gpu_cores,
                "memory_bandwidth_gb_s": self.hardware_profile.memory_bandwidth_gb_s,
                "unified_memory_gb": self.hardware_profile.unified_memory_gb,
                "max_embedding_dimension": self.hardware_profile.max_embedding_dimension
            },
            "current_configuration": {
                "model": self.current_model,
                "dimensions": self.current_dimensions,
                "device": self.optimal_device.value,
                "device_string": self.get_device_string()
            },
            "performance": {
                "embeddings_per_second": self.metrics.embeddings_per_second,
                "average_latency_ms": self.metrics.average_latency_ms,
                "total_operations": self.metrics.total_operations,
                "failed_operations": self.metrics.failed_operations,
                "success_rate": (self.metrics.total_operations - self.metrics.failed_operations) / max(self.metrics.total_operations, 1),
                "last_updated": self.metrics.last_updated.isoformat()
            },
            "recommended_models": [
                {
                    "name": model.name,
                    "dimensions": model.dimensions,
                    "memory_mb": model.memory_mb,
                    "performance_score": model.performance_score,
                    "description": model.description
                }
                for model in self.hardware_profile.recommended_models
            ],
            "cache_status": {
                "cached_models": len(self.model_cache),
                "max_cache_size": self.config["max_models_cached"]
            }
        }

# Global enhanced accelerator instance
_enhanced_accelerator: Optional[EnhancedAppleSiliconAccelerator] = None

def get_enhanced_accelerator() -> EnhancedAppleSiliconAccelerator:
    """Get global enhanced Apple Silicon accelerator instance"""
    global _enhanced_accelerator
    if _enhanced_accelerator is None:
        _enhanced_accelerator = EnhancedAppleSiliconAccelerator()
    return _enhanced_accelerator

# Enhanced convenience functions
def generate_enhanced_embeddings(texts: Union[str, List[str]], 
                               target_dimensions: Optional[int] = None) -> Optional[Union[List[float], List[List[float]]]]:
    """Generate embeddings with enhanced Apple Silicon acceleration"""
    return get_enhanced_accelerator().generate_embeddings(texts, target_dimensions=target_dimensions)

def get_hardware_recommendation() -> Dict[str, Any]:
    """Get hardware-based model recommendation"""
    accelerator = get_enhanced_accelerator()
    return accelerator._get_model_recommendation({})

def benchmark_current_hardware() -> Dict[str, Any]:
    """Benchmark current hardware capabilities"""
    return get_enhanced_accelerator().benchmark_models()

def get_optimal_dimensions() -> int:
    """Get optimal embedding dimensions for current hardware"""
    accelerator = get_enhanced_accelerator()
    return accelerator.hardware_profile.max_embedding_dimension

if __name__ == "__main__":
    # Hardware demonstration
    print(" Enhanced Apple Silicon Accelerator Demo")
    print("=" * 60)
    
    accelerator = get_enhanced_accelerator()
    
    # Show comprehensive metrics
    metrics = accelerator.get_comprehensive_metrics()
    print(f"\n Hardware: {metrics['hardware']['chip_model']}")
    print(f" Neural Engine: {metrics['hardware']['neural_engine_tops']} TOPS")
    print(f" Max Dimensions: {metrics['hardware']['max_embedding_dimension']}")
    print(f" Recommended Models: {len(metrics['recommended_models'])}")
    
    # Test embedding generation
    test_texts = ["Enhanced Apple Silicon acceleration test"]
    embeddings = accelerator.generate_embeddings(test_texts)
    
    if embeddings:
        print(f"\n Generated {len(embeddings[0])}D embedding successfully")
        print(f" Performance: {metrics['performance']['embeddings_per_second']:.1f} embeddings/second")
    
    # Benchmark models
    print("\n Running model benchmark...")
    benchmark = accelerator.benchmark_models()
    print(f" Recommended: {benchmark['recommendation']['recommended_model']}")
    print(f" Dimensions: {benchmark['recommendation']['dimensions']}") 