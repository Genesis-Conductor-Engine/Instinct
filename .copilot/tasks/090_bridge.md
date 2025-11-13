# Task 090: Webhook + Argo Bridge

## Goal

Implement a webhook receiver and Argo Workflows integration to enable event-driven CVE analysis pipeline execution.

## Files to Create/Edit

### New Files
- `src/bridge/__init__.py` - Bridge package initialization
- `src/bridge/webhook_server.py` - Flask/FastAPI webhook receiver
- `src/bridge/argo_client.py` - Argo Workflows client
- `src/bridge/event_handlers.py` - Event processing logic
- `k8s/webhook-deployment.yaml` - Kubernetes deployment for webhook server
- `k8s/webhook-service.yaml` - Kubernetes service
- `argo/cve-analysis-workflow.yaml` - Argo workflow definition
- `tests/bridge/test_webhook.py` - Tests for webhook server
- `tests/bridge/test_argo_client.py` - Tests for Argo client

### Supporting Files
- `requirements.txt` - Add `fastapi`, `uvicorn`, `argo-workflows`
- `config/bridge.yaml` - Bridge configuration

## Requirements

### Functional Requirements

1. **Webhook Server**
   - HTTP server to receive webhook events
   - Support GitHub webhooks (push, release)
   - Support custom CVE alert webhooks
   - Validate webhook signatures (HMAC)
   - Health check endpoint

2. **Argo Workflows Integration**
   - Submit workflows to Argo programmatically
   - Pass parameters (CVE IDs, date ranges, etc.)
   - Monitor workflow status
   - Retrieve workflow results
   - Handle workflow failures and retries

3. **Event Processing**
   - Parse incoming webhook payloads
   - Extract relevant parameters for pipeline
   - Queue events if pipeline is busy
   - Deduplicate duplicate events
   - Rate limiting and throttling

4. **Pipeline Orchestration**
   - Trigger NVD ingest on schedule or event
   - Run full analysis pipeline via Argo
   - Support partial pipeline execution
   - Pass artifacts between workflow steps
   - Store results in persistent storage

### Non-Functional Requirements

1. **Reliability**
   - Handle transient Argo API failures
   - Queue events for retry on failure
   - Idempotent workflow submissions
   - Graceful degradation

2. **Security**
   - Authenticate webhook sources
   - Secure Argo API credentials
   - Rate limit to prevent DoS
   - Audit log all events

3. **Performance**
   - Handle 100+ webhook events per hour
   - Low latency (<500ms) webhook response
   - Efficient workflow submission
   - Minimal resource overhead

### Acceptance Criteria
- [ ] Webhook server receiving and validating events
- [ ] Argo client submitting workflows
- [ ] Full pipeline workflow defined in Argo
- [ ] Event handlers for different webhook types
- [ ] Kubernetes manifests for deployment
- [ ] Health check and metrics endpoints
- [ ] Tests for webhook and Argo client
- [ ] Documentation for setup

## Implementation Guidance

```python
# src/bridge/webhook_server.py
from fastapi import FastAPI, Request, HTTPException, Header
import hmac
import hashlib
from typing import Optional

app = FastAPI(title="CVE Analysis Bridge")

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """Handle GitHub webhook events"""
    body = await request.body()
    
    # Validate signature
    if not validate_github_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")
    
    # Process event
    await handle_github_event(event_type, payload)
    
    return {"status": "accepted"}

@app.post("/webhook/cve-alert")
async def cve_alert_webhook(request: Request):
    """Handle CVE alert webhooks from external systems"""
    payload = await request.json()
    
    # Extract CVE IDs
    cve_ids = payload.get("cve_ids", [])
    
    # Submit Argo workflow
    await submit_cve_analysis_workflow(cve_ids)
    
    return {"status": "accepted", "workflow": "submitted"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cve-bridge"}

def validate_github_signature(payload: bytes, signature: str) -> bool:
    """Validate GitHub webhook signature"""
    if not signature or not WEBHOOK_SECRET:
        return False
    
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

```python
# src/bridge/argo_client.py
from argo_workflows import WorkflowsServiceApi, Configuration, ApiClient
from argo_workflows.models import (
    V1alpha1Workflow,
    V1alpha1WorkflowSpec,
    V1alpha1Template,
)

