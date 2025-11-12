"""Tests for super-learner arbiter module."""
import pytest
from pathlib import Path
from cve_matter.arbiter.super_learner import SuperLearner


def test_super_learner_initialization():
    """Test SuperLearner initialization."""
    learner = SuperLearner()
    assert learner is not None
    assert learner.n_folds == 5
    assert len(learner.base_learners) == 3


def test_super_learner_with_custom_folds():
    """Test SuperLearner with custom folds."""
    learner = SuperLearner(n_folds=3)
    assert learner.n_folds == 3


def test_super_learner_fit_predict(temp_data_file, temp_output_dir):
    """Test SuperLearner fit and predict."""
    learner = SuperLearner()
    result = learner.fit_predict_from_file(temp_data_file)
    
    assert result is not None
    assert 'status' in result
    
    if result['status'] == 'success':
        assert 'cv_accuracy' in result
        assert 'predictions' in result
    
    # Save predictions
    output_path = temp_output_dir / 'predictions.json'
    learner.save_predictions(result, output_path)
    assert output_path.exists()
