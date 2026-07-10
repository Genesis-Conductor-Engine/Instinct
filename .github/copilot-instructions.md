# Copilot Instructions for CVE Matter-Analysis OS

## Repository Overview

**Purpose**: CVE matter-analysis pipeline for blue-team security operations.

**Domain**: Cybersecurity, Machine Learning, Vulnerability Analysis

**Project Type**: Python-based ML pipeline with containerization and Kubernetes deployment

**Key Technologies**:
- **Language**: Python 3.11+ (3.12.3 currently used in CI)
- **ML/Data**: NumPy, SciPy, pandas, scikit-learn
- **Container**: Docker with multi-stage builds
- **Orchestration**: Kubernetes (GKE), Argo Workflows (optional, Task 090)
- **CI/CD**: GitHub Actions
- **Testing**: pytest with markers for integration, heavy, gpu, and slow tests
- **Code Quality**: black (formatter), flake8 (linter), mypy (type checker)

**Repository Size**: Small to medium Python project with modular architecture for 5 pipeline stages + orchestration tasks.

**External Services**: 
- NVD API v2.0 (National Vulnerability Database)
- Optional: Notion (documentation sync), GCP (GKE, GCS), Argo Workflows

## Critical Security Requirements

**⚠️ DEFENSE-ONLY MISSION**: This repository is strictly for defensive security purposes. ALL code must support:
- ✅ Vulnerability analysis and prioritization
- ✅ Risk assessment for remediation
- ✅ Defensive security operations

Review `SECURITY.md` before making any changes. Violations of the defense-only stance are unacceptable.

## Project Structure

### Core Directories

```
/src/                    # Main source code (modules to be implemented in tasks)
  main.py               # Entry point - displays pipeline status
  __init__.py
  
/tests/                  # Test suite (pytest with markers)
  test_structure.py     # Current structural tests
  
/capsules/               # Capsule configurations (JSON)
  hmoc-0.2.json         # H-MOC configuration
  lidlift-v1.json       # LID-LIFT system config
  runbooks.json         # Operational runbooks

/prompts/                # System descriptions and prompts
  legendary_lidlift_v14.md   # Main system description
  
/.copilot/               # Copilot agent configurations
  AGENT_GUIDE.md        # Comprehensive agent guide
  tasks/                # Task definitions (010-090)
  
/.github/
  workflows/            # CI/CD pipelines
    ci.yml             # Lint, test, validate (standard runners)
    codeql.yml         # Security analysis (CodeQL)
    container-scan.yml # Trivy container scanning
    notion-sync.yml    # Documentation sync (optional)
    publish-capsules.yml # Capsule publishing on releases
    
/docs/                   # Documentation
  copilot-agents.md     # Agent documentation
```

### Configuration Files

- `pyproject.toml` - Build config, tool settings (black, mypy, pytest, isort)
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies (testing, linting)
- `Dockerfile` - Multi-stage Docker build (Python 3.11-slim base)
- `prompts.yaml` - Prompt configurations
- `CODEOWNERS` - Code ownership definitions

## Setup and Workflow Commands

### Prerequisites

- **Python 3.11 or higher** (CI uses 3.12.3, but 3.11+ is minimum)
- **Docker** (optional, for containerized development/deployment)
- **Git** (for version control)
- **NVD API Key** (optional but recommended for higher rate limits)

### Setup from Clean Checkout

**ALWAYS run these commands in order from repository root:**

```bash
# 1. Create virtual environment (REQUIRED)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install production dependencies (REQUIRED)
pip install --upgrade pip
pip install -r requirements.txt

# 3. Install development dependencies (REQUIRED for linting/testing)
pip install -r requirements-dev.txt

# 4. Verify installation
python -m src.main  # Should display pipeline status
```

**Expected outcome**: `python -m src.main` creates `data/`, `logs/`, and `checkpoints/` directories and displays pipeline stages with "To be implemented" messages.

### Build Commands

**Run main application:**
```bash
python -m src.main
```

**No separate build step** - Python source is directly executable.

### Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test markers
pytest -m integration     # Integration tests only
pytest -m heavy          # Heavy computational tests
pytest -m gpu            # GPU/CUDA tests
pytest -m slow           # Slow tests
pytest -m "not slow"     # Exclude slow tests

