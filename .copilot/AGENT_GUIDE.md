# Copilot Agent Guide

## Overview

Welcome to the CVE Matter-Analysis OS repository. This guide provides instructions for GitHub Copilot agents working on this project.

## Repository Mission

**Defense-only CVE matter-analysis pipeline**: Build and maintain a blue-team vulnerability analysis system that ingests data from NVD, performs positional alignment, applies stacked arbitration, detects distributional shifts with ε-refractors, and calculates Bayesian evidence scores.

## Core Principles

### 1. Defense-Only Stance

This repository is **strictly for defensive security purposes**. All code and analysis must support:
- ✅ Vulnerability detection and prioritization
- ✅ Defensive security measures
- ✅ Risk assessment and mitigation
- ❌ **NO exploit payload generation**
- ❌ **NO offensive security tools**
- ❌ **NO cryptographic-breaking attempts**

### 2. File-Anchored Tasks

All development work is organized into discrete, file-anchored tasks located in `.copilot/tasks/`. Each task:
- Has a clear goal and acceptance criteria
- Specifies which files to create or modify
- Includes validation requirements
- Should result in exactly one Pull Request

### 3. One PR Per Task

Follow the workflow:
1. Read the task definition in `.copilot/tasks/`
2. Implement the changes specified
3. Create a single, focused PR for that task
4. Reference this onboarding issue in the PR description
5. Move to the next task only after the current PR is merged

### 4. Security-First Development

- **Never commit secrets**: Use environment variables or secret management systems
- **Scan dependencies**: Check for vulnerabilities before adding new packages
- **Validate inputs**: Sanitize all external data sources
- **Follow SECURITY.md**: Adhere to the security policy for all changes

## Task Execution Workflow

### Step 1: Select a Task

Tasks are numbered sequentially in `.copilot/tasks/`:
- `010_ingest_nvd.md` - NVD data ingestion
- `020_alignment.md` - Positional alignment
- `030_arbiter.md` - Stacked arbiter
- `040_refractors.md` - Epsilon-refractors
- `050_evidence.md` - Bayesian evidence
- `060_notion_sync.md` - Notion synchronization
- `070_capsules_publish.md` - Capsules publishing
- `080_cuda_support.md` - CUDA/GPU support
- `090_bridge.md` - Webhook + Argo bridge

**Start with task 010 and proceed sequentially.**

### Step 2: Read the Task Definition

Each task file includes:
- **Goal**: What needs to be accomplished
- **Files to Edit**: Specific files to create or modify
- **Requirements**: Functional and technical requirements
- **Acceptance Criteria**: How to validate the implementation
- **Dependencies**: Any prerequisite tasks or external dependencies

### Step 3: Implement the Changes

- Make **minimal, surgical changes** to accomplish the task
- Follow existing code patterns and conventions
- Add tests consistent with the repository's testing approach
- Update documentation if relevant to your changes
- Ensure your code passes linters and builds

### Step 4: Validate Your Work

Before creating a PR:
- ✅ Run linters and formatters
- ✅ Run existing tests to ensure no regressions
- ✅ Add/update tests for your changes
- ✅ Verify acceptance criteria are met
- ✅ Check that no secrets are committed
- ✅ Run security scanners on new dependencies

### Step 5: Create a Pull Request

Your PR description should include:
- **Short rationale**: Why these changes are needed
- **Edited file list**: What files were modified
- **Validation evidence**: Test output, build logs, or manual verification results
- **Reference**: Link to the task file and this onboarding guide

Example PR template:
```markdown
## Task: [Task Number] - [Task Name]

**Rationale**: [Brief explanation of why these changes are needed]

**Task Reference**: `.copilot/tasks/XXX_task_name.md`

### Changes Made
- Created/Modified: [list of files]
- Added tests in: [test files]
- Updated documentation: [doc files]

### Validation
- [x] Linters pass
- [x] Tests pass
- [x] Security scan clean
- [x] Acceptance criteria met

**Test Output**:
```
[Include relevant test results or validation evidence]
```

**References**: Related to onboarding issue #[issue number]
```

### Step 6: Address Review Feedback

- Respond to code review comments promptly
- Make requested changes in additional commits
- Re-validate after changes
- Do not force-push (preserve review history)

## Technology Stack

### Languages and Frameworks
- **Python 3.11+**: Primary language for all modules
- **Optional CUDA**: GPU acceleration for compute-intensive operations
- **Docker**: Container runtime
- **Kubernetes (GKE)**: Orchestration platform with gVisor isolation

### Infrastructure
- **Terraform**: Infrastructure as Code
- **Argo Workflows**: DAG-based pipeline orchestration
- **GitHub Actions**: CI/CD automation
- **Prometheus**: Metrics and monitoring

### Key Libraries (examples)
- `numpy`, `scipy`: Numerical computing
- `scikit-learn`: Machine learning (arbiter, alignment)
- `requests`: HTTP client for NVD API
- `pytest`: Testing framework

