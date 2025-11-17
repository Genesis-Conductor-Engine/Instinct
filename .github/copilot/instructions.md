# GitHub Copilot Instructions — CVE Matter-Analysis OS

**Repository**: Instinct (CVE Matter-Analysis OS)  
**Purpose**: Defense-only blue-team vulnerability analysis pipeline  
**Language/Stack**: Python 3.11, CUDA (optional), Docker, K8s (GKE/gVisor), Argo, Terraform, GitHub Actions  
**Mission**: Build and maintain the CVE matter-analysis pipeline with Bayesian evidence, positional alignment, reverse-adversarial refractors, and a black-box arbiter.

---

## 1. Agent Operating Rules

### Core Principles

**Act from files, not guesswork**. Prefer repository artifacts over improvisation. Always reference existing code, documentation, and configuration files.

**Defense-only guardrails**. This is a private, defense-only repository. Refuse any requests for:
- Cryptographic-breaking code
- Offensive exploit generation
- Malware or payload development
- Anything that could be used for attack purposes

**Idempotent PRs**. Every change must be reproducible via scripts or CI. Changes should be deterministic and well-documented.

**Citations & logs**. Reference edited files in commit messages and PR descriptions. Emit structured logs where applicable using the `structlog` library.

**Never commit secrets**. Read API keys and credentials via environment variables or secret management systems. Fail closed if secrets are missing. Never hardcode credentials in source code.

---

## 2. File Anchors (read these first)

Before making any changes, familiarize yourself with these key files:

- **`.copilot/AGENT_GUIDE.md`** — Primary operating guide for Copilot agents
- **`.copilot/tasks/`** — Atomic tasks with acceptance criteria (010-090)
- **`config/matter.yaml`** — Configuration: mode=cve, thresholds, alignment, refractors, arbiter
- **`src/`** — Source modules:
  - `src/ingest/` — NVD data ingestion
  - `src/alignment/` — Positional alignment (Procrustes, CCA)
  - `src/models/` — Stacked arbiter and ML models
  - `src/refractors/` — Epsilon-refractors for distributional shift
  - `src/evaluation/` — Bayesian evidence calculation
  - `src/orchestrate/` — Pipeline orchestration
- **`k8s/`** — Kubernetes manifests: CRD+webhook, runtime classes, GPU job specs, policies
- **`argo/`** — Argo Workflows: WorkflowTemplate, CronWorkflow, Events
- **`terraform/`** — Infrastructure as Code: GKE cluster, GPU node pool, GCS capsules bucket
- **`prompts/`** — LID-LIFT prompt artifacts (legendary_lidlift_v14.md)
- **`capsules/`** — Capsule artifacts for link-pack (configuration bundles)
- **`SECURITY.md`** — Security policy and vulnerability disclosure
- **`README.md`** — Overview and quick start guide

---

## 3. Default Task Order (finish each before moving on)

Tasks are located in `.copilot/tasks/` and should be completed sequentially:

### Task 010: NVD Ingest
- **Edit**: `src/ingest/nvd_client.py`, `tests/test_ingest.py`
- **Criteria**: Delta sync, ETag/backoff, JSONL output, tests pass
- **Reference**: `.copilot/tasks/010_ingest_nvd.md`

### Task 020: Positional Alignment
- **Edit**: `src/alignment/procrustes.py`, `src/alignment/cca.py`, `tests/test_alignment.py`
- **Criteria**: `alignment_R2 ≥ 0.85`, re-register on fail
- **Reference**: `.copilot/tasks/020_alignment.md`

### Task 030: Arbiter (stacked) + Pareto Knee
- **Edit**: `src/models/arbiter.py`
- **Criteria**: Choose knee over `{accuracy, f1, robust_auc_ε}` vs `{latency_ms, energy_J, cost_$}`
- **Reference**: `.copilot/tasks/030_arbiter.md`

### Task 040: Refractor Grid (ε & axes)
- **Edit**: `src/refractors/epsilon.py`, `src/refractors/shifts.py`
- **Criteria**: Grid runs; outputs robust AUC & CVaR@95
- **Reference**: `.copilot/tasks/040_refractors.md`

