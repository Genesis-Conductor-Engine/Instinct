# Kubernetes Manifests

This directory contains Kubernetes manifests for deploying the CVE Matter-Analysis OS to GKE.

## Structure

- **CRDs**: Custom Resource Definitions for PolicyTrigger and related resources
- **Deployments**: Application deployment manifests
- **Services**: Service definitions for networking
- **ConfigMaps**: Configuration data
- **Secrets**: Secret placeholders (actual secrets managed via GitHub Secrets)
- **RuntimeClasses**: gVisor and GPU runtime class definitions
- **AdmissionWebhook**: Webhook configuration for policy enforcement
- **GPU Jobs**: Job manifests for GPU-accelerated workloads
- **NetworkPolicies**: Network isolation policies

## Files to be Created (per tasks)

### Task 090: Admission Webhook & Triggers
- `crd-policytrigger.yaml` - PolicyTrigger Custom Resource Definition
- `deploy-webhook.yaml` - Admission webhook deployment
- `webhook-config.yaml` - Webhook configuration
- `service-webhook.yaml` - Webhook service definition

### Task 080: GPU Support
- `gpu-job.yaml` - GPU-enabled job template
- `runtime-class-gpu.yaml` - GPU runtime class definition

### Base Infrastructure
- `namespace.yaml` - cve-analysis namespace
- `runtime-class-gvisor.yaml` - gVisor runtime class
- `deployment-pipeline.yaml` - Main pipeline deployment
- `service-pipeline.yaml` - Pipeline service
- `configmap-matter.yaml` - Matter configuration from config/matter.yaml
- `networkpolicy-default-deny.yaml` - Default deny network policy

## Deployment

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply runtime classes
kubectl apply -f k8s/runtime-class-gvisor.yaml

# Apply CRDs
kubectl apply -f k8s/crd-policytrigger.yaml

# Deploy admission webhook
kubectl apply -f k8s/deploy-webhook.yaml
kubectl apply -f k8s/service-webhook.yaml
kubectl apply -f k8s/webhook-config.yaml

# Deploy main application
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n cve-analysis
kubectl get services -n cve-analysis
```

## Security Considerations

- All pods run with gVisor runtime class by default for enhanced isolation
- GPU pods require explicit `macrosegment: code` label
- AdmissionWebhook enforces PolicyTrigger rules
- Network policies restrict pod-to-pod communication
- Workload Identity maps KSA to GSA (no node-level keys)

## Testing

```bash
# Dry run manifests
kubectl apply -f k8s/ --dry-run=client

# Validate manifests
kubectl apply -f k8s/ --dry-run=server --validate=true

# Check differences
kubectl diff -f k8s/
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GKE Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [gVisor Runtime](https://gvisor.dev/docs/user_guide/quick_start/kubernetes/)
- [Admission Webhooks](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
