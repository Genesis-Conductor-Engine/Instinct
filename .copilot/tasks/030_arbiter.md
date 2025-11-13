# Task 030: Stacked Arbiter with Pareto Knee Detection

## Goal

Implement a stacked ensemble learning system (arbiter) for vulnerability severity prediction with multi-objective optimization and Pareto knee detection.

## Files to Create/Edit

### New Files
- `src/models/__init__.py` - Package initialization
- `src/models/arbiter.py` - Stacked arbiter implementation
- `src/models/base_learners.py` - Base learner configurations
- `src/models/pareto.py` - Pareto frontier and knee detection
- `tests/models/__init__.py` - Test package initialization
- `tests/models/test_arbiter.py` - Tests for arbiter
- `tests/models/test_pareto.py` - Tests for Pareto detection

### Supporting Files
- `requirements.txt` - Add `scikit-learn`, `xgboost`, `lightgbm` (optional)
- `config/models.yaml` - Model hyperparameters configuration

## Requirements

### Functional Requirements

1. **Stacked Ensemble Architecture**
   - Multiple base learners (Level 0): RandomForest, GradientBoosting, etc.
   - Meta-learner (Level 1): LogisticRegression or another model
   - Support for classification (severity levels) and regression (CVSS scores)
   - Out-of-fold predictions for meta-learner training

2. **Pareto Optimization**
   - Multi-objective optimization (e.g., accuracy vs inference time)
   - Calculate Pareto frontier across model configurations
   - Detect Pareto knee (optimal trade-off point)
   - Support custom objective functions

3. **Predictions and Confidence**
   - Severity predictions with confidence scores
   - Feature importance from ensemble
   - Support for probability estimates
   - Calibrated predictions

4. **Model Management**
   - Save and load trained models
   - Version control for models
   - Support for incremental learning

### Acceptance Criteria
- [ ] Stacked arbiter with 3+ base learners implemented
- [ ] Pareto frontier calculation working
- [ ] Knee detection identifying optimal configuration
- [ ] Predictions with confidence intervals
- [ ] Feature importance extraction
- [ ] Model serialization (save/load)
- [ ] Tests achieve >80% coverage
- [ ] Docstrings for all public APIs

## Implementation Guidance

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
import numpy as np

class StackedArbiter:
    """Stacked ensemble for vulnerability severity prediction"""
    
    def __init__(self, base_learners=None, meta_learner=None):
        self.base_learners = base_learners or self._default_base_learners()
        self.meta_learner = meta_learner or LogisticRegression()
        
    def fit(self, X, y):
        """Train ensemble on aligned embeddings"""
        # Train base learners and generate meta-features
        meta_features = self._train_base_learners(X, y)
        # Train meta-learner on base predictions
        self.meta_learner.fit(meta_features, y)
        
    def predict(self, X):
        """Predict severity with confidence"""
        base_predictions = self._get_base_predictions(X)
        return self.meta_learner.predict(base_predictions)
        
    def predict_proba(self, X):
        """Get probability estimates"""
        base_predictions = self._get_base_predictions(X)
        return self.meta_learner.predict_proba(base_predictions)
```

## References
- Wolpert, D. H. (1992). "Stacked generalization"
- Das, I. (1999). "On characterizing the 'knee' of the Pareto curve"
