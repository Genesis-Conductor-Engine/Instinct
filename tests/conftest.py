"""Test configuration and fixtures."""
import pytest
import json
from pathlib import Path
import tempfile


@pytest.fixture
def sample_cve_data():
    """Generate sample CVE data for testing."""
    return {
        'metadata': {
            'count': 10,
            'source': 'test',
        },
        'cves': [
            {
                'id': f'CVE-2024-{10000 + i}',
                'description': f'Test vulnerability {i}',
                'published': '2024-01-01T00:00:00',
                'modified': '2024-01-01T00:00:00',
                'cvss_score': float(i + 1),
                'severity': ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][i % 4],
                'references': [f'https://example.com/ref{i}'],
            }
            for i in range(10)
        ]
    }


@pytest.fixture
def temp_data_file(sample_cve_data):
    """Create a temporary file with sample CVE data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_cve_data, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