class ArgoClient:
    """Client for Argo Workflows API"""
    
    def __init__(self, namespace: str = "argo"):
        config = Configuration()
        config.host = os.environ.get("ARGO_API_HOST", "https://localhost:2746")
        self.api = WorkflowsServiceApi(ApiClient(config))
        self.namespace = namespace
    
    def submit_workflow(
        self,
        workflow_name: str,
        parameters: dict
    ) -> str:
        """Submit a workflow to Argo"""
        
        # Load workflow template
        workflow_manifest = self._load_workflow_template(workflow_name)
        
        # Set parameters
        workflow_manifest["spec"]["arguments"] = {
            "parameters": [
                {"name": k, "value": str(v)}
                for k, v in parameters.items()
            ]
        }
        
        # Submit to Argo
        response = self.api.create_workflow(
            namespace=self.namespace,
            body=workflow_manifest
        )
        
        workflow_id = response.metadata.name
        logger.info(f"Submitted workflow: {workflow_id}")
        
        return workflow_id
    
    def get_workflow_status(self, workflow_id: str) -> str:
        """Get status of a workflow"""
        workflow = self.api.get_workflow(
            namespace=self.namespace,
            name=workflow_id
        )
        return workflow.status.phase
    
    def get_workflow_logs(self, workflow_id: str) -> str:
        """Retrieve logs from a workflow"""
        logs = self.api.workflow_logs(
            namespace=self.namespace,
            name=workflow_id
        )
        return logs
```

## Argo Workflow Definition

```yaml
# argo/cve-analysis-workflow.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: cve-analysis-
spec:
  entrypoint: cve-pipeline
  
  arguments:
    parameters:
    - name: cve-ids
      value: ""
    - name: days
      value: "7"
  
  templates:
  - name: cve-pipeline
    dag:
      tasks:
      - name: ingest
        template: ingest-nvd
        arguments:
          parameters:
          - name: days
            value: "{{workflow.parameters.days}}"
      
      - name: align
        template: alignment
        dependencies: [ingest]
        arguments:
          artifacts:
          - name: cves
            from: "{{tasks.ingest.outputs.artifacts.cves}}"
      
      - name: arbiter
        template: predict-severity
        dependencies: [align]
        arguments:
          artifacts:
          - name: embeddings
            from: "{{tasks.align.outputs.artifacts.embeddings}}"
      
      - name: refractors
        template: detect-shifts
        dependencies: [align]
        arguments:
          artifacts:
          - name: embeddings
            from: "{{tasks.align.outputs.artifacts.embeddings}}"
      
      - name: evidence
        template: calculate-evidence
        dependencies: [arbiter, refractors]
        arguments:
          artifacts:
          - name: predictions
            from: "{{tasks.arbiter.outputs.artifacts.predictions}}"
  
  - name: ingest-nvd
    inputs:
      parameters:
      - name: days
    container:
      image: gcr.io/PROJECT_ID/lidlift:latest
      command: [python, -m, src.ingest.nvd_client]
      args: ["--days", "{{inputs.parameters.days}}", "--output", "/tmp/cves.jsonl"]
    outputs:
      artifacts:
      - name: cves
        path: /tmp/cves.jsonl
  
  - name: alignment
    inputs:
      artifacts:
      - name: cves
        path: /tmp/cves.jsonl
    container:
      image: gcr.io/PROJECT_ID/lidlift:latest
      command: [python, -m, src.alignment]
      args: ["--input", "/tmp/cves.jsonl", "--output", "/tmp/embeddings.npy"]
    outputs:
      artifacts:
      - name: embeddings
        path: /tmp/embeddings.npy
  
  # Additional templates for arbiter, refractors, evidence...
```

## Kubernetes Deployment

```yaml
# k8s/webhook-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cve-bridge
  namespace: cve-analysis
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cve-bridge
  template:
    metadata:
      labels:
        app: cve-bridge
    spec:
      containers:
      - name: bridge
        image: gcr.io/PROJECT_ID/cve-bridge:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: webhook-secrets
              key: secret
        - name: ARGO_API_HOST
          value: "https://argo-server.argo:2746"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Configuration

Environment variables:
- `WEBHOOK_SECRET`: Secret for validating webhooks
- `ARGO_API_HOST`: Argo Workflows API endpoint
- `ARGO_NAMESPACE`: Kubernetes namespace for workflows

## References
- Argo Workflows: https://argoproj.github.io/argo-workflows/
- FastAPI: https://fastapi.tiangolo.com/
- GitHub Webhooks: https://docs.github.com/en/webhooks