# Run specific test file
pytest tests/test_structure.py -v
```

**Important**: 
- Current test suite has 12 passing structural tests in `test_structure.py`
- Markers are defined in `pyproject.toml` under `[tool.pytest.ini_options]`
- Tests use pytest-cov, pytest-mock, pytest-asyncio, pytest-timeout plugins

### Lint and Format Commands

**ALWAYS run before committing code:**

```bash
# Format code (auto-fix)
black --line-length 100 src/ tests/

# Check formatting without changes
black --check --line-length 100 src/ tests/

# Lint with flake8 (errors and warnings)
flake8 src/ --count --max-line-length=100 --statistics

# Critical errors only
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Type check with mypy
mypy src/ --ignore-missing-imports

# Sort imports (optional, configured for black compatibility)
isort src/ tests/
```

**Configuration**:
- black: line-length=100, target Python 3.11
- flake8: max-line-length=100, max-complexity=10
- mypy: ignore_missing_imports=true
- All settings in `pyproject.toml`

### Docker Commands

**⚠️ Known Issue**: Docker build currently fails due to missing transitive dependency `charset-normalizer` in requirements.txt. The build script uses `pip wheel` with `--no-deps`, which requires all transitive dependencies to be explicitly listed.

**Build image (will fail until charset-normalizer is added):**
```bash
docker build -t lidlift:latest .
```

**Run container (after build succeeds):**
```bash
docker run -it --rm \
  -e NVD_API_KEY=$NVD_API_KEY \
  -v $(pwd)/data:/app/data \
  lidlift:latest
```

**Workaround**: When fixing the Docker build, add missing transitive dependencies to `requirements.txt` or modify the Dockerfile to not use `--no-deps` flag.

### Other Validation Commands

**Validate JSON files:**
```bash
for file in $(find . -name "*.json" -not -path "./.git/*"); do
  python -m json.tool "$file" > /dev/null && echo "✓ $file" || echo "✗ $file"
done
```

**Validate YAML files:**
```bash
python -c "
import yaml
from pathlib import Path
for file in Path('.').rglob('*.yml'):
    if '.git' not in str(file):
        with open(file) as f:
            yaml.safe_load(f)
        print(f'✓ {file}')
"
```

**Security scans (local):**
```bash
# Python dependency check
safety check

# Bandit security linting
bandit -r src/
```

## GitHub Actions Workflows

### CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push to main/develop, PRs to main/develop, manual dispatch

**Jobs**:
1. **lint** - Runs flake8, black, mypy (continue-on-error: true)
2. **unit-tests** - Pytest with coverage, uploads to Codecov
3. **integration-tests** - Tests with `-m integration` marker
4. **heavy-tests** - Tests with `-m heavy` marker, 30min timeout (only on push/manual)
5. **validate-configs** - JSON/YAML validation
6. **ci-success** - Aggregates results, fails if lint/unit-tests/validate-configs fail

**Runner**: All jobs use standard `ubuntu-latest` runners

**Important Notes**:
- Integration tests run after unit tests (needs: unit-tests)
- Heavy tests only run on push to main/develop or manual trigger
- `continue-on-error: true` on lint jobs means they won't fail CI (but should be fixed)
- Coverage reports uploaded to Codecov (optional, won't fail if unavailable)

### CodeQL Workflow (`.github/workflows/codeql.yml`)

**Triggers**: Push to main/develop, PRs, weekly schedule (Mondays 00:00 UTC), manual

**Purpose**: Security analysis using GitHub CodeQL

**Language**: Python

**Query Packs**: security-and-quality

**Runner**: `ubuntu-latest`

**Notes**: Results uploaded to GitHub Security tab (SARIF format)

### Container Scan Workflow (`.github/workflows/container-scan.yml`)

**Triggers**: Push/PR to main/develop (when Dockerfile changes), manual

**Jobs**:
1. **scan-image** - Builds Docker image, scans with Trivy
   - Fails on HIGH/CRITICAL vulnerabilities
   - Uploads SARIF to GitHub Security tab
2. **scan-filesystem** - Scans repository with Trivy
3. **scan-success** - Aggregates, fails if image scan fails

**Runner**: `ubuntu-latest`

**Important**: Currently expected to fail due to Docker build issue mentioned above.

### Other Workflows

- **notion-sync.yml**: Syncs prompts/docs to Notion (Task 060, requires secrets)
- **publish-capsules.yml**: Publishes capsules to GCS on version tags (Task 070, requires GCP auth)

## Local CI Simulation

To closely mirror CI behavior locally, run:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all checks in order (same as CI)
black --check --line-length 100 src/ tests/
flake8 src/ --count --max-line-length=100 --statistics
mypy src/ --ignore-missing-imports
pytest -v --cov=src --cov-report=term-missing
pytest -m integration -v
python -c "import yaml; from pathlib import Path; [yaml.safe_load(open(f)) for f in Path('.').rglob('*.yml') if '.git' not in str(f)]"
```

