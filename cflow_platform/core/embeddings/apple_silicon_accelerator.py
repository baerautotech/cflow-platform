from __future__ import annotations

"""
CerebraFlow Unified Apple Silicon Accelerator (core)

Ported from Cerebral backend-python/shared/apple_silicon_accelerator.py with logging sanitized
and no vendor references. Provides Apple Silicon acceleration with graceful fallbacks.
"""

import logging
import os
import platform
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import torch  # type: ignore
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - Apple Silicon acceleration disabled")

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("Sentence Transformers not available")

try:
    import numpy as np  # type: ignore
    NUMPY_AVAILABLE = True
except Exception:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available")


class AcceleratorDevice(Enum):
    NEURAL_ENGINE = "neural_engine"
    MPS = "mps"
    CUDA = "cuda"
    CPU = "cpu"


@dataclass
class AcceleratorMetrics:
    device: str
    total_operations: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    operations_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    batch_size_optimized: int = 1
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ModelCache:
    model: Any
    device: str
    load_time: float
    last_used: datetime
    usage_count: int = 0
    memory_mb: float = 0.0


class CerebraFlowAppleSiliconAccelerator:
    def __init__(self) -> None:
        self.logger = logging.getLogger("CerebraFlow.AppleSilicon")
        self.system_info = self._detect_system()
        self.available_devices = self._detect_devices()
        self.optimal_device = self._select_optimal_device()
        self.metrics: Dict[str, AcceleratorMetrics] = {}
        self.model_cache: Dict[str, ModelCache] = {}
        self.config = {
            "max_models_cached": 5,
            "cache_timeout_minutes": 30,
            "batch_size_optimization": True,
            "memory_optimization": True,
            "performance_monitoring": True,
        }
        self._lock = threading.Lock()
        self.logger.info("CerebraFlow Apple Silicon Accelerator initialized")
        self._log_system_capabilities()

    def _detect_system(self) -> Dict[str, Any]:
        info = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_apple_silicon": False,
            "neural_engine_available": False,
            "chip_model": "unknown",
        }
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            info["is_apple_silicon"] = True
            info["neural_engine_available"] = True
            try:
                import subprocess
                result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
                if result.returncode == 0:
                    chip = result.stdout.strip()
                    for tag in ("M4", "M3", "M2", "M1"):
                        if tag in chip:
                            info["chip_model"] = tag
                            break
            except Exception:
                pass
        return info

    def _detect_devices(self) -> List[AcceleratorDevice]:
        devices = [AcceleratorDevice.CPU]
        if not TORCH_AVAILABLE:
            return devices
        if self.system_info["neural_engine_available"]:
            devices.append(AcceleratorDevice.NEURAL_ENGINE)
        if torch.backends.mps.is_available():  # type: ignore[attr-defined]
            devices.append(AcceleratorDevice.MPS)
        if hasattr(torch, "cuda") and torch.cuda.is_available():  # type: ignore[attr-defined]
            devices.append(AcceleratorDevice.CUDA)
        return devices

    def _select_optimal_device(self) -> AcceleratorDevice:
        if AcceleratorDevice.NEURAL_ENGINE in self.available_devices:
            return AcceleratorDevice.NEURAL_ENGINE
        if AcceleratorDevice.MPS in self.available_devices:
            return AcceleratorDevice.MPS
        if AcceleratorDevice.CUDA in self.available_devices:
            return AcceleratorDevice.CUDA
        return AcceleratorDevice.CPU

    def _log_system_capabilities(self) -> None:
        self.logger.info("System Capabilities:")
        self.logger.info(f"  Platform: {self.system_info['platform']}")
        self.logger.info(f"  Machine: {self.system_info['machine']}")
        if self.system_info["is_apple_silicon"]:
            self.logger.info(f"  Apple Silicon: {self.system_info['chip_model']}")
            self.logger.info("  Neural Engine: Available")
        else:
            self.logger.info("  Apple Silicon: Not available")
        self.logger.info(f"  Available devices: {[d.value for d in self.available_devices]}")
        self.logger.info(f"  Optimal device: {self.optimal_device.value}")

    def get_device_string(self) -> str:
        if not TORCH_AVAILABLE:
            return "cpu"
        if self.optimal_device == AcceleratorDevice.MPS and torch.backends.mps.is_available():  # type: ignore[attr-defined]
            return "mps"
        if self.optimal_device == AcceleratorDevice.CUDA and torch.cuda.is_available():  # type: ignore[attr-defined]
            return "cuda"
        return "cpu"

    def create_sentence_transformer(self, model_name: str = "all-MiniLM-L6-v2") -> Optional[Any]:
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.warning("Sentence Transformers not available - returning None")
            return None
        cache_key = f"sentence_transformer_{model_name}"
        if cache_key in self.model_cache:
            mc = self.model_cache[cache_key]
            mc.last_used = datetime.now()
            mc.usage_count += 1
            self.logger.info(f"Using cached sentence transformer: {model_name}")
            return mc.model
        start_time = time.time()
        try:
            model = SentenceTransformer(model_name)  # type: ignore[name-defined]
            device_str = self.get_device_string()
            if device_str != "cpu":
                model = model.to(device_str)
                self.logger.info(f"Model moved to {device_str}")
            load_time = time.time() - start_time
            self.model_cache[cache_key] = ModelCache(
                model=model,
                device=device_str,
                load_time=load_time,
                last_used=datetime.now(),
            )
            self._clean_model_cache()
            self.logger.info(f"Sentence transformer loaded in {load_time:.3f}s on {device_str}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load sentence transformer: {e}")
            return None

    def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: Optional[int] = None,
    ) -> Optional[Union[List[float], List[List[float]]]]:
        start_time = time.time()
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        model = self.create_sentence_transformer(model_name)
        if model is None:
            if NUMPY_AVAILABLE:
                return [np.random.uniform(-1, 1, 384).tolist() for _ in texts]  # type: ignore[name-defined]
            return [[0.0] * 384 for _ in texts]
        try:
            if batch_size is None:
                batch_size = self._get_optimal_batch_size(len(texts))
            if TORCH_AVAILABLE:
                embeddings = model.encode(texts, convert_to_tensor=True, batch_size=batch_size)
                if embeddings.device.type != "cpu":
                    embeddings = embeddings.cpu()
                embeddings = embeddings.numpy().tolist()
            else:
                embeddings = model.encode(texts, batch_size=batch_size).tolist()
            processing_time = time.time() - start_time
            self._record_metrics("embeddings", len(texts), processing_time)
            return embeddings[0] if is_single else embeddings
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return None

    def _get_optimal_batch_size(self, total_items: int) -> int:
        if self.optimal_device == AcceleratorDevice.MPS:
            if total_items < 10:
                return total_items
            if total_items < 100:
                return 32
            if total_items < 1000:
                return 64
            return 128
        if self.optimal_device == AcceleratorDevice.CUDA:
            return min(total_items, 256)
        return min(total_items, 16)

    def _record_metrics(self, op: str, n: int, t: float) -> None:
        if not self.config.get("performance_monitoring", True):
            return
        with self._lock:
            if op not in self.metrics:
                self.metrics[op] = AcceleratorMetrics(device=self.optimal_device.value)
            m = self.metrics[op]
            m.total_operations += 1
            m.total_time += t
            m.average_time = m.total_time / m.total_operations
            m.operations_per_second = n / t if t > 0 else 0.0
            m.last_updated = datetime.now()

    def _clean_model_cache(self) -> None:
        if len(self.model_cache) <= self.config["max_models_cached"]:
            return
        items = list(self.model_cache.items())
        items.sort(key=lambda x: x[1].last_used)
        while len(self.model_cache) > self.config["max_models_cached"]:
            oldest = items.pop(0)[0]
            del self.model_cache[oldest]
            self.logger.info(f"Removed cached model: {oldest}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        return {
            "system_info": self.system_info,
            "available_devices": [d.value for d in self.available_devices],
            "optimal_device": self.optimal_device.value,
            "metrics": {
                k: {
                    "device": v.device,
                    "total_operations": v.total_operations,
                    "average_time": v.average_time,
                    "operations_per_second": v.operations_per_second,
                    "last_updated": v.last_updated.isoformat(),
                }
                for k, v in self.metrics.items()
            },
            "cached_models": len(self.model_cache),
            "config": self.config,
        }


_global_accel: Optional[CerebraFlowAppleSiliconAccelerator] = None


def get_apple_silicon_accelerator() -> CerebraFlowAppleSiliconAccelerator:
    global _global_accel
    if _global_accel is None:
        _global_accel = CerebraFlowAppleSiliconAccelerator()
    return _global_accel


def create_accelerated_sentence_transformer(model_name: str = "all-MiniLM-L6-v2") -> Optional[Any]:
    return get_apple_silicon_accelerator().create_sentence_transformer(model_name)


def generate_accelerated_embeddings(
    texts: Union[str, List[str]], model_name: str = "all-MiniLM-L6-v2"
) -> Optional[Union[List[float], List[List[float]]]]:
    return get_apple_silicon_accelerator().generate_embeddings(texts, model_name)


