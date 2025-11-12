# Kubernetes Deployment Guide

## Overview

CVE Matter-Analysis OS uses Kubernetes with enhanced security features:

- **gVisor RuntimeClass** for sandboxed execution
- **AdmissionWebhook** for policy enforcement
- **PolicyTrigger CRD** for custom security policies
- **Argo Workflows** for batch GPU workloads

## Prerequisites

- Kubernetes cluster (v1.25+)
- `kubectl` configured
- `argo` CLI (for workflows)
- gVisor runtime installed on nodes

## Installation

### 1. Deploy gVisor RuntimeClass

```bash
kubectl apply -f k8s/gvisor-runtime.yaml
```

This creates:
- RuntimeClass resource for gVisor
- Example pod using the runtime

Verify:
```bash
kubectl get runtimeclass
```

### 2. Deploy PolicyTrigger CRD

```bash
kubectl apply -f k8s/policy-trigger-crd.yaml
```

This creates:
- Custom Resource Definition for PolicyTrigger
- Example PolicyTrigger for critical CVEs

Verify:
```bash
kubectl get crd policytriggers.cve-matter.security.io
kubectl get policytriggers
```

### 3. Deploy Admission Webhook

```bash
# Generate webhook certificates (if not done)
./scripts/generate-webhook-certs.sh

# Create secret with certificates
kubectl create secret tls webhook-certs \
  --cert=webhook.crt \
  --key=webhook.key

# Deploy webhook
kubectl apply -f k8s/admission-webhook.yaml
```

Verify:
```bash
kubectl get validatingwebhookconfigurations
kubectl get pods -l app=cve-matter-webhook
```

## Running Workloads

### Basic Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cve-analysis
spec:
  runtimeClassName: gvisor
  containers:
  - name: cve-matter
    image: cve-matter-analysis:cpu
    command: ["cve-matter", "ingest"]
    args: ["--output", "/data/cves.json"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
```

### Job for CVE Analysis

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cve-alignment-job
spec:
  template:
    spec:
      runtimeClassName: gvisor
      containers:
      - name: cve-matter
        image: cve-matter-analysis:cpu
        command: ["cve-matter", "align"]
        args:
          - "--method"
          - "procrustes"
          - "--input"
          - "/data/cves.json"
        volumeMounts:
        - name: data
          mountPath: /data
      restartPolicy: Never
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: cve-data-pvc
```

### GPU Workload

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cve-epsilon-gpu
spec:
  containers:
  - name: cve-matter
    image: cve-matter-analysis:cuda
    command: ["cve-matter", "refract"]
    args:
      - "--input"
      - "/data/cves.json"
      - "--use-gpu"
    resources:
      limits:
        nvidia.com/gpu: 1
    volumeMounts:
    - name: data
      mountPath: /data
  nodeSelector:
    cloud.google.com/gke-accelerator: nvidia-tesla-t4
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  volumes:
  - name: data
    emptyDir: {}
```

## Argo Workflows

### Install Argo Workflows

```bash
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml
```

### Submit Epsilon Sweep Workflow

```bash
argo submit argo/epsilon-sweep-workflow.yaml -n argo

# Watch workflow
argo watch @latest -n argo

# Get workflow logs
argo logs @latest -n argo
```

### List Workflows

```bash
argo list -n argo
```

## PolicyTrigger Usage

### Create a PolicyTrigger

```yaml
apiVersion: cve-matter.security.io/v1
kind: PolicyTrigger
metadata:
  name: high-cve-quarantine
spec:
  severity: HIGH
  action: quarantine
  threshold: 7.0
  targets:
    - production
  notificationChannels:
    - slack-security
```

Apply:
```bash
kubectl apply -f policy-trigger.yaml
```

### View PolicyTriggers

```bash
kubectl get policytriggers
kubectl describe policytrigger high-cve-quarantine
```

### Update PolicyTrigger Status

PolicyTriggers have a status subresource that can be updated by controllers:

```yaml
status:
  lastTriggered: "2024-11-12T19:00:00Z"
  triggeredCount: 5
  state: active
```

## ConfigMaps and Secrets

### Create Configuration

```bash
kubectl create configmap cve-matter-config \
  --from-file=config/matter.yaml
```

### Create NVD API Key Secret

```bash
kubectl create secret generic nvd-api-key \
  --from-literal=api-key=your-nvd-api-key
```

Use in pod:
```yaml
env:
- name: NVD_API_KEY
  valueFrom:
    secretKeyRef:
      name: nvd-api-key
      key: api-key
```

## Persistent Storage

### Create PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cve-data-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

## Monitoring and Logging

### View Logs

```bash
# Pod logs
kubectl logs <pod-name>

# Follow logs
kubectl logs -f <pod-name>

# Previous logs (if pod restarted)
kubectl logs <pod-name> --previous
```

### Resource Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods

# Specific pod
kubectl top pod <pod-name>
```

## Security Best Practices

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cve-matter-netpol
spec:
  podSelector:
    matchLabels:
      app: cve-matter
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: cve-matter
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: cve-matter
  - ports:
    - protocol: TCP
      port: 443  # HTTPS for NVD API
```

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cve-matter
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cve-matter-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cve-matter-role
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["create", "get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cve-matter-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: cve-matter-role
subjects:
- kind: ServiceAccount
  name: cve-matter-sa
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check logs
kubectl logs <pod-name>
```

### gVisor Issues

```bash
# Verify RuntimeClass
kubectl get runtimeclass gvisor

# Check node labels
kubectl get nodes --show-labels | grep runtime

# Test with simple pod
kubectl run test --image=busybox --restart=Never --overrides='{"spec":{"runtimeClassName":"gvisor"}}' -- sleep 3600
```

### Admission Webhook Issues

```bash
# Check webhook configuration
kubectl get validatingwebhookconfigurations cve-matter-admission-webhook -o yaml

# Check webhook pods
kubectl get pods -l app=cve-matter-webhook

# Check webhook logs
kubectl logs -l app=cve-matter-webhook

# Test webhook
kubectl apply -f test-policytrigger.yaml
```

### GPU Not Available

```bash
# Check GPU nodes
kubectl get nodes -l cloud.google.com/gke-accelerator

# Check NVIDIA device plugin
kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds

# Check node allocatable resources
kubectl describe node <gpu-node-name> | grep nvidia.com/gpu
```

## Cleanup

```bash
# Delete all CVE Matter resources
kubectl delete -f k8s/

# Delete Argo workflows
argo delete -n argo --all

# Delete namespace
kubectl delete namespace cve-matter
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [gVisor Runtime](https://gvisor.dev/docs/user_guide/quick_start/kubernetes/)
- [Argo Workflows](https://argoproj.github.io/argo-workflows/)
- [Custom Resource Definitions](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)
