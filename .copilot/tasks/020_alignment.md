# Task 020: Positional Alignment

## Goal

Implement positional alignment methods to align vulnerability representations across different embedding spaces, enabling comparison of vulnerabilities from different sources or time periods.

## Files to Create/Edit

### New Files
- `src/alignment/__init__.py` - Package initialization with public API
- `src/alignment/procrustes.py` - Procrustes alignment implementation
- `src/alignment/cca.py` - Canonical Correlation Analysis implementation
- `src/alignment/base.py` - Base class for alignment methods
- `tests/alignment/__init__.py` - Test package initialization
- `tests/alignment/test_procrustes.py` - Tests for Procrustes alignment
- `tests/alignment/test_cca.py` - Tests for CCA
- `tests/alignment/test_integration.py` - Integration tests

### Supporting Files
- `requirements.txt` - Add `numpy`, `scipy`, `scikit-learn`
- `src/alignment/metrics.py` - Alignment quality metrics (optional)

## Requirements

### Functional Requirements

1. **Procrustes Alignment**
   - Implement orthogonal Procrustes analysis for shape matching
   - Find optimal rotation matrix R that minimizes ||R·Xa - Xb||²
   - Support both orthogonal and scaled Procrustes
   - Return transformation matrix and alignment quality (R²)

2. **Canonical Correlation Analysis (CCA)**
   - Implement CCA to find linear relationships between two embedding spaces
   - Maximize correlation between projected spaces
   - Support regularization for high-dimensional data
   - Return projection matrices and canonical correlations

3. **Alignment Quality Metrics**
   - Calculate R² (coefficient of determination) for alignment quality
   - Require alignment_R2 ≥ configured threshold (default 0.8)
   - Calculate residual error after alignment
   - Provide per-dimension alignment scores

4. **Public API**
   - Expose unified `align(X_a, X_b, method='procrustes') -> (R2, X_a2b)` function
   - Support method selection: 'procrustes', 'cca', or 'auto'
   - Return aligned embeddings and quality metrics
   - Raise exception if alignment quality below threshold

5. **Reference Space Management**
   - Support loading pre-computed reference embeddings
   - Enable aligning new data to reference space
   - Cache transformation matrices for repeated alignment

### Non-Functional Requirements

1. **Performance**
   - Handle embedding matrices up to 10,000 x 512 dimensions
   - Alignment computation <1 second for typical input sizes
   - Memory-efficient implementation for large matrices

2. **Numerical Stability**
   - Handle ill-conditioned matrices gracefully
   - Use SVD-based methods for robustness
   - Validate input data for NaN/Inf values

3. **Configurability**
   - Allow setting R² threshold via configuration
   - Support different alignment methods
   - Enable regularization parameters for CCA

4. **Observability**
   - Log alignment quality metrics
   - Warn when alignment quality is marginal
   - Provide diagnostic information for failed alignments

## Implementation Guidance

### Base Class

```python
from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple

class AlignmentMethod(ABC):
    """Base class for alignment methods"""
    
    @abstractmethod
    def fit(self, X_source: np.ndarray, X_target: np.ndarray) -> 'AlignmentMethod':
        """Fit alignment transformation from source to target"""
        
    @abstractmethod
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply learned transformation to new data"""
        
    @abstractmethod
    def fit_transform(self, X_source: np.ndarray, X_target: np.ndarray) -> Tuple[np.ndarray, float]:
        """Fit and transform in one step, return aligned data and R²"""
```

### Procrustes Implementation

