# Argo Workflows

This directory contains Argo Workflows manifests for orchestrating the CVE Matter-Analysis pipeline.

## Structure

- **WorkflowTemplates**: Reusable workflow templates
- **CronWorkflows**: Scheduled workflow executions
- **Workflows**: One-time workflow definitions
- **Events**: Event-driven workflow triggers

## Files to be Created (per tasks)

### Task 091: Argo ε-Sweep
- `workflowtemplate-tensor-macrosegments.yaml` - Main ε-sweep workflow template
- `cronworkflow-nightly.yaml` - Nightly scheduled sweep (03:00 UTC)
- `workflow-manual-sweep.yaml` - Manual trigger workflow
- `eventsource-webhook.yaml` - Webhook event source for external triggers

### Supporting Workflows
- `workflowtemplate-nvd-ingest.yaml` - NVD data ingestion workflow
- `workflowtemplate-alignment.yaml` - Positional alignment workflow
- `workflowtemplate-arbiter.yaml` - Stacked arbiter workflow
- `workflowtemplate-evidence.yaml` - Bayesian evidence calculation workflow

## Workflow Execution

```bash
# Submit one-time workflow
argo submit argo/workflowtemplate-tensor-macrosegments.yaml

# List workflows
argo list

# Get workflow status
argo get @latest

# View workflow logs
argo logs @latest

# Stop a running workflow
argo stop <workflow-name>

# Delete completed workflows
argo delete --completed
```

## Tensor Macrosegments Workflow

The main ε-sweep workflow uses tensor macrosegments:

1. **Spec Ring**: Load configuration and validate parameters
2. **Tool Ring**: Select and prepare ML tools
3. **Code Ring**: Execute compute-intensive operations (GPU workloads)
4. **Decision Ring**: Analyze results and make recommendations

Each pod is labeled with its macrosegment (`spec`, `tool`, `code`, `decision`) for policy enforcement.

## Scheduling

The nightly CronWorkflow runs at 03:00 UTC:
```yaml
schedule: "0 3 * * *"
```

This schedule:
- Ingests CVEs from the last 24 hours
- Performs alignment and arbiter training
- Runs ε-refractor grid sweep
- Calculates Bayesian evidence scores
- Stores artifacts in GCS

## Artifact Management

Workflow artifacts are stored in GCS:
- **Bucket**: `cve-analysis-artifacts`
- **Prefix**: `argo-artifacts/`
- **Retention**: 30 days

## Monitoring

Workflows export metrics to Prometheus:
- Workflow execution time
- Step duration
- Failure rate
- Resource utilization

## Security

- All compute pods labeled `macrosegment: code` for GPU access
- WorkflowTemplates use service accounts with minimal permissions
- Artifacts stored in encrypted GCS buckets
- No secrets in workflow definitions (use Kubernetes secrets)

## Example Workflow

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: epsilon-sweep-
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: epsilon-range
        value: "0.001,0.5"
      - name: grid-resolution
        value: "20"
  
  templates:
    - name: main
      steps:
        - - name: ingest
            template: nvd-ingest
        - - name: align
            template: alignment
        - - name: arbiter
            template: stacked-arbiter
        - - name: refractor
            template: epsilon-refractor
        - - name: evidence
            template: bayesian-evidence
```

## References

- [Argo Workflows Documentation](https://argoproj.github.io/workflows/)
- [Workflow Templates](https://argoproj.github.io/workflows/workflow-templates/)
- [CronWorkflows](https://argoproj.github.io/workflows/cron-workflows/)
- [Artifact Repository](https://argoproj.github.io/workflows/artifact-repository-ref/)
