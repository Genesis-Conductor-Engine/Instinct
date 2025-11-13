# Task 080: CUDA/GPU Support

## Goal

Add optional CUDA support for GPU-accelerated operations in compute-intensive pipeline stages (alignment, arbiter training, embedding generation).

## Files to Create/Edit

### New Files
- `src/cuda/__init__.py` - CUDA utilities package
- `src/cuda/device_manager.py` - GPU device management and selection
- `src/cuda/accelerated_ops.py` - GPU-accelerated operations
- `tests/cuda/test_device_manager.py` - Tests for device management
- `docker/Dockerfile.cuda` - Docker image with CUDA support
- `.github/workflows/cuda-tests.yml` - CI workflow for CUDA tests

### Files to Modify
- `src/alignment/procrustes.py` - Add GPU acceleration option
- `src/models/arbiter.py` - Add GPU training support
- `requirements.txt` - Add optional CUDA dependencies
- `README.md` - Add CUDA setup instructions

## Requirements

### Functional Requirements

1. **Device Management**
   - Auto-detect available GPUs
   - Select GPU based on CUDA_VISIBLE_DEVICES
   - Fallback to CPU if CUDA unavailable
   - Memory management and cleanup

2. **Accelerated Operations**
   - GPU-accelerated matrix operations for alignment
   - GPU training for ensemble models
   - Batch processing on GPU
   - Efficient data transfer between CPU/GPU

3. **Optional Dependency**
   - CUDA is optional, not required
   - Graceful degradation to CPU
   - Clear error messages if CUDA unavailable
   - No performance impact when using CPU

4. **Configuration**
   - Environment variable for GPU selection
   - Memory limit configuration
   - Batch size optimization for GPU
   - Mixed precision training option

### Non-Functional Requirements

1. **Performance**
   - ≥3x speedup for large matrix operations
   - ≥5x speedup for model training
   - Efficient memory usage (avoid OOM)
   - Minimize CPU-GPU transfer overhead

2. **Compatibility**
   - Support CUDA 11.8+
   - Compatible with common GPU types (V100, A100, T4)
   - Works with both single and multi-GPU setups
   - Docker image with CUDA runtime

### Acceptance Criteria
- [ ] Device manager detects and selects GPUs
- [ ] Fallback to CPU works correctly
- [ ] GPU-accelerated alignment implemented
- [ ] GPU model training working
- [ ] Docker image with CUDA support
- [ ] CI tests for CUDA (on GPU runners)
- [ ] Documentation for CUDA setup
- [ ] Performance benchmarks documented

## Implementation Guidance

```python
# src/cuda/device_manager.py
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    CUDA_AVAILABLE = False
    logger.info("PyTorch not installed, CUDA support disabled")

class DeviceManager:
    """Manage GPU/CPU device selection"""
    
    def __init__(self):
        self.device = self._select_device()
        
    def _select_device(self) -> str:
        """Select best available device"""
        if not CUDA_AVAILABLE:
            logger.info("CUDA not available, using CPU")
            return "cpu"
        
        # Check CUDA_VISIBLE_DEVICES
        visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        if visible_devices == "":
            # Use first available GPU
            device = "cuda:0"
        else:
            device = f"cuda:{visible_devices.split(',')[0]}"
        
        logger.info(f"Using device: {device}")
        return device
    
    def get_device(self) -> str:
        """Get current device"""
        return self.device
    
    def is_cuda(self) -> bool:
        """Check if using CUDA"""
        return self.device.startswith("cuda")
    
    def get_memory_info(self) -> Optional[dict]:
        """Get GPU memory information"""
        if not self.is_cuda():
            return None
        
        import torch
        device_id = int(self.device.split(":")[-1])
        
        return {
            "allocated": torch.cuda.memory_allocated(device_id),
            "reserved": torch.cuda.memory_reserved(device_id),
            "total": torch.cuda.get_device_properties(device_id).total_memory
        }
```

```python
# Modified src/alignment/procrustes.py
class ProcrustesAlignment(AlignmentMethod):
    def __init__(self, scaling: bool = False, use_cuda: bool = False):
        self.scaling = scaling
        self.use_cuda = use_cuda and CUDA_AVAILABLE
        self.device_manager = DeviceManager() if self.use_cuda else None
        
    def fit(self, X_source: np.ndarray, X_target: np.ndarray):
        if self.use_cuda:
            return self._fit_cuda(X_source, X_target)
        else:
            return self._fit_cpu(X_source, X_target)
    
    def _fit_cuda(self, X_source, X_target):
        """GPU-accelerated Procrustes alignment"""
        import torch
        device = self.device_manager.get_device()
        
        # Convert to torch tensors on GPU
        X_src = torch.from_numpy(X_source).float().to(device)
        X_tgt = torch.from_numpy(X_target).float().to(device)
        
        # Center on GPU
        X_src_centered = X_src - X_src.mean(dim=0)
        X_tgt_centered = X_tgt - X_tgt.mean(dim=0)
        
        # SVD on GPU
        U, _, Vt = torch.linalg.svd(X_src_centered.T @ X_tgt_centered)
        self.rotation_matrix = (U @ Vt).cpu().numpy()
        
        return self
```

## Docker Configuration

```dockerfile
# docker/Dockerfile.cuda
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.11 python3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install torch --index-url https://download.pytorch.org/whl/cu118

COPY . .

CMD ["python3", "-m", "src.main"]
```

## GitHub Actions Workflow

```yaml
# .github/workflows/cuda-tests.yml
name: CUDA Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  gpu-tests:
    # NOTE: Update with actual large runner label from GitHub docs
    # Example: ubuntu-22.04-16core-gpu or similar
    runs-on: ubuntu-latest  # TODO: Replace with GPU runner label
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Check CUDA availability
        run: nvidia-smi
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install torch --index-url https://download.pytorch.org/whl/cu118
          
      - name: Run GPU tests
        env:
          CUDA_VISIBLE_DEVICES: 0
        run: |
          pytest tests/cuda/ -v -m gpu
```

## Configuration

```yaml
# Environment variables
CUDA_VISIBLE_DEVICES: "0"  # GPU device ID
CUDA_MEMORY_LIMIT: "8GB"  # Optional memory limit
USE_CUDA: "true"  # Enable CUDA acceleration
```

## Performance Benchmarks

Document expected speedups:
- Matrix operations (10K x 512): 3-5x faster
- Model training (ensemble): 5-10x faster
- Batch alignment (1000 CVEs): 4-6x faster

## References
- NVIDIA CUDA Toolkit: https://developer.nvidia.com/cuda-toolkit
- PyTorch CUDA: https://pytorch.org/docs/stable/cuda.html
- cuBLAS for linear algebra: https://docs.nvidia.com/cuda/cublas/