### Task 050: Evidence & Decision
- **Edit**: `src/evaluation/evidence.py`
- **Criteria**: BIC/WAIC log-evidence; Bayes factor + Jeffreys class
- **Reference**: `.copilot/tasks/050_evidence.md`

### Task 060: Legendary Prompt Sync (Notion)
- **Run**: `scripts/register_prompt_notion.sh`
- **Criteria**: SHA in Notion matches `prompts/legendary_lidlift_v14.md`
- **Reference**: `.copilot/tasks/060_notion_sync.md`

### Task 070: Capsule Publish
- **Run**: `scripts/publish_capsules.sh` (on tag)
- **Criteria**: `capsules/*.json` reachable at configured bucket/domain
- **Reference**: `.copilot/tasks/070_capsules_publish.md`

### Task 080: GPU Enablement (optional)
- **Files**: `terraform/gpu.tf`, `k8s/gpu-job.yaml`, `docker/Dockerfile` (CUDA)
- **Criteria**: GPU pod requests succeed; tests marked `@gpu` pass
- **Reference**: `.copilot/tasks/080_cuda_support.md`

### Task 090: Admission Webhook & Triggers
- **Files**: `k8s/crd-policytrigger.yaml`, `k8s/deploy-webhook.yaml`, `k8s/webhook-config.yaml`
- **Criteria**: Pods labeled `macrosegment: code` receive sedation init; suspicious binaries rejected
- **Reference**: `.copilot/tasks/090_bridge.md`

### Task 091: Argo ε-Sweep
- **Files**: `argo/workflowtemplate-tensor-macrosegments.yaml`, `argo/cronworkflow-nightly.yaml`
- **Criteria**: Nightly sweep executes and stores artifacts

---

## 4. CI/CD & Quality Gates (must pass on every PR)

### Continuous Integration
- **Lint**: `flake8` for Python code style
- **Tests**: `pytest` with >80% coverage target
- **Python Version**: 3.11 (minimum)
- **Type Checking**: `mypy` for static type analysis

### Security Scanning
- **CodeQL**: Python security analysis (fail on HIGH/CRITICAL)
- **Trivy**: Container image scanning (fail on HIGH/CRITICAL vulnerabilities)
- **Dependency Scanning**: GitHub Dependabot enabled

### Branch Protection
- Required status checks must pass
- At least 1 approving review required
- Linear history enforced (no merge commits)
- No-secret check blocks PRs containing keys or tokens

### Container Requirements
- Build Docker image successfully
- Rootless container (non-root user)
- Read-only filesystem where possible
- No privilege escalation
- Minimal base image (distroless or alpine)

---

## 5. Environment & Secrets

**Use GitHub Secrets / Environments only**. Never commit secrets to the repository.

### Required Secrets
- `NVD_API_KEY` — National Vulnerability Database API key (optional but recommended)
- `GCP_PROJECT_ID` — Google Cloud Platform project identifier
- `GCP_SA_JSON` — GCP Service Account JSON key (if needed for Terraform/K8s)
- `NOTION_API_TOKEN` — Notion integration token for documentation sync
- `NOTION_PROMPTS_DB_ID` — Notion database ID for prompts

### Local Development
- Read from environment variables: `os.getenv('SECRET_NAME')`
- Use `.env` file (gitignored) for local development
- CI injects secrets via `env:` or `secrets:` in workflow files

### Secret Detection
- Pre-commit hooks prevent secret commits
- GitHub secret scanning enabled
- CI fails if secrets detected in diff

---

## 6. Kubernetes/GKE Runtime Rules

### Workload Identity
- Map Kubernetes Service Account (KSA) to Google Service Account (GSA)
- No node-level service account keys
- Use GKE Workload Identity for authentication

### Runtime Isolation
- **RuntimeClass**: Use gVisor for default pods (enhanced isolation)
- **GPU Workloads**: Limited to pods with label `macrosegment: code`
- **Network Policies**: Restrict pod-to-pod communication

### Admission Webhook Policies
AdmissionWebhook applies policies configured by PolicyTrigger CRDs:
- `inject-sleep-init` — Inject initialization delay for controlled startup
- `reject-suspicious-binary` — Block containers with unauthorized binaries
- `freeze-image-pull` — Prevent runtime image pull (only use pre-approved images)

