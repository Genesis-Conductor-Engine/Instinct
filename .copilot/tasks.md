# GitHub Copilot Tasks Configuration

## Project Tasks

### Development Tasks

- **Ingest CVE Data**
  - Command: `cve-matter ingest --source nvd --output data/cve_data.json`
  - Description: Fetch and ingest CVE data from NVD
  - Category: Data Collection

- **Run Alignment Analysis**
  - Command: `cve-matter align --method procrustes --input data/cve_data.json`
  - Description: Perform Procrustes alignment on CVE features
  - Category: Analysis

- **Run Super-Learner Prediction**
  - Command: `cve-matter arbiter --input data/cve_data.json --n-folds 5`
  - Description: Execute super-learner ensemble predictions
  - Category: Machine Learning

- **Compute Epsilon Values**
  - Command: `cve-matter refract --input data/cve_data.json --use-gpu`
  - Description: Calculate epsilon refraction values (GPU-accelerated)
  - Category: Advanced Analysis

- **Evaluate Model Evidence**
  - Command: `cve-matter evidence --input data/cve_data.json --criteria bic waic`
  - Description: Compute BIC and WAIC for model selection
  - Category: Model Evaluation

### Testing Tasks

- **Run Unit Tests**
  - Command: `pytest tests/ -v`
  - Description: Execute all unit tests
  - Category: Testing

- **Run Tests with Coverage**
  - Command: `pytest tests/ -v --cov=cve_matter --cov-report=html`
  - Description: Run tests and generate coverage report
  - Category: Testing

- **Lint Code**
  - Command: `ruff check cve_matter/ tests/`
  - Description: Check code style with ruff
  - Category: Quality

- **Format Code**
  - Command: `black cve_matter/ tests/`
  - Description: Auto-format code with black
  - Category: Quality

- **Type Check**
  - Command: `mypy cve_matter/`
  - Description: Run static type checking
  - Category: Quality

### Docker Tasks

- **Build CPU Image**
  - Command: `docker build --target cpu -t cve-matter-analysis:cpu .`
  - Description: Build CPU-only Docker image
  - Category: Containers

- **Build CUDA Image**
  - Command: `docker build --target cuda -t cve-matter-analysis:cuda .`
  - Description: Build GPU-enabled Docker image
  - Category: Containers

- **Run with Docker Compose**
  - Command: `docker-compose up cve-matter-cpu`
  - Description: Start CVE Matter with Docker Compose
  - Category: Containers

- **Scan Container with Trivy**
  - Command: `trivy image cve-matter-analysis:cpu`
  - Description: Scan Docker image for vulnerabilities
  - Category: Security

### Kubernetes Tasks

- **Apply RuntimeClass**
  - Command: `kubectl apply -f k8s/gvisor-runtime.yaml`
  - Description: Deploy gVisor RuntimeClass
  - Category: Kubernetes

- **Deploy CRD**
  - Command: `kubectl apply -f k8s/policy-trigger-crd.yaml`
  - Description: Deploy PolicyTrigger CRD
  - Category: Kubernetes

- **Deploy Webhook**
  - Command: `kubectl apply -f k8s/admission-webhook.yaml`
  - Description: Deploy admission webhook
  - Category: Kubernetes

- **Submit Argo Workflow**
  - Command: `argo submit argo/epsilon-sweep-workflow.yaml`
  - Description: Run GPU epsilon sweep workflow
  - Category: Workflows

### Terraform Tasks

- **Initialize Terraform**
  - Command: `cd terraform && terraform init`
  - Description: Initialize Terraform configuration
  - Category: Infrastructure

- **Plan Infrastructure**
  - Command: `cd terraform && terraform plan`
  - Description: Preview infrastructure changes
  - Category: Infrastructure

- **Apply Infrastructure**
  - Command: `cd terraform && terraform apply`
  - Description: Deploy GKE cluster and GPU nodes
  - Category: Infrastructure

- **Destroy Infrastructure**
  - Command: `cd terraform && terraform destroy`
  - Description: Tear down infrastructure
  - Category: Infrastructure

### Security Tasks

- **Run CodeQL Analysis**
  - Command: `codeql database analyze`
  - Description: Perform static security analysis
  - Category: Security

- **Scan Dependencies**
  - Command: `pip-audit`
  - Description: Check for vulnerable dependencies
  - Category: Security

- **Generate SBOM**
  - Command: `syft packages . -o json > sbom.json`
  - Description: Create Software Bill of Materials
  - Category: Security

## Task Categories

- **Data Collection**: CVE data ingestion and preprocessing
- **Analysis**: Statistical and alignment analysis
- **Machine Learning**: Prediction and model training
- **Advanced Analysis**: Epsilon calculations and GPU workloads
- **Model Evaluation**: Information criteria and validation
- **Testing**: Unit, integration, and system tests
- **Quality**: Code quality and formatting tools
- **Containers**: Docker builds and management
- **Security**: Vulnerability scanning and analysis
- **Kubernetes**: K8s deployment and management
- **Workflows**: Argo workflows for batch processing
- **Infrastructure**: Terraform IaC operations

## Quick Start Workflow

1. Install dependencies: `pip install -e ".[dev]"`
2. Run tests: `pytest tests/ -v`
3. Ingest data: `cve-matter ingest --output data/cve_data.json`
4. Run analysis: `cve-matter align --input data/cve_data.json`
5. Build container: `docker build --target cpu -t cve-matter-analysis:cpu .`

## Notes

- All tasks follow defensive blue-team security principles
- No offensive capabilities or cryptographic breaking included
- GPU tasks require CUDA-enabled hardware
- Kubernetes tasks require configured cluster access
- Terraform tasks require GCP credentials
