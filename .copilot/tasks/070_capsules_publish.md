# Task 070: Capsules Publishing

## Goal

Implement automated publishing of capsule configuration files to a cloud storage bucket or domain when new versions are tagged.

## Files to Create/Edit

### New Files
- `.github/workflows/publish-capsules.yml` - GitHub Actions workflow for publishing
- `scripts/publish_capsules.sh` - Script to publish capsules
- `scripts/validate_capsules.py` - Validation script for capsules
- `tests/scripts/test_validate_capsules.py` - Tests for validation

### Supporting Files
- `.env.example` - Add publishing configuration examples

## Requirements

### Functional Requirements

1. **Automated Publishing**
   - Trigger on Git tag creation (e.g., v1.0.0, v1.4.0)
   - Publish capsules to GCS bucket or CDN
   - Set appropriate access permissions (public or authenticated)
   - Generate versioned URLs for capsules

2. **Validation**
   - Validate JSON schema before publishing
   - Check for required fields
   - Verify version consistency
   - Run automated tests

3. **Versioning**
   - Publish versioned capsules (e.g., lidlift-v1.4.0.json)
   - Update "latest" symlinks/aliases
   - Maintain version history
   - Support rollback to previous versions

4. **Notification**
   - Post publication status to workflow
   - Generate changelog if applicable
   - Update documentation with new URLs

### Acceptance Criteria
- [ ] GitHub Actions workflow for publishing
- [ ] Triggered on tag creation
- [ ] Capsule validation before publishing
- [ ] Published to cloud storage (GCS or equivalent)
- [ ] Versioned URLs generated
- [ ] Latest aliases updated
- [ ] Tests for validation logic
- [ ] Documentation updated

## Implementation Guidance

```yaml
# .github/workflows/publish-capsules.yml
name: Publish Capsules

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # For GCP Workload Identity
      
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Validate capsules
        run: |
          python scripts/validate_capsules.py capsules/*.json
          
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
          
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        
      - name: Publish capsules
        env:
          GCS_BUCKET: ${{ secrets.GCS_CAPSULES_BUCKET }}
          VERSION: ${{ github.ref_name }}
        run: |
          bash scripts/publish_capsules.sh
          
      - name: Update latest
        run: |
          # Create/update latest symlinks
          echo "Published capsules version ${VERSION}"
```

```bash
#!/bin/bash
# scripts/publish_capsules.sh

set -euo pipefail

GCS_BUCKET="${GCS_BUCKET:-}"
VERSION="${VERSION:-latest}"

if [ -z "$GCS_BUCKET" ]; then
    echo "Error: GCS_BUCKET must be set"
    exit 1
fi

# Remove 'v' prefix from version if present
VERSION_CLEAN="${VERSION#v}"

echo "Publishing capsules version $VERSION_CLEAN to gs://$GCS_BUCKET/"

# Publish each capsule with version
for capsule in capsules/*.json; do
    filename=$(basename "$capsule" .json)
    
    # Upload versioned file
    gsutil -h "Content-Type:application/json" \
           -h "Cache-Control:public, max-age=3600" \
           cp "$capsule" "gs://$GCS_BUCKET/${filename}-${VERSION_CLEAN}.json"
    
    # Update latest
    gsutil -h "Content-Type:application/json" \
           -h "Cache-Control:public, max-age=300" \
           cp "$capsule" "gs://$GCS_BUCKET/${filename}-latest.json"
    
    echo "Published $filename version $VERSION_CLEAN"
done

echo "All capsules published successfully"
```

```python
# scripts/validate_capsules.py
import json
import sys
from pathlib import Path
from typing import List

def validate_capsule(filepath: Path) -> List[str]:
    """Validate a capsule JSON file"""
    errors = []
    
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    
    # Check required fields
    required_fields = ['name', 'version', 'type', 'description']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate version format
    if 'version' in data:
        version = data['version']
        if not isinstance(version, str) or not version:
            errors.append(f"Invalid version format: {version}")
    
    return errors

def main(capsule_files: List[str]):
    """Validate all capsule files"""
    all_valid = True
    
    for filepath in capsule_files:
        path = Path(filepath)
        print(f"Validating {path.name}...")
        
        errors = validate_capsule(path)
        if errors:
            all_valid = False
            print(f"  ✗ Validation failed:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✓ Valid")
    
    if not all_valid:
        print("\nValidation failed!")
        sys.exit(1)
    else:
        print("\nAll capsules valid!")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_capsules.py <capsule1.json> [capsule2.json ...]")
        sys.exit(1)
    
    main(sys.argv[1:])
```

## Configuration

Secrets and variables to configure:
- `GCS_CAPSULES_BUCKET`: GCS bucket name for capsules
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: GCP Workload Identity Provider
- `GCP_SERVICE_ACCOUNT`: Service account for publishing

## References
- Google Cloud Storage: https://cloud.google.com/storage/docs
- GitHub Actions with GCP: https://github.com/google-github-actions/auth
