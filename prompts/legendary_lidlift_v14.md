# LID-LIFT v1.4 System Description

**Version:** 1.4  
**Type:** Defense-Only CVE Matter-Analysis Pipeline  
**Mission:** Blue-team CVE matter-analysis from NVD ingest → positional alignment → stacked arbiter → ε-refractors → Bayesian evidence

## System Overview

LID-LIFT (Layered Intelligence Defense - Lateral Inference Framework for Threat Analysis) is a defense-focused CVE matter-analysis system designed to:

1. **Ingest**: Pull and normalize CVE data from NVD (National Vulnerability Database)
2. **Align**: Perform positional alignment across multiple vulnerability representations
3. **Arbitrate**: Apply stacked ensemble learning with Pareto knee detection
4. **Refract**: Use epsilon-refractors to detect distributional shifts
5. **Evidence**: Calculate Bayesian evidence scores for vulnerability prioritization

## Core Principles

### Defense-Only Stance
- **NO offensive payloads** - All analysis is defensive and protective
- **NO cryptographic-breaking** - System does not attempt to break or weaken cryptography
- **NO exploit generation** - System focuses on defense, detection, and prioritization
- **YES vulnerability analysis** - System analyzes and prioritizes vulnerabilities for remediation

### Chain of Thought (CoT) Disabled
LID-LIFT v1.4 operates in direct inference mode without explicit chain-of-thought reasoning paths. This provides:
- Faster response times for high-volume CVE processing
- Reduced token consumption in production pipelines
- Direct output generation without intermediate reasoning steps

### H-MOC Run Report Integration
LID-LIFT integrates with H-MOC (Hierarchical Multi-Objective Coordinator) for:
- Structured run reports with execution metrics
- Multi-objective optimization tracking
- Performance monitoring and alerting
- Audit trail for compliance and review

## Technical Architecture

### 1. NVD Ingest Module (`src/ingest/nvd_client.py`)
**Purpose:** Fetch and normalize CVE data from NVD API v2.0

**Key Features:**
- Delta synchronization with ETag support
- Exponential backoff for rate limiting
- JSONL output format for efficient streaming
- Checkpointing for recovery from failures

**Outputs:**
- Normalized CVE records in JSONL format
- Metadata including CVSS scores, CWE mappings, CPE data
- Timestamp-based tracking for incremental updates

### 2. Positional Alignment (`src/alignment/`)
**Purpose:** Align vulnerability representations across different embedding spaces

**Components:**
- **Procrustes Alignment** (`procrustes.py`): Orthogonal transformation for shape matching
- **Canonical Correlation Analysis** (`cca.py`): Linear relationships between embedding spaces

**Key Metrics:**
- R² (coefficient of determination) ≥ configured threshold
- Alignment quality scores
- Transformation matrices for cross-space mapping

**Use Case:** Enable comparison of vulnerabilities from different sources or time periods

### 3. Stacked Arbiter (`src/models/arbiter.py`)
**Purpose:** Ensemble learning for vulnerability severity prediction

**Architecture:**
- **Base learners**: Multiple weak learners (RandomForest, GradientBoosting, etc.)
- **Meta-learner**: Stacked super-learner for final predictions
- **Pareto knee detection**: Identify optimal trade-off points in multi-objective space

**Outputs:**
- Severity predictions with confidence intervals
- Feature importance scores
- Pareto-optimal configurations

### 4. Epsilon-Refractors (`src/refractors/`)
**Purpose:** Detect distributional shifts in vulnerability patterns

**Components:**
- **Epsilon-refractor** (`epsilon.py`): Measure deviation from expected distributions
- **Shift detector** (`shifts.py`): Identify concept drift and data drift

**Key Metrics:**
- ε-divergence: Quantify distributional differences
- Shift magnitude and direction
- Alert thresholds for significant changes

**Use Case:** Detect emerging threat patterns or changes in vulnerability landscape

### 5. Bayesian Evidence Module (`src/evaluation/evidence.py`)
**Purpose:** Calculate evidence scores for model comparison and vulnerability prioritization

**Metrics:**
- **BIC** (Bayesian Information Criterion): Model complexity penalty
- **WAIC** (Widely Applicable Information Criterion): Better for hierarchical models
- **Bayes Factor**: Relative evidence between models
- **Jeffreys Scale**: Interpret evidence strength

