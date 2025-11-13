# Task 010: NVD Data Ingestion

## Goal

Implement a robust client for fetching and normalizing CVE data from the National Vulnerability Database (NVD) API v2.0.

## Files to Create/Edit

### New Files
- `src/ingest/__init__.py` - Package initialization
- `src/ingest/nvd_client.py` - Main NVD API client implementation
- `tests/ingest/__init__.py` - Test package initialization
- `tests/ingest/test_nvd_client.py` - Unit tests for NVD client
- `tests/fixtures/nvd_sample.json` - Sample NVD API response for testing

### Supporting Files
- `requirements.txt` - Add `requests`, `requests-cache` dependencies
- `src/ingest/config.py` - Configuration for NVD client (optional)

## Requirements

### Functional Requirements

1. **API Integration**
   - Connect to NVD API v2.0 (https://services.nvd.nist.gov/rest/json/cves/2.0/)
   - Support optional API key for higher rate limits
   - Implement pagination for large result sets

2. **Delta Synchronization**
   - Track last successful sync timestamp
   - Fetch only CVEs modified since last sync
   - Support full refresh mode for initial sync or recovery

3. **Rate Limiting & Backoff**
   - Respect NVD API rate limits (5 requests/30s without key, 50 requests/30s with key)
   - Implement exponential backoff for rate limit errors (429)
   - Implement retry logic for transient network errors (500, 502, 503)

4. **ETag Support**
   - Store and send ETag headers for conditional requests
   - Handle 304 Not Modified responses efficiently
   - Reduce unnecessary data transfer

5. **Data Normalization**
   - Extract key fields: CVE ID, description, CVSS scores, CWE mappings, CPE data
   - Normalize CVSS v2/v3 scores into consistent format
   - Convert timestamps to ISO 8601 format

6. **Output Format**
   - Write normalized CVE records to JSONL (JSON Lines) format
   - One CVE per line for efficient streaming
   - Support output to file or stdout

7. **Checkpointing**
   - Save progress periodically to enable recovery from failures
   - Store checkpoint data (last processed CVE ID, timestamp, ETag)
   - Resume from checkpoint on restart

### Non-Functional Requirements

1. **Performance**
   - Process at least 1000 CVEs per hour
   - Use connection pooling for HTTP requests
   - Minimize memory footprint for large datasets

2. **Reliability**
   - Gracefully handle API errors
   - Retry transient failures up to 3 times
   - Log all errors with context

3. **Observability**
   - Structured logging with JSON output
   - Log key events: sync started, progress updates, sync completed
   - Include metrics: CVEs fetched, API calls made, errors encountered

4. **Security**
   - Store API key in environment variable (NVD_API_KEY)
   - Never log API keys or sensitive data
   - Validate SSL certificates

## Implementation Guidance

### Class Structure

```python
class NVDClient:
    """Client for interacting with NVD API v2.0"""
    
    def __init__(self, api_key: Optional[str] = None, checkpoint_file: Optional[str] = None):
        """Initialize client with optional API key and checkpoint file"""
        
    def fetch_recent(self, days: int = 7) -> List[Dict]:
        """Fetch CVEs modified in the last N days"""
        
    def fetch_since(self, last_modified: datetime) -> List[Dict]:
        """Fetch CVEs modified since given timestamp"""
        
    def fetch_all(self, start_date: Optional[datetime] = None) -> Iterator[Dict]:
        """Fetch all CVEs, optionally starting from a date"""
        
    def normalize_cve(self, raw_cve: Dict) -> Dict:
        """Normalize raw CVE JSON to standardized format"""
        
    def save_checkpoint(self):
        """Save current progress to checkpoint file"""
        
    def load_checkpoint(self) -> Optional[Dict]:
        """Load previous checkpoint if it exists"""
```

### Normalized CVE Schema

```json
{
  "cve_id": "CVE-2023-12345",
  "description": "Vulnerability description...",
  "published_date": "2023-01-15T10:30:00Z",
  "last_modified_date": "2023-01-20T14:45:00Z",
  "cvss_v3": {
    "base_score": 7.5,
    "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
    "severity": "HIGH"
  },
  "cvss_v2": {
    "base_score": 5.0,
    "vector_string": "AV:N/AC:L/Au:N/C:P/I:N/A:N"
  },
  "cwe_ids": ["CWE-79", "CWE-89"],
  "cpe_matches": [
    "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*"
  ],
  "references": [
    {"url": "https://example.com/advisory", "source": "vendor"}
  ]
}
```

### Error Handling

```python
class NVDAPIError(Exception):
    """Base exception for NVD API errors"""

class RateLimitError(NVDAPIError):
    """Raised when rate limit is exceeded"""

class APIUnavailableError(NVDAPIError):
    """Raised when API is temporarily unavailable"""
```

## Acceptance Criteria

### Implementation
- [ ] `NVDClient` class implemented with all required methods
- [ ] Delta sync functionality working (fetches only new/modified CVEs)
- [ ] ETag support implemented for conditional requests
- [ ] Exponential backoff for rate limits and retries for transient errors
- [ ] JSONL output format implemented
- [ ] Checkpointing functionality working (save and resume)
- [ ] CVE normalization extracts all required fields

### Testing
- [ ] Unit tests for `NVDClient` methods with mocked API responses
- [ ] Test rate limit handling (mock 429 responses)
- [ ] Test retry logic for transient errors (mock 500, 502, 503)
- [ ] Test ETag conditional request behavior
- [ ] Test checkpoint save and restore
- [ ] Test CVE normalization with sample data
- [ ] Test edge cases (empty responses, malformed data, missing fields)
- [ ] Tests achieve >80% code coverage

### Documentation
- [ ] Docstrings for all public methods
- [ ] Usage examples in module docstring
- [ ] Configuration options documented (API key, checkpoint file, etc.)
- [ ] Error handling behavior documented

### Quality
- [ ] Code passes flake8 linting
- [ ] Code passes black formatting check
- [ ] Code passes mypy type checking
- [ ] No hardcoded secrets or API keys in code
- [ ] All external dependencies added to requirements.txt

## Validation Steps

1. **Manual Testing**
   ```bash
   # Set API key (optional)
   export NVD_API_KEY="your-api-key-here"
   
   # Fetch recent CVEs
   python -m src.ingest.nvd_client --days 7 --output data/cves.jsonl
   
   # Verify output
   head -n 5 data/cves.jsonl | python -m json.tool
   
   # Test resume from checkpoint
   python -m src.ingest.nvd_client --days 7 --checkpoint data/checkpoint.json
   ```

2. **Automated Testing**
   ```bash
   # Run unit tests
   pytest tests/ingest/ -v
   
   # Run with coverage
   pytest tests/ingest/ --cov=src.ingest --cov-report=term-missing
   
   # Verify coverage >80%
   ```

3. **Linting and Type Checking**
   ```bash
   # Format code
   black src/ingest/ tests/ingest/
   
   # Check linting
   flake8 src/ingest/ tests/ingest/
   
   # Type check
   mypy src/ingest/
   ```

4. **Integration Test**
   - Run client against real NVD API (with API key)
   - Fetch CVEs from last 7 days
   - Verify output is valid JSONL
   - Verify checkpoint is saved
   - Verify resume from checkpoint works

## Dependencies

### Python Packages
- `requests>=2.31.0` - HTTP client
- `requests-cache>=1.1.0` - Optional caching for development
- `python-dateutil>=2.8.2` - Date parsing

### External Services
- NVD API v2.0 (https://nvd.nist.gov/developers)
- Optional: NVD API key for higher rate limits (request from NVD website)

## Notes

- **API Key**: Request from https://nvd.nist.gov/developers/request-an-api-key
- **Rate Limits**: Without key: 5 requests/30s, With key: 50 requests/30s
- **Data Volume**: NVD contains 200,000+ CVEs; initial sync will take time
- **Incremental Updates**: Most runs should be incremental (fetch last 24 hours)
- **Testing**: Use mocked responses for unit tests; avoid hitting real API in tests

## References

- NVD API 2.0 Documentation: https://nvd.nist.gov/developers/vulnerabilities
- CVE JSON Schema: https://csrc.nist.gov/schema/nvd/api/2.0/cve_api_json_2.0.schema
- CVSS Specification: https://www.first.org/cvss/specification-document

## Related Tasks

- **Task 020**: Positional alignment (consumes output from this task)
- **Task 060**: Notion sync (may use ingest logs for status updates)
