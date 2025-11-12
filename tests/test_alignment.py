"""Tests for alignment modules."""
from cve_matter.alignment.cca import CCAAlignment
from cve_matter.alignment.procrustes import ProcrustesAlignment


def test_procrustes_initialization():
    """Test ProcrustesAlignment initialization."""
    aligner = ProcrustesAlignment()
    assert aligner is not None


def test_procrustes_align_from_file(temp_data_file, temp_output_dir):
    """Test Procrustes alignment from file."""
    aligner = ProcrustesAlignment()
    result = aligner.align_from_file(temp_data_file)

    assert result is not None
    assert 'status' in result

    # Save results
    output_path = temp_output_dir / 'procrustes_result.json'
    aligner.save_results(result, output_path)
    assert output_path.exists()


def test_cca_initialization():
    """Test CCAAlignment initialization."""
    aligner = CCAAlignment()
    assert aligner is not None
    assert aligner.n_components == 2


def test_cca_align_from_file(temp_data_file, temp_output_dir):
    """Test CCA alignment from file."""
    aligner = CCAAlignment()
    result = aligner.align_from_file(temp_data_file)

    assert result is not None
    assert 'status' in result

    # Save results
    output_path = temp_output_dir / 'cca_result.json'
    aligner.save_results(result, output_path)
    assert output_path.exists()


def test_cca_with_config():
    """Test CCA with custom configuration."""
    config = {'alignment': {'n_components': 3}}
    aligner = CCAAlignment(config=config)
    assert aligner.n_components == 3