If all commands succeed, CI should pass.

## Development Workflow

### Task-Based Development

This repository uses a **task-based workflow**. All development work is organized into tasks in `.copilot/tasks/`:

- **010_ingest_nvd.md** - NVD data ingestion
- **020_alignment.md** - Positional alignment
- **030_arbiter.md** - Stacked arbiter
- **040_refractors.md** - Epsilon-refractors
- **050_evidence.md** - Bayesian evidence
- **060_notion_sync.md** - Notion synchronization
- **070_capsules_publish.md** - Capsule publishing
- **080_cuda_support.md** - CUDA/GPU support
- **090_bridge.md** - Webhook + Argo bridge

**ALWAYS**:
1. Read the full task definition in `.copilot/tasks/` before starting
2. Read `.copilot/AGENT_GUIDE.md` for detailed task execution guidance
3. Implement exactly what the task specifies (file-anchored changes)
4. Create one PR per task
5. Execute tasks sequentially (010 → 020 → ... → 090)

### Standard Development Flow

```bash
# 1. Ensure dependencies installed
pip install -r requirements.txt -r requirements-dev.txt

# 2. Make code changes (minimal, surgical modifications)
# - Edit only files specified in task definition
# - Follow existing patterns and conventions

# 3. Format code immediately after changes
black src/ tests/

# 4. Lint your changes
flake8 src/ --max-line-length=100

# 5. Type check
mypy src/ --ignore-missing-imports

# 6. Run tests frequently
pytest -v

# 7. Run tests with coverage before committing
pytest --cov=src --cov-report=term-missing

# 8. Validate configuration files if changed
python -m json.tool <file.json>
python -c "import yaml; yaml.safe_load(open('<file.yml>'))"

# 9. Commit and push
git add <files>
git commit -m "Descriptive message"
git push
```

## Common Issues and Solutions

### Issue: Import errors or missing modules
**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Issue: Tests fail with "ModuleNotFoundError"
**Solution**: Run tests as a module from repo root:
```bash
python -m pytest
# OR
pytest  # if pytest is in PATH from activated venv
```

### Issue: Docker build fails with "charset_normalizer" error
**Known Issue**: `requirements.txt` is missing transitive dependencies. 
**Workaround**: Add `charset-normalizer>=2.0.0` to requirements.txt, or modify Dockerfile to not use `--no-deps` flag in pip install command.

### Issue: Black and flake8 disagree on formatting
**Solution**: Configuration is aligned (line-length=100 for both). Run black first, then flake8:
```bash
black --line-length 100 src/ tests/
flake8 src/ tests/ --max-line-length=100
```

### Issue: Mypy reports many errors
**Note**: `ignore_missing_imports=true` is configured in pyproject.toml. If you see errors, they're likely real type issues. Mypy is currently passing in CI.

### Issue: "pytest" command not found
**Solution**: Ensure dev dependencies installed and venv activated:
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Issue: Python version mismatch
**Minimum**: Python 3.11 required
**Current CI**: Python 3.12.3
**Solution**: If using Python 3.10 or earlier, upgrade. If 3.11+, should work fine.

## Environment Variables

The application recognizes these environment variables (see README.md for full list):