**Outputs:**
- Log-evidence scores for each vulnerability
- Model comparison metrics
- Uncertainty quantification

## Data Flow

```
NVD API → Ingest → JSONL → Alignment → Embeddings → Arbiter → Predictions
                                           ↓
                                      Refractors → Shift Detection
                                           ↓
                                      Evidence → Priority Scores
```

## Security Guardrails

### Input Validation
- Sanitize all external inputs (CVE data, API responses)
- Validate schema compliance before processing
- Reject malformed or suspicious data

### Output Filtering
- Never expose internal system paths or credentials
- Sanitize all outputs before external transmission
- Log security-relevant events for audit

### Dependency Management
- Pin all dependencies with version locks
- Regular security scanning with Trivy
- Automated updates for security patches

### Secrets Management
- No secrets in source code or configuration files
- Use environment variables or secret management systems (e.g., GCP Secret Manager)
- Rotate credentials regularly

## Operational Requirements

### Performance
- Process ≥1000 CVEs per hour in batch mode
- API response time <5 seconds for single CVE queries
- Support concurrent processing with worker pools

### Reliability
- Graceful degradation on partial failures
- Retry logic with exponential backoff
- Comprehensive error logging and monitoring

### Observability
- Structured logging (JSON format)
- Prometheus metrics for monitoring
- Distributed tracing for request flows
- H-MOC run reports for execution analysis

## Deployment Targets

### Docker
- Multi-stage builds for minimal image size
- Non-root user for security
- Health check endpoints

### Kubernetes (GKE)
- Horizontal pod autoscaling based on CPU/memory
- gVisor for enhanced container isolation
- Pod security policies enforced

### Argo Workflows
- DAG-based pipeline orchestration
- Artifact passing between steps
- Retry and timeout policies

## Configuration

### Environment Variables
- `NVD_API_KEY`: API key for NVD access (optional but recommended)
- `ALIGNMENT_R2_THRESHOLD`: Minimum R² for alignment (default: 0.8)
- `EPSILON_THRESHOLD`: Threshold for refractor alerts (default: 0.05)
- `EVIDENCE_METHOD`: Bayesian evidence method (BIC or WAIC, default: WAIC)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARN, ERROR)
- `CUDA_VISIBLE_DEVICES`: GPU device selection for CUDA operations

### Configuration Files
- `config/pipeline.yaml`: Pipeline configuration
- `config/models.yaml`: Model hyperparameters
- `config/thresholds.yaml`: Alert and filtering thresholds

## Usage Example

```python
from src.ingest import NVDClient
from src.alignment import align
from src.models import Arbiter
from src.refractors import EpsilonRefractor
from src.evaluation import calculate_evidence

# 1. Ingest CVE data
client = NVDClient()
cves = client.fetch_recent(days=7)

# 2. Align embeddings
X_aligned = align(cves.embeddings, reference_space)

# 3. Predict severity
arbiter = Arbiter()
predictions = arbiter.predict(X_aligned)

# 4. Detect shifts
refractor = EpsilonRefractor()
shifts = refractor.detect(X_aligned)

# 5. Calculate evidence
evidence = calculate_evidence(predictions, cves.ground_truth)
```

## Versioning and Updates

- **Current Version**: 1.4
- **Last Updated**: 2025-11-13
- **Next Review**: Quarterly or on major CVE landscape changes
- **Breaking Changes**: Require major version bump and migration guide

## References

- NVD API Documentation: https://nvd.nist.gov/developers
- CVSS v3.1 Specification: https://www.first.org/cvss/v3.1/specification-document
- Bayesian Model Comparison: Gelman et al., "Bayesian Data Analysis" (3rd ed.)
- Procrustes Analysis: Goodall, "Procrustes methods in the statistical analysis of shape"

## Support and Contact

For questions, issues, or contributions related to LID-LIFT v1.4:
- Internal Issue Tracker: Use GitHub Issues on this repository
- Security Concerns: Follow SECURITY.md disclosure process
- Feature Requests: Tag with `enhancement` label

---

**Reminder**: This is a DEFENSE-ONLY system. Any attempt to use LID-LIFT for offensive purposes, exploit generation, or cryptographic attacks violates the system's design principles and security policy.