### Resource Management
- Set resource requests and limits for all pods
- Use node affinity for GPU workloads
- Enable horizontal pod autoscaling where appropriate

---

## 7. Argo Orchestration

### Workflow Execution
- Run ε-grid sweep with `tensor-macrosegments` WorkflowTemplate
- CronWorkflow scheduled nightly at 03:00 UTC
- Label all compute pods with `macrosegment: code` for webhook policies

### Artifact Management
- Store workflow outputs in GCS bucket
- Use Argo artifact repository for intermediate data
- Retain artifacts for 30 days minimum

### Monitoring
- Export workflow metrics to Prometheus
- Alert on workflow failures
- Track execution time and resource usage

---

## 8. Definition of Done (per task/PR)

Every PR must meet these criteria before merge:

### Testing & Quality
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`flake8`, `black`)
- [ ] Type checking passes (`mypy`)
- [ ] Code coverage ≥80% for new code
- [ ] No security vulnerabilities detected (CodeQL, Trivy)

### Security
- [ ] No secrets in diff
- [ ] New dependencies scanned for vulnerabilities
- [ ] Input validation for external data
- [ ] Proper error handling (no information leakage)

### Documentation
- [ ] Changelog updated (if applicable)
- [ ] Docstrings for all public functions/classes
- [ ] README updated for user-facing changes
- [ ] Configuration options documented

### Infrastructure Changes
- [ ] **For K8s/Argo changes**: `kubectl diff` or dry-run manifests attached to PR
- [ ] **For Terraform changes**: `terraform plan` output attached to PR (redacted if needed)
- [ ] Infrastructure tested in staging environment

### Review
- [ ] At least 1 approving review
- [ ] All review comments addressed
- [ ] CI/CD pipelines pass

---

## 9. Failure Handling (what Copilot must do)

### Missing Tools or Permissions
If a task fails due to missing tools or insufficient permissions:
- Print exact simulated steps that would be executed
- Mark output as **SIMULATED** in the PR body
- Document what permissions/tools are required
- Propose alternative approach if possible

### Unclear Prompt or Specification
If the prompt or task specification is unclear:
- Re-template the failing prompt with clarifying assumptions
- Propose a single follow-up question as code comments
- Do NOT commit unclear or incorrect code
- Ask for clarification in PR description

### Performance Budget Breach
If latency, energy, or cost budgets are exceeded:
- Propose rollback to last stable configuration
- Open a separate issue with label `perf-budget`
- Document performance metrics and analysis
- Suggest optimization strategies

### Security Issues
If security vulnerabilities are discovered:
- DO NOT commit vulnerable code
- Follow responsible disclosure (see SECURITY.md)
- Report privately to security team
- Wait for fix approval before proceeding

---

## 10. One-Shot Bootstrap Prompt (for Copilot PR generator)

**Copy-paste this prompt when starting work on this repository:**

```
Build/maintain a private, defense-only CVE Matter-Analysis OS:

Pipeline: NVD ingest → positional alignment (Procrustes/CCA) → stacked arbiter (Pareto knee) 
→ ε-refractors → Bayesian evidence (BIC/WAIC)

Requirements:
- Python 3.11+, CUDA optional
- Docker (rootless, gVisor runtime)
- Kubernetes manifests (AdmissionWebhook + PolicyTrigger CRD)
- Argo Workflows (ε-sweep, nightly CronWorkflow)
- Terraform (GKE cluster + GPU node pool)
- CI: lint (flake8), pytest, CodeQL, Trivy
- Tests for all modules (>80% coverage)
- SECURITY.md with CVD process
- Task definitions in .copilot/tasks/ (010-090)
- config/matter.yaml for thresholds and modes

Guardrails:
- Defense-only: NO offensive/crypto-breaking code
- No secrets in commits (use env variables)
- Idempotent changes (reproducible via scripts)
- One PR per task (sequential execution)
- File-anchored: reference .copilot/AGENT_GUIDE.md and task files
```

---

## 11. Technology Stack Reference

### Core Technologies
- **Python 3.11+**: Primary language
- **NumPy, SciPy, scikit-learn**: Numerical computing and ML
- **Requests**: HTTP client for NVD API
- **StructLog**: Structured logging
- **Pytest**: Testing framework