```python
import numpy as np
from scipy.linalg import orthogonal_procrustes
from typing import Tuple

class ProcrustesAlignment(AlignmentMethod):
    """Orthogonal Procrustes alignment"""
    
    def __init__(self, scaling: bool = False):
        self.scaling = scaling
        self.rotation_matrix = None
        self.scale_factor = None
        
    def fit(self, X_source: np.ndarray, X_target: np.ndarray) -> 'ProcrustesAlignment':
        """
        Fit Procrustes alignment.
        
        Args:
            X_source: Source embeddings (n_samples, n_features)
            X_target: Target embeddings (n_samples, n_features)
            
        Returns:
            self
        """
        # Center the data
        X_source_centered = X_source - X_source.mean(axis=0)
        X_target_centered = X_target - X_target.mean(axis=0)
        
        # Compute optimal rotation matrix using SVD
        self.rotation_matrix, _ = orthogonal_procrustes(X_source_centered, X_target_centered)
        
        if self.scaling:
            # Compute optimal scale factor
            X_aligned = X_source_centered @ self.rotation_matrix
            self.scale_factor = np.trace(X_target_centered.T @ X_aligned) / np.trace(X_aligned.T @ X_aligned)
        else:
            self.scale_factor = 1.0
            
        return self
        
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply learned transformation"""
        if self.rotation_matrix is None:
            raise ValueError("Must call fit() before transform()")
            
        X_centered = X - X.mean(axis=0)
        X_aligned = self.scale_factor * (X_centered @ self.rotation_matrix)
        return X_aligned
        
    def fit_transform(self, X_source: np.ndarray, X_target: np.ndarray) -> Tuple[np.ndarray, float]:
        """Fit and transform, return aligned data and R²"""
        self.fit(X_source, X_target)
        X_aligned = self.transform(X_source)
        
        # Calculate R²
        r2 = calculate_r2(X_aligned, X_target)
        
        return X_aligned, r2
```

### CCA Implementation

```python
from sklearn.cross_decomposition import CCA as SklearnCCA

class CCAAlignment(AlignmentMethod):
    """Canonical Correlation Analysis alignment"""
    
    def __init__(self, n_components: int = None, regularization: float = 0.0):
        self.n_components = n_components
        self.regularization = regularization
        self.cca = None
        
    def fit(self, X_source: np.ndarray, X_target: np.ndarray) -> 'CCAAlignment':
        """Fit CCA alignment"""
        n_components = self.n_components or min(X_source.shape[1], X_target.shape[1])
        
        # Use sklearn CCA with regularization
        self.cca = SklearnCCA(n_components=n_components, max_iter=500)
        self.cca.fit(X_source, X_target)
        
        return self
        
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply CCA transformation"""
        if self.cca is None:
            raise ValueError("Must call fit() before transform()")
            
        return self.cca.transform(X)
        
    def fit_transform(self, X_source: np.ndarray, X_target: np.ndarray) -> Tuple[np.ndarray, float]:
        """Fit and transform, return aligned data and R²"""
        self.fit(X_source, X_target)
        X_aligned = self.transform(X_source)
        Y_aligned = self.cca.transform(X_target)
        
        # Calculate R² using canonical correlations
        r2 = calculate_r2(X_aligned, Y_aligned)
        
        return X_aligned, r2
```

### Public API

```python
def align(
    X_source: np.ndarray,
    X_target: np.ndarray,
    method: str = 'procrustes',
    threshold: float = 0.8,
    **kwargs
) -> Tuple[float, np.ndarray]:
    """
    Align source embeddings to target space.
    
    Args:
        X_source: Source embeddings (n_samples, n_features)
        X_target: Target embeddings (n_samples, n_features)
        method: Alignment method ('procrustes', 'cca', 'auto')
        threshold: Minimum acceptable R² (default: 0.8)
        **kwargs: Additional arguments for alignment method
        
    Returns:
        Tuple of (R², X_aligned)
        
    Raises:
        AlignmentError: If alignment quality below threshold
    """
    if method == 'procrustes':
        aligner = ProcrustesAlignment(**kwargs)
    elif method == 'cca':
        aligner = CCAAlignment(**kwargs)
    elif method == 'auto':
        # Try Procrustes first, fall back to CCA if needed
        aligner = ProcrustesAlignment(**kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
        
    X_aligned, r2 = aligner.fit_transform(X_source, X_target)
    
    if r2 < threshold:
        raise AlignmentError(
            f"Alignment quality R²={r2:.3f} below threshold {threshold:.3f}"
        )
        
    return r2, X_aligned
```

### Metrics

