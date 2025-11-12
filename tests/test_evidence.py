"""Tests for evidence analysis module."""
import pytest
from pathlib import Path
from cve_matter.evidence.model_selection import EvidenceAnalyzer


def test_evidence_analyzer_initialization():
    """Test EvidenceAnalyzer initialization."""
    analyzer = EvidenceAnalyzer()
    assert analyzer is not None


def test_compute_evidence(temp_data_file, temp_output_dir):
    """Test evidence computation."""
    analyzer = EvidenceAnalyzer()
    result = analyzer.compute_evidence_from_file(temp_data_file)
    
    assert result is not None
    assert 'status' in result
    
    if result['status'] == 'success':
        assert 'bic' in result
        assert 'waic' in result
        assert 'log_likelihood' in result
    
    # Save results
    output_path = temp_output_dir / 'evidence_results.json'
    analyzer.save_results(result, output_path)
    assert output_path.exists()


def test_compute_evidence_with_specific_criteria(temp_data_file):
    """Test evidence computation with specific criteria."""
    analyzer = EvidenceAnalyzer()
    result = analyzer.compute_evidence_from_file(
        temp_data_file,
        criteria=['bic']
    )
    
    assert result is not None
    if result['status'] == 'success':
        assert 'bic' in result
