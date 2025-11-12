# CVE Matter-Analysis OS

[![CI](https://github.com/igor-holt/Instinct/actions/workflows/ci.yml/badge.svg)](https://github.com/igor-holt/Instinct/actions/workflows/ci.yml)
[![CodeQL](https://github.com/igor-holt/Instinct/actions/workflows/codeql.yml/badge.svg)](https://github.com/igor-holt/Instinct/actions/workflows/codeql.yml)
[![Trivy](https://github.com/igor-holt/Instinct/actions/workflows/trivy.yml/badge.svg)](https://github.com/igor-holt/Instinct/actions/workflows/trivy.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red.svg)](SECURITY.md)

**A private blue-team repository for defensive CVE vulnerability analysis.**

CVE Matter-Analysis OS is a comprehensive Python 3.11 command-line interface (CLI) platform designed for defensive security operations and vulnerability assessment. This tool provides advanced statistical methods for CVE analysis using machine learning, alignment techniques, and model selection criteria.

## ⚠️ Important Notice

**This is a defensive blue-team security tool only.**

- ✅ **Allowed**: Vulnerability assessment, defensive security, research
- ❌ **Prohibited**: Offensive operations, exploitation, cryptographic breaking

See [SECURITY.md](SECURITY.md) for full details on intended use and security policy.

## Features

### Core Modules

- **🔍 Ingest**: NVD CVE data ingestion with rate limiting
- **🔄 Alignment**: Procrustes and CCA (Canonical Correlation Analysis)
- **🤖 Arbiter**: Super-learner ensemble for risk prediction
- **📊 Refractors**: Epsilon (ε) calculations with optional CUDA support
- **📈 Evidence**: BIC/WAIC model selection criteria

### Infrastructure

- **🐳 Docker**: Multi-stage builds with CPU and CUDA support
- **☸️ Kubernetes**: gVisor RuntimeClass, AdmissionWebhook, PolicyTrigger CRD
- **🔁 Argo Workflows**: GPU-accelerated epsilon sweep workflows
- **🏗️ Terraform**: GKE cluster with GPU node pools
- **🔐 Security**: CodeQL, Trivy scanning, CVD policy

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/igor-holt/Instinct.git
cd Instinct

# Install dependencies
pip install -e ".[dev]"

# Verify installation
cve-matter --version
```

### Basic Usage

```bash
# Ingest CVE data from NVD
cve-matter ingest --output data/cve_data.json

# Run Procrustes alignment
cve-matter align --method procrustes --input data/cve_data.json

# Execute super-learner predictions
cve-matter arbiter --input data/cve_data.json --n-folds 5

# Compute epsilon values (GPU-accelerated)
cve-matter refract --input data/cve_data.json --use-gpu

# Evaluate model evidence
cve-matter evidence --input data/cve_data.json --criteria bic waic
```

## Configuration

Configuration is managed via `config/matter.yaml`:

```yaml
nvd:
  api_key: null  # Optional NVD API key
  max_results: 100

alignment:
  method: procrustes  # or 'cca'
  n_components: 2

refractors:
  use_gpu: false  # Set true for CUDA
```

## Docker

### Build Images

```bash
# CPU-only image
docker build --target cpu -t cve-matter-analysis:cpu .

# CUDA-enabled image (requires NVIDIA Docker)
docker build --target cuda -t cve-matter-analysis:cuda .
```

### Run with Docker Compose

```bash
# CPU workload
docker-compose up cve-matter-cpu

# GPU workload (requires nvidia-docker2)
docker-compose up cve-matter-cuda
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster with gVisor support
- GPU nodes (optional, for CUDA workloads)
- Argo Workflows (for batch processing)

### Deploy Resources

```bash
# Deploy gVisor RuntimeClass
kubectl apply -f k8s/gvisor-runtime.yaml

# Deploy PolicyTrigger CRD
kubectl apply -f k8s/policy-trigger-crd.yaml

# Deploy admission webhook
kubectl apply -f k8s/admission-webhook.yaml

# Submit Argo workflow for epsilon sweep
argo submit argo/epsilon-sweep-workflow.yaml
```

## Terraform Infrastructure

### GKE Cluster with GPU Nodes

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan infrastructure changes
terraform plan

# Deploy cluster
terraform apply

# Configure kubectl
gcloud container clusters get-credentials cve-matter-cluster --zone us-central1-a
```

The Terraform configuration creates:
- GKE cluster with gVisor support
- CPU node pool (n2-standard-4)
- GPU node pool (nvidia-tesla-t4)
- VPC network with private nodes
- Workload Identity enabled
- Shielded nodes for security

## Development

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=cve_matter --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Lint with ruff
ruff check cve_matter/ tests/

# Format with black
black cve_matter/ tests/

# Type check with mypy
mypy cve_matter/
```

### CI/CD

GitHub Actions workflows:
- **CI**: Build, test, lint on push/PR
- **CodeQL**: Static security analysis
- **Trivy**: Container vulnerability scanning

## Architecture

```
cve_matter/
├── ingest/       # NVD data ingestion
├── alignment/    # Procrustes & CCA
├── arbiter/      # Super-learner ensemble
├── refractors/   # Epsilon calculations
├── evidence/     # BIC/WAIC criteria
└── cli.py        # Command-line interface

k8s/              # Kubernetes manifests
├── gvisor-runtime.yaml
├── admission-webhook.yaml
└── policy-trigger-crd.yaml

argo/             # Argo Workflows
└── epsilon-sweep-workflow.yaml

terraform/        # Infrastructure as Code
├── main.tf
├── gke.tf
├── variables.tf
└── outputs.tf
```

## Security

This project follows secure development practices:

- **Static Analysis**: CodeQL scans on every PR
- **Dependency Scanning**: Trivy checks for vulnerabilities
- **Container Security**: Multi-stage builds, non-root execution
- **Kubernetes Security**: gVisor sandboxing, RBAC, network policies
- **CVD Policy**: Coordinated Vulnerability Disclosure

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

Proprietary - Private blue-team repository. See [SECURITY.md](SECURITY.md) for usage restrictions.

## Contributing

This is a private repository. For security issues, see [SECURITY.md](SECURITY.md).

## Acknowledgments

- National Vulnerability Database (NVD) for CVE data
- Open-source security research community
- NIST Cybersecurity Framework

---

**Disclaimer**: This tool is for defensive security purposes only. Misuse for offensive operations, exploitation, or cryptographic breaking is strictly prohibited.
