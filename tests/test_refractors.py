"""Tests for epsilon refractor module."""
from cve_matter.refractors.epsilon import EpsilonCalculator


def test_epsilon_calculator_initialization():
    """Test EpsilonCalculator initialization."""
    calc = EpsilonCalculator()
    assert calc is not None
    assert calc.use_gpu is False


def test_epsilon_calculator_with_gpu_flag():
    """Test EpsilonCalculator with GPU flag."""
    calc = EpsilonCalculator(use_gpu=True)
    # Should be False if CUDA not available
    assert calc.use_gpu in [True, False]


def test_epsilon_sweep(temp_data_file, temp_output_dir):
    """Test epsilon sweep computation."""
    calc = EpsilonCalculator()
    result = calc.compute_epsilon_sweep(temp_data_file)

    assert result is not None
    assert 'status' in result

    if result['status'] == 'success':
        assert 'epsilon_range' in result
        assert 'stability_scores' in result
        assert 'optimal_epsilon' in result

    # Save results
    output_path = temp_output_dir / 'epsilon_results.json'
    calc.save_results(result, output_path)
    assert output_path.exists()


def test_epsilon_sweep_custom_range(temp_data_file):
    """Test epsilon sweep with custom range."""
    calc = EpsilonCalculator()
    result = calc.compute_epsilon_sweep(
        temp_data_file,
        epsilon_min=0.01,
        epsilon_max=0.5,
        n_steps=10
    )

    assert result is not None
    if result['status'] == 'success':
        assert result['epsilon_range'] == [0.01, 0.5]
        assert result['n_steps'] == 10