## Development Environment

### Local Setup
```bash
# Clone repository
git clone https://github.com/igor-holt/Instinct.git
cd Instinct

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linters
flake8 src/
black --check src/
mypy src/
```

### Docker Development
```bash
# Build image
docker build -t lidlift:dev .

# Run container
docker run -it --rm \
  -e NVD_API_KEY=$NVD_API_KEY \
  -v $(pwd)/data:/app/data \
  lidlift:dev

# Run tests in container
docker run -it --rm lidlift:dev pytest
```

## Code Standards

### Python Style
- Follow PEP 8 style guide
- Use `black` for automatic formatting
- Use `flake8` for linting
- Use `mypy` for type checking
- Maximum line length: 100 characters
- Use type hints for function signatures

### Documentation
- Write docstrings for all public functions and classes
- Use NumPy-style docstrings
- Keep inline comments minimal and focused on "why" not "what"
- Update relevant documentation when changing APIs

### Testing
- Write unit tests for all new functions
- Aim for >80% code coverage
- Use pytest fixtures for common setup
- Mock external dependencies (NVD API, etc.)
- Include integration tests for full pipeline runs

### Git Practices
- Write clear, concise commit messages
- Use present tense ("Add feature" not "Added feature")
- Reference issue numbers in commits when applicable
- Keep commits focused and atomic
- Do not commit generated files or dependencies

## Security Guidelines

### Secrets Management
- **Never commit**: API keys, passwords, tokens, certificates
- **Use environment variables**: For configuration and secrets
- **Use secret managers**: GCP Secret Manager for production
- **Rotate credentials**: Regularly update API keys and tokens

### Dependency Security
- **Pin versions**: Use exact versions in requirements.txt
- **Scan before adding**: Check new dependencies for known vulnerabilities
- **Update regularly**: Apply security patches promptly
- **Minimize dependencies**: Only add necessary packages

### Code Security
- **Validate inputs**: Sanitize all external data
- **Use parameterized queries**: Prevent injection attacks
- **Avoid eval()**: Never use eval() or exec() on untrusted input
- **Handle errors gracefully**: Don't expose internal details in error messages

### Reporting Vulnerabilities
- Follow the process in `SECURITY.md`
- Report security issues privately to security team
- Do not create public issues for security vulnerabilities

## Common Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_nvd_client.py

# Run tests matching pattern
pytest -k "test_alignment"
```

### Linting and Formatting
```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Run flake8
flake8 src/ tests/

# Type checking
mypy src/
```

### Building and Running
```bash
# Build Docker image
docker build -t lidlift:latest .

# Run locally
python -m src.main

# Run specific module
python -m src.ingest.nvd_client
```

### Infrastructure
```bash
# Initialize Terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure changes
terraform apply

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n cve-analysis
```

## Troubleshooting

### Common Issues

**Issue**: Import errors when running tests
**Solution**: Ensure you've installed development dependencies: `pip install -r requirements-dev.txt`

**Issue**: Docker build fails
**Solution**: Check Docker version (need 20.10+) and ensure you have sufficient disk space

**Issue**: Kubernetes deployment fails
**Solution**: Verify kubectl is configured correctly and you have access to the GKE cluster

**Issue**: Tests fail locally but pass in CI
**Solution**: Ensure your local environment matches CI environment (Python version, dependencies)

### Getting Help

1. **Check documentation**: Review `prompts/legendary_lidlift_v14.md` and task files
2. **Review logs**: Check application logs and CI logs for error details
3. **Consult runbooks**: See `capsules/runbooks.json` for operational procedures
4. **Ask for help**: Create an issue or reach out to the team

## Additional Resources

- **Main Documentation**: `prompts/legendary_lidlift_v14.md`
- **Capsule Configurations**: `capsules/lidlift-v1.json`, `capsules/hmoc-0.2.json`
- **Operational Runbooks**: `capsules/runbooks.json`
- **Security Policy**: `SECURITY.md`
- **Code Ownership**: `CODEOWNERS`

## Quick Reference

| Component | Module Path | Description |
|-----------|-------------|-------------|
| NVD Client | `src/ingest/nvd_client.py` | Fetch CVE data from NVD API |
| Procrustes | `src/alignment/procrustes.py` | Orthogonal alignment |
| CCA | `src/alignment/cca.py` | Canonical correlation analysis |
| Arbiter | `src/models/arbiter.py` | Stacked ensemble learner |
| Refractors | `src/refractors/epsilon.py` | Distributional shift detection |
| Evidence | `src/evaluation/evidence.py` | Bayesian evidence calculation |

## Version History

- **v1.0** (2025-11-13): Initial version
- **Current**: v1.0

---

**Remember**: This is a **defense-only** system. All work must support defensive security purposes and must not generate exploits or offensive capabilities.