### Optional Technologies
- **CUDA/PyTorch**: GPU acceleration
- **XGBoost, LightGBM**: Advanced ML models

### Infrastructure
- **Docker**: Containerization
- **Kubernetes (GKE)**: Orchestration
- **gVisor**: Container isolation
- **Argo Workflows**: Pipeline orchestration
- **Terraform**: Infrastructure as Code
- **GitHub Actions**: CI/CD

### Monitoring & Observability
- **Prometheus**: Metrics collection
- **Structlog**: Structured logging (JSON)
- **CloudWatch/Stackdriver**: Log aggregation

---

## 12. Code Style and Standards

### Python Style Guide
- Follow PEP 8 conventions
- Use `black` for code formatting (line length: 100)
- Use `flake8` for linting
- Use `mypy` for type checking
- Type hints required for function signatures
- NumPy-style docstrings for documentation

### Git Conventions
- Clear, concise commit messages
- Present tense ("Add feature" not "Added feature")
- Reference issue/task numbers: `[Task 010] Implement NVD client`
- Atomic commits (one logical change per commit)

### Testing Standards
- Unit tests for all functions
- Integration tests for workflows
- Mock external dependencies (NVD API, GCP, etc.)
- Use pytest fixtures for common setup
- Aim for >80% code coverage
- Mark slow/GPU tests with pytest markers

### Security Standards
- Input validation for all external data
- Parameterized queries (no string interpolation)
- Never use `eval()` or `exec()` on untrusted input
- Proper error handling without information leakage
- Regular dependency updates and security scanning

---

## 13. Common Commands

### Development Workflow
```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Testing
pytest                                    # Run all tests
pytest --cov=src --cov-report=html       # With coverage
pytest -m "not gpu and not integration"  # Skip slow tests

# Linting
black src/ tests/                        # Format code
flake8 src/ tests/                       # Check style
mypy src/                                # Type checking

# Running
python -m src.main                       # Run pipeline
python -m src.ingest.nvd_client         # Run NVD client
```

### Infrastructure
```bash
# Terraform
terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan

# Kubernetes
kubectl apply -f k8s/
kubectl get pods -n cve-analysis
kubectl logs -f deployment/cve-pipeline

# Argo
argo submit argo/workflowtemplate-tensor-macrosegments.yaml
argo list
argo logs @latest
```

### Docker
```bash
# Build
docker build -t lidlift:latest .

# Run
docker run -it --rm \
  -e NVD_API_KEY=$NVD_API_KEY \
  -v $(pwd)/data:/app/data \
  lidlift:latest

# Security scan
trivy image lidlift:latest
```

---

## 14. Troubleshooting

### Common Issues

**Import Errors**
- Ensure dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.11+)
- Verify PYTHONPATH includes `src/`

**Test Failures**
- Check that you're not hitting real external APIs (should be mocked)
- Verify test fixtures exist: `tests/fixtures/`
- Run with verbose output: `pytest -v`

**Docker Build Failures**
- Check Docker version: `docker --version` (need 20.10+)
- Verify Dockerfile syntax
- Check for sufficient disk space

**Kubernetes Deployment Issues**
- Verify cluster access: `kubectl cluster-info`
- Check namespace exists: `kubectl get namespace cve-analysis`
- Review pod logs: `kubectl logs -f <pod-name>`

---

## 15. Additional Resources

### Documentation
- **Primary Guide**: `.copilot/AGENT_GUIDE.md`
- **System Description**: `prompts/legendary_lidlift_v14.md`
- **Security Policy**: `SECURITY.md`
- **API Documentation**: Auto-generated from docstrings

### External References
- [NVD API 2.0 Documentation](https://nvd.nist.gov/developers/vulnerabilities)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Argo Workflows Documentation](https://argoproj.github.io/workflows/)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### Support Channels
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Security**: Report vulnerabilities privately via SECURITY.md
- **Questions**: Check documentation first, then create a discussion

---

## Version History

- **v1.0** (2025-11-16): Initial Copilot instructions created
- **Current**: v1.0

---

**Remember**: This is a **defense-only** system. All work must support defensive security purposes and must not generate exploits or offensive capabilities. When in doubt, err on the side of caution and ask for clarification.
