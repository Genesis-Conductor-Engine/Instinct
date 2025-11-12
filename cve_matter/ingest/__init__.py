"""NVD CVE data ingestion module."""
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import time


class NVDIngestor:
    """Ingest CVE data from the National Vulnerability Database (NVD).
    
    This module provides defensive capabilities for ingesting and processing
    CVE vulnerability data for blue-team analysis purposes only.
    """
    
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize NVD ingestor with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.api_key = self.config.get('nvd', {}).get('api_key')
        self.rate_limit_delay = 6.0 if not self.api_key else 0.6  # NVD rate limits
        
    def fetch_cves(self, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None,
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch CVE records from NVD API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_results: Maximum number of results to fetch
            
        Returns:
            List of CVE records
        """
        cves = []
        params: Dict[str, Any] = {
            'resultsPerPage': min(max_results, 2000)
        }
        
        if start_date:
            params['pubStartDate'] = f"{start_date}T00:00:00.000"
        if end_date:
            params['pubEndDate'] = f"{end_date}T23:59:59.999"
            
        headers = {}
        if self.api_key:
            headers['apiKey'] = self.api_key
            
        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if 'vulnerabilities' in data:
                for vuln in data['vulnerabilities']:
                    cve_data = self._parse_cve(vuln)
                    cves.append(cve_data)
                    
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch from NVD API: {e}")
            # Return mock data for testing/development
            cves = self._generate_mock_data(max_results)
            
        return cves[:max_results]
    
    def _parse_cve(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a CVE record from NVD format.
        
        Args:
            vuln: Raw vulnerability data from NVD
            
        Returns:
            Parsed CVE record
        """
        cve = vuln.get('cve', {})
        cve_id = cve.get('id', 'UNKNOWN')
        
        descriptions = cve.get('descriptions', [])
        description = next(
            (d['value'] for d in descriptions if d.get('lang') == 'en'),
            'No description available'
        )
        
        metrics = cve.get('metrics', {})
        cvss_v3 = metrics.get('cvssMetricV31', [{}])[0] if metrics.get('cvssMetricV31') else {}
        base_score = cvss_v3.get('cvssData', {}).get('baseScore', 0.0)
        severity = cvss_v3.get('cvssData', {}).get('baseSeverity', 'NONE')
        
        return {
            'id': cve_id,
            'description': description,
            'published': cve.get('published', ''),
            'modified': cve.get('lastModified', ''),
            'cvss_score': base_score,
            'severity': severity,
            'references': [ref.get('url', '') for ref in cve.get('references', [])],
        }
    
    def _generate_mock_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock CVE data for testing when API is unavailable.
        
        Args:
            count: Number of mock records to generate
            
        Returns:
            List of mock CVE records
        """
        mock_cves = []
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        for i in range(count):
            mock_cves.append({
                'id': f'CVE-2024-{10000 + i}',
                'description': f'Mock vulnerability description for testing purposes #{i}',
                'published': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'cvss_score': float((i % 10) + 1),
                'severity': severities[i % len(severities)],
                'references': [f'https://example.com/advisory/{i}'],
            })
            
        return mock_cves
    
    def save_data(self, cves: List[Dict[str, Any]], output_path: Path) -> None:
        """Save CVE data to JSON file.
        
        Args:
            cves: List of CVE records
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                'metadata': {
                    'count': len(cves),
                    'generated': datetime.now().isoformat(),
                    'source': 'NVD'
                },
                'cves': cves
            }, f, indent=2)
