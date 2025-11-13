# Task 040: Epsilon-Refractors for Distributional Shift Detection

## Goal

Implement epsilon-refractor mechanisms to detect distributional shifts in vulnerability patterns, enabling early warning of emerging threat landscapes.

## Files to Create/Edit

### New Files
- `src/refractors/__init__.py` - Package initialization
- `src/refractors/epsilon.py` - Epsilon-refractor implementation
- `src/refractors/shifts.py` - Shift detection algorithms
- `src/refractors/metrics.py` - Divergence metrics (KL, JS, etc.)
- `tests/refractors/__init__.py` - Test package initialization
- `tests/refractors/test_epsilon.py` - Tests for epsilon-refractor
- `tests/refractors/test_shifts.py` - Tests for shift detection

### Supporting Files
- `requirements.txt` - Add `scipy` for statistical functions
- `config/thresholds.yaml` - Alert thresholds configuration

## Requirements

### Functional Requirements

1. **Epsilon-Divergence Calculation**
   - Calculate ε-divergence between distributions
   - Support multiple divergence metrics: KL, JS, Wasserstein
   - Configurable epsilon threshold (default: 0.05)
   - Per-feature and global divergence measures

2. **Shift Detection**
   - Detect concept drift (changes in P(Y|X))
   - Detect data drift (changes in P(X))
   - Sliding window approach for temporal monitoring
   - Statistical significance testing

3. **Alert Generation**
   - Trigger alerts when ε exceeds threshold
   - Classify shift severity (low, medium, high)
   - Identify which features/dimensions shifted most
   - Provide actionable diagnostics

4. **Reference Distribution Management**
   - Store reference distributions for comparison
   - Update reference distributions periodically
   - Support multiple reference periods

### Acceptance Criteria
- [ ] Epsilon-refractor calculates divergence correctly
- [ ] Shift detection working with synthetic drift
- [ ] Alert thresholds configurable
- [ ] Per-feature drift attribution
- [ ] Statistical significance tests implemented
- [ ] Tests achieve >80% coverage
- [ ] Docstrings for all public APIs

## Implementation Guidance

```python
import numpy as np
from scipy.stats import entropy, wasserstein_distance

class EpsilonRefractor:
    """Detect distributional shifts using epsilon-divergence"""
    
    def __init__(self, threshold: float = 0.05, metric: str = 'kl'):
        self.threshold = threshold
        self.metric = metric
        self.reference_dist = None
        
    def fit(self, X_reference: np.ndarray):
        """Establish reference distribution"""
        self.reference_dist = self._estimate_distribution(X_reference)
        
    def detect(self, X_current: np.ndarray) -> Dict:
        """Detect shifts in current data"""
        current_dist = self._estimate_distribution(X_current)
        epsilon = self._calculate_divergence(self.reference_dist, current_dist)
        
        alert = epsilon > self.threshold
        
        return {
            'epsilon': epsilon,
            'alert': alert,
            'severity': self._classify_severity(epsilon),
            'shifted_features': self._identify_shifted_features(X_current)
        }
        
    def _calculate_divergence(self, p, q):
        """Calculate divergence between distributions"""
        if self.metric == 'kl':
            return entropy(p, q)
        elif self.metric == 'js':
            m = 0.5 * (p + q)
            return 0.5 * entropy(p, m) + 0.5 * entropy(q, m)
        elif self.metric == 'wasserstein':
            return wasserstein_distance(p, q)
```

## Configuration

```yaml
refractors:
  epsilon_threshold: 0.05
  divergence_metric: kl  # or js, wasserstein
  window_size: 1000  # samples for drift detection
  alert_severity:
    low: 0.05
    medium: 0.10
    high: 0.20
```

## References
- Dasu, T. et al. (2006). "An information-theoretic approach to detecting changes in multi-dimensional data streams"
- Rabanser, S. et al. (2019). "Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift"
