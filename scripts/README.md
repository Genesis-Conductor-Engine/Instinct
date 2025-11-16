# Scripts

This directory contains utility scripts for the CVE Matter-Analysis OS.

## Structure

- **Deployment Scripts**: Automation for deployment tasks
- **Data Processing**: ETL and data preparation scripts
- **Sync Scripts**: Synchronization with external systems (Notion)
- **Publishing Scripts**: Artifact publishing to GCS
- **Maintenance**: Database cleanup, log rotation, etc.

## Scripts to be Created (per tasks)

### Task 060: Notion Sync
- `register_prompt_notion.sh` - Sync legendary_lidlift_v14.md to Notion
- `notion_sync.py` - Python script for Notion API integration

### Task 070: Capsule Publishing
- `publish_capsules.sh` - Publish capsules/*.json to GCS bucket
- `validate_capsules.py` - Validate capsule JSON schemas

### Development and Testing
- `setup_dev_env.sh` - Setup development environment
- `run_tests.sh` - Run test suite with coverage
- `lint_all.sh` - Run all linters (flake8, black, mypy)
- `build_docker.sh` - Build Docker image
- `deploy_local.sh` - Deploy to local Kubernetes (kind/minikube)

### Deployment
- `deploy_staging.sh` - Deploy to staging environment
- `deploy_production.sh` - Deploy to production environment
- `rollback.sh` - Rollback to previous version

### Data Management
- `backup_checkpoints.sh` - Backup NVD sync checkpoints
- `restore_checkpoints.sh` - Restore checkpoints from backup
- `cleanup_old_data.sh` - Remove data older than retention period

### Monitoring
- `health_check.sh` - Check pipeline health
- `generate_report.sh` - Generate analysis report
- `export_metrics.sh` - Export metrics to Prometheus

## Usage Examples

### Register Prompt to Notion (Task 060)
```bash
# Set required environment variables
export NOTION_API_TOKEN="your-notion-token"
export NOTION_PROMPTS_DB_ID="your-database-id"

# Run sync script
./scripts/register_prompt_notion.sh

# Verify SHA matches
cat prompts/legendary_lidlift_v14.md | sha256sum
```

### Publish Capsules (Task 070)
```bash
# Set GCP credentials
export GCP_PROJECT_ID="your-project-id"
export GCP_SA_JSON="path/to/service-account.json"

# Validate capsules
python scripts/validate_capsules.py capsules/

# Publish to GCS (on git tag)
./scripts/publish_capsules.sh v1.0.0
```

### Development Workflow
```bash
# Setup development environment
./scripts/setup_dev_env.sh

# Run linters
./scripts/lint_all.sh

# Run tests
./scripts/run_tests.sh

# Build Docker image
./scripts/build_docker.sh

# Deploy locally
./scripts/deploy_local.sh
```

### Production Deployment
```bash
# Deploy to staging first
./scripts/deploy_staging.sh

# Run smoke tests
./scripts/health_check.sh staging

# Deploy to production
./scripts/deploy_production.sh

# Monitor deployment
watch kubectl get pods -n cve-analysis

# Rollback if needed
./scripts/rollback.sh
```

## Script Template

All scripts should follow this template:

```bash
#!/usr/bin/env bash
# Script: script_name.sh
# Description: Brief description of what this script does
# Usage: ./script_name.sh [arguments]
# Dependencies: List of required tools/commands

set -euo pipefail  # Exit on error, undefined var, pipe failure
IFS=$'\n\t'

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

check_dependencies() {
    local deps=("$@")
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
}

# Main function
main() {
    log_info "Starting script..."
    
    # Check dependencies
    check_dependencies "command1" "command2"
    
    # Script logic here
    
    log_info "Script completed successfully"
}

# Run main function
main "$@"
```

## Security Guidelines

- **Never commit secrets**: Use environment variables or secret management
- **Validate inputs**: Check all user inputs and file paths
- **Use set -euo pipefail**: Fail fast on errors
- **Log actions**: Use structured logging with timestamps
- **Dry-run mode**: Support --dry-run flag for testing
- **Error handling**: Provide clear error messages and exit codes

## Testing Scripts

Test scripts before using them in production:

```bash
# Use dry-run mode
./scripts/deploy_production.sh --dry-run

# Test in staging environment
./scripts/deploy_staging.sh

# Validate output
./scripts/health_check.sh staging
```

## CI/CD Integration

Scripts are used in GitHub Actions workflows:

```yaml
# Example workflow step
- name: Publish Capsules
  run: ./scripts/publish_capsules.sh
  env:
    GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
    GCP_SA_JSON: ${{ secrets.GCP_SA_JSON }}
```

## Maintenance

- **Review regularly**: Check scripts for outdated commands
- **Update dependencies**: Keep tool versions current
- **Document changes**: Update comments when modifying logic
- **Test after changes**: Always test scripts after modifications

## References

- [Bash Best Practices](https://github.com/awesome-lists/awesome-bash#style-guides)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [ShellCheck](https://www.shellcheck.net/) - Shell script linting tool