- `NVD_API_KEY` - API key for NVD access (optional, increases rate limits)
- `ALIGNMENT_R2_THRESHOLD` - Minimum R² for alignment quality (default: 0.8)
- `EPSILON_THRESHOLD` - Threshold for refractor alerts (default: 0.05)
- `EVIDENCE_METHOD` - Bayesian evidence method: BIC or WAIC (default: WAIC)
- `LOG_LEVEL` - Logging verbosity: DEBUG, INFO, WARN, ERROR (default: INFO)
- `CUDA_VISIBLE_DEVICES` - GPU device selection (optional, for Task 080)

For local development, create a `.env` file (already in .gitignore) with your settings.

## Dependencies and Tools

### Required Tools (Always Needed)

- Python 3.11+ with pip and venv
- Git

### Optional Tools (For Specific Tasks)

- Docker (for containerization, Task 070 may require)
- kubectl (for Kubernetes deployment)
- gcloud CLI (for GCP operations)
- Notion CLI/API (for Task 060)

### Python Dependencies

**Production** (requirements.txt):
- requests, requests-cache (HTTP/API)
- numpy, scipy, pandas (data processing)
- scikit-learn (ML)
- pyyaml (config)
- structlog (logging)
- python-dateutil (date handling)

**Development** (requirements-dev.txt):
- pytest + plugins (testing)
- black, flake8, mypy, isort (code quality)
- bandit, safety (security)
- sphinx + theme (docs)

**Optional** (commented in requirements.txt):
- torch (CUDA/GPU, Task 080)
- xgboost, lightgbm (advanced ML models)
- notion-client (Task 060)
- argo-workflows (Task 090)
- fastapi, uvicorn (Task 090 webhook server)

## Performance and Runner Notes

### Standard GitHub-Hosted Runners

All current workflows use **standard `ubuntu-latest`** runners. This is appropriate for:
- Linting and formatting (fast)
- Unit tests (< 1 minute)
- Integration tests (few minutes)
- Container builds and scans (< 10 minutes)

### Large Runner Considerations

The CI workflow includes a **heavy-tests** job with a comment about using larger runners. This job:
- Is configured for 30-minute timeout
- Should use larger runners (e.g., ubuntu-22.04-16core) if tests become compute-intensive
- Currently uses standard runner as a placeholder

**When to use large runners**:
- Heavy computational tests (epsilon-sweeps, large-scale alignment)
- GPU tests (Task 080, would need GPU-enabled runners)
- Full pipeline integration tests with 10K+ samples

Update `runs-on` label in `.github/workflows/ci.yml` when large runners are needed.

## Quick Reference

### Most Common Commands

```bash
# Daily development
source venv/bin/activate
black src/ tests/
pytest -v
python -m src.main

# Before commit
black --check src/ tests/
flake8 src/ --max-line-length=100
mypy src/ --ignore-missing-imports
pytest --cov=src

# Full local CI simulation
black --check --line-length 100 src/ tests/ && \
flake8 src/ --count --max-line-length=100 && \
mypy src/ --ignore-missing-imports && \
pytest -v --cov=src
```

### Quick File Locations

- Main entry point: `src/main.py`
- Tests: `tests/test_structure.py`
- CI config: `.github/workflows/ci.yml`
- Task definitions: `.copilot/tasks/`
- System description: `prompts/legendary_lidlift_v14.md`
- Agent guide: `.copilot/AGENT_GUIDE.md`
- Security policy: `SECURITY.md`

## Agent Instructions

When working in this repository:

1. **Trust these instructions** as the primary source of truth for setup, build, test, and workflow commands.
2. **Follow the task-based workflow** - read `.copilot/AGENT_GUIDE.md` and task definitions in `.copilot/tasks/` before implementing changes.
3. **Run commands in the order specified** above - setup commands are sequential and order-dependent.
4. **Always activate virtual environment** before running Python commands.
5. **Lint and test frequently** during development to catch issues early.
6. **Check SECURITY.md** before making changes - defense-only stance is non-negotiable.
7. **Make minimal, surgical changes** - modify only files specified in task definitions.
8. **One PR per task** - follow the file-anchored task approach.
9. Only search, explore, or trial-and-error when:
   - These instructions are incomplete or unclear
   - You encounter an error not covered in "Common Issues"
   - A task definition references a pattern or convention not documented here

This repository is well-structured with clear task definitions. Following these instructions will minimize build failures and speed up development.
