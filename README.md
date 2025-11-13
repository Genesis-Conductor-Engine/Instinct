# CVE Matter-Analysis OS

**Defense-Only Blue-Team Vulnerability Analysis Pipeline**

## Overview

The CVE Matter-Analysis OS is a comprehensive pipeline for analyzing vulnerabilities from the National Vulnerability Database (NVD). This system employs advanced machine learning techniques including positional alignment, stacked arbitration, epsilon-refractors for distributional shift detection, and Bayesian evidence calculation to prioritize and analyze security vulnerabilities.

**Mission**: Defense-only CVE analysis supporting blue-team security operations.

## Architecture

The pipeline consists of five main stages:

1. **NVD Ingest** → Fetch and normalize CVE data from NVD API v2.0
2. **Positional Alignment** → Align vulnerability embeddings across different spaces
3. **Stacked Arbiter** → Ensemble learning for severity prediction with Pareto optimization
4. **Epsilon-Refractors** → Detect distributional shifts in vulnerability patterns
5. **Bayesian Evidence** → Calculate evidence scores using BIC/WAIC for prioritization

## Technology Stack

- **Language**: Python 3.11+
- **ML/Data**: NumPy, SciPy, scikit-learn
- **Optional**: CUDA for GPU acceleration
- **Container**: Docker with gVisor isolation
- **Orchestration**: Kubernetes (GKE), Argo Workflows
- **Infrastructure**: Terraform
- **CI/CD**: GitHub Actions

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized deployment)
- kubectl and access to GKE cluster (for production deployment)
- NVD API key (optional but recommended for higher rate limits)

### Local Development

```bash
# Clone repository
git clone https://github.com/igor-holt/Instinct.git
cd Instinct

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run pipeline
python -m src.main
```

### Running with Docker

```bash
# Build image
docker build -t lidlift:latest .

# Run container
docker run -it --rm \
  -e NVD_API_KEY=$NVD_API_KEY \
  -v $(pwd)/data:/app/data \
  lidlift:latest
```

## Configuration

Environment variables:
- `NVD_API_KEY` - API key for NVD access (optional but recommended)
- `ALIGNMENT_R2_THRESHOLD` - Minimum R² for alignment quality (default: 0.8)
- `EPSILON_THRESHOLD` - Threshold for refractor alerts (default: 0.05)
- `EVIDENCE_METHOD` - Bayesian evidence method: BIC or WAIC (default: WAIC)
- `LOG_LEVEL` - Logging verbosity: DEBUG, INFO, WARN, ERROR (default: INFO)
- `CUDA_VISIBLE_DEVICES` - GPU device selection for CUDA operations (optional)

## Documentation

- **System Description**: [prompts/legendary_lidlift_v14.md](prompts/legendary_lidlift_v14.md)
- **Capsule Configurations**: [capsules/](capsules/)
- **Security Policy**: [SECURITY.md](SECURITY.md)
- **Code Ownership**: [CODEOWNERS](CODEOWNERS)

## Copilot Agent Usage

This repository is configured for GitHub Copilot agents to assist with development tasks.

### Getting Started with Copilot

1. **Read the Agent Guide**: Start with [`.copilot/AGENT_GUIDE.md`](.copilot/AGENT_GUIDE.md) for comprehensive instructions
2. **Review Task Definitions**: Tasks are defined in [`.copilot/tasks/`](.copilot/tasks/) numbered 010-090
3. **Follow the Workflow**: Execute tasks sequentially, one PR per task
4. **Reference Documentation**: Use system documentation in `prompts/` and `capsules/`

### Task Overview

- **Task 010**: NVD data ingestion with delta sync and ETag support
- **Task 020**: Positional alignment using Procrustes and CCA
- **Task 030**: Stacked arbiter with Pareto knee detection
- **Task 040**: Epsilon-refractors for distributional shift detection
- **Task 050**: Bayesian evidence calculation (BIC/WAIC)
- **Task 060**: Notion synchronization for documentation
- **Task 070**: Automated capsule publishing on release
- **Task 080**: Optional CUDA/GPU acceleration support
- **Task 090**: Webhook receiver and Argo Workflows integration

### Key Principles for Copilot Agents

1. **Defense-Only**: All code must support defensive security purposes exclusively
2. **File-Anchored**: Each task specifies exact files to create or modify
3. **One PR Per Task**: Create focused, reviewable pull requests
4. **Security-First**: Never commit secrets; scan dependencies; validate inputs
5. **Sequential Execution**: Complete tasks in order (010 → 020 → ... → 090)

### Creating a PR

When working on a task:
```markdown
## Task: [Number] - [Name]

**Rationale**: Brief explanation of changes

**Task Reference**: `.copilot/tasks/XXX_task_name.md`

### Changes Made
- Created/Modified: [file list]
- Tests added: [test files]

### Validation
- [x] Linters pass
- [x] Tests pass  
- [x] Security scan clean
- [x] Acceptance criteria met

**Test Output**: [Include evidence]
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific module tests
pytest tests/ingest/ -v
```

### Linting and Formatting

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/
```

## Security

**This is a defense-only system**. See [SECURITY.md](SECURITY.md) for:
- Security policy and guardrails
- Vulnerability reporting process
- Secure development practices
- Incident response procedures

### Prohibited Activities

- ❌ Exploit generation
- ❌ Offensive security operations
- ❌ Cryptographic breaking
- ❌ Malware development

### Permitted Activities

- ✅ Vulnerability analysis
- ✅ Risk assessment and prioritization
- ✅ Threat detection and monitoring
- ✅ Defense planning and operations

## Contributing

1. Review the [Copilot Agent Guide](.copilot/AGENT_GUIDE.md)
2. Select a task from [`.copilot/tasks/`](.copilot/tasks/)
3. Implement changes following the task definition
4. Create a focused PR with validation evidence
5. Address code review feedback

## License

[License TBD - Add appropriate license]

## Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Security**: Report vulnerabilities privately via [SECURITY.md](SECURITY.md)
- **Documentation**: See `prompts/` and `.copilot/` directories

## Acknowledgments

This system integrates concepts from:
- NVD/NIST for vulnerability data
- H-MOC (Hierarchical Multi-Objective Coordinator) for orchestration
- LID-LIFT (Layered Intelligence Defense) framework
- Academic research in Bayesian model comparison and distributional shift detection

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-13  
**Status**: Active Development
