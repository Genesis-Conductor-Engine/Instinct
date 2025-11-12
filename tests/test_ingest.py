"""Tests for NVD ingestion module."""
import pytest
from pathlib import Path
from cve_matter.ingest import NVDIngestor


def test_nvd_ingestor_initialization():
    """Test NVDIngestor initialization."""
    ingestor = NVDIngestor()
    assert ingestor is not None
    assert ingestor.api_key is None
    assert ingestor.rate_limit_delay == 6.0


def test_nvd_ingestor_with_config():
    """Test NVDIngestor initialization with config."""
    config = {'nvd': {'api_key': 'test_key'}}
    ingestor = NVDIngestor(config=config)
    assert ingestor.api_key == 'test_key'
    assert ingestor.rate_limit_delay == 0.6


def test_fetch_cves():
    """Test CVE fetching."""
    ingestor = NVDIngestor()
    cves = ingestor.fetch_cves(max_results=5)
    assert len(cves) <= 5
    assert all('id' in cve for cve in cves)
    assert all('cvss_score' in cve for cve in cves)


def test_fetch_cves_with_date_range():
    """Test CVE fetching with date range."""
    ingestor = NVDIngestor()
    cves = ingestor.fetch_cves(
        start_date='2024-01-01',
        end_date='2024-01-31',
        max_results=5
    )
    assert len(cves) <= 5


def test_save_data(temp_output_dir):
    """Test saving CVE data."""
    ingestor = NVDIngestor()
    cves = ingestor.fetch_cves(max_results=5)
    
    output_path = temp_output_dir / 'test_cves.json'
    ingestor.save_data(cves, output_path)
    
    assert output_path.exists()
    
    import json
    with open(output_path) as f:
        saved_data = json.load(f)
    
    assert 'metadata' in saved_data
    assert 'cves' in saved_data
    assert len(saved_data['cves']) == len(cves)