```python
def calculate_r2(X_pred: np.ndarray, X_true: np.ndarray) -> float:
    """
    Calculate R² (coefficient of determination).
    
    R² = 1 - (SS_res / SS_tot)
    where SS_res = sum of squared residuals
          SS_tot = total sum of squares
    """
    # Center the data
    X_true_centered = X_true - X_true.mean(axis=0)
    
    # Calculate residuals
    residuals = X_pred - X_true
    
    # Sum of squared residuals
    ss_res = np.sum(residuals ** 2)
    
    # Total sum of squares
    ss_tot = np.sum(X_true_centered ** 2)
    
    # R²
    r2 = 1 - (ss_res / ss_tot)
    
    return r2
```

## Acceptance Criteria

### Implementation
- [ ] `ProcrustesAlignment` class implemented with fit/transform/fit_transform
- [ ] `CCAAlignment` class implemented with fit/transform/fit_transform
- [ ] `align()` public API function working with all methods
- [ ] R² calculation implemented correctly
- [ ] Alignment quality threshold checking working
- [ ] Input validation for NaN/Inf values
- [ ] Proper error handling and exceptions

### Testing
- [ ] Unit tests for Procrustes alignment with known transformations
- [ ] Unit tests for CCA alignment
- [ ] Test R² calculation with simple examples
- [ ] Test threshold enforcement (should raise exception)
- [ ] Test with various matrix sizes and dimensions
- [ ] Test numerical stability (ill-conditioned matrices)
- [ ] Integration test aligning real embedding data
- [ ] Tests achieve >80% code coverage

### Documentation
- [ ] Docstrings for all public classes and methods
- [ ] Usage examples in module docstring
- [ ] Mathematical background documented
- [ ] Configuration options documented
- [ ] Error conditions documented

### Quality
- [ ] Code passes flake8 linting
- [ ] Code passes black formatting
- [ ] Code passes mypy type checking
- [ ] No hardcoded thresholds (use configuration)
- [ ] All dependencies added to requirements.txt

## Validation Steps

1. **Unit Tests**
   ```bash
   pytest tests/alignment/ -v --cov=src.alignment --cov-report=term-missing
   ```

2. **Manual Testing**
   ```python
   from src.alignment import align
   import numpy as np
   
   # Create sample embeddings
   X_source = np.random.randn(100, 128)
   X_target = np.random.randn(100, 128)
   
   # Align using Procrustes
   r2, X_aligned = align(X_source, X_target, method='procrustes')
   print(f"Procrustes R²: {r2:.3f}")
   
   # Align using CCA
   r2, X_aligned = align(X_source, X_target, method='cca')
   print(f"CCA R²: {r2:.3f}")
   ```

3. **Integration Test**
   - Generate synthetic embeddings with known transformation
   - Apply Procrustes alignment
   - Verify recovered transformation matches original
   - Verify R² > 0.95 for perfectly aligned data

4. **Quality Checks**
   ```bash
   black src/alignment/ tests/alignment/
   flake8 src/alignment/ tests/alignment/
   mypy src/alignment/
   ```

## Dependencies

### Python Packages
- `numpy>=1.24.0` - Array operations
- `scipy>=1.10.0` - Procrustes and linear algebra
- `scikit-learn>=1.3.0` - CCA implementation

### Internal Dependencies
- None (this is a foundational module)

## Configuration

Add to config file or environment:
```yaml
alignment:
  default_method: procrustes
  r2_threshold: 0.8
  cca_n_components: null  # auto-detect
  cca_regularization: 0.0
```

## Notes

- **Procrustes vs CCA**: Procrustes is faster and works well for similar spaces; CCA better for finding latent correlations
- **R² Threshold**: 0.8 is a reasonable default; adjust based on use case
- **Dimensionality**: CCA requires n_samples > n_features; use regularization if needed
- **Centering**: Both methods require centering data for best results

## References

- Goodall, C. (1991). "Procrustes methods in the statistical analysis of shape"
- Hotelling, H. (1936). "Relations between two sets of variates"
- Scipy orthogonal_procrustes: https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.orthogonal_procrustes.html
- Scikit-learn CCA: https://scikit-learn.org/stable/modules/generated/sklearn.cross_decomposition.CCA.html

## Related Tasks

- **Task 010**: NVD ingestion (provides CVE data to embed)
- **Task 030**: Arbiter (consumes aligned embeddings)
- **Task 040**: Refractors (may use alignment metrics for shift detection)
