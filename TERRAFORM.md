# Terraform Infrastructure Guide

## Overview

The Terraform configuration deploys a complete GKE (Google Kubernetes Engine) infrastructure for running CVE Matter-Analysis OS with optional GPU support.

## Architecture

- **GKE Cluster** with gVisor support for enhanced security
- **CPU Node Pool** (n2-standard-4) for general workloads
- **GPU Node Pool** (nvidia-tesla-t4) for accelerated epsilon calculations
- **Private VPC** with secondary IP ranges for pods and services
- **Workload Identity** enabled for secure GCP API access
- **Shielded Nodes** for additional security

## Prerequisites

1. **Google Cloud SDK** installed and configured
2. **Terraform** >= 1.0 installed
3. **GCP Project** with required APIs enabled:
   - Kubernetes Engine API
   - Compute Engine API
   - Cloud Resource Manager API

4. **IAM Permissions**:
   - `roles/container.admin`
   - `roles/compute.admin`
   - `roles/iam.serviceAccountAdmin`

## Setup

### 1. Configure GCS Backend (Optional)

Create a GCS bucket for Terraform state:

```bash
gsutil mb gs://cve-matter-terraform-state
gsutil versioning set on gs://cve-matter-terraform-state
```

### 2. Create terraform.tfvars

```hcl
project_id      = "your-gcp-project-id"
region          = "us-central1"
zone            = "us-central1-a"
cluster_name    = "cve-matter-cluster"
enable_gpu      = true
gpu_type        = "nvidia-tesla-t4"
cpu_node_count  = 2
gpu_node_count  = 1
```

### 3. Initialize Terraform

```bash
cd terraform
terraform init
```

### 4. Plan Infrastructure

```bash
terraform plan
```

Review the plan to ensure it matches your expectations.

### 5. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm.

## Post-Deployment

### Configure kubectl

```bash
gcloud container clusters get-credentials cve-matter-cluster \
  --zone us-central1-a \
  --project your-gcp-project-id
```

### Verify Cluster

```bash
kubectl get nodes
kubectl get namespaces
```

### Install NVIDIA GPU Drivers (for GPU nodes)

```bash
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded-latest.yaml
```

### Deploy gVisor RuntimeClass

```bash
kubectl apply -f ../k8s/gvisor-runtime.yaml
```

## Resource Details

### Network Configuration

- **VPC**: Custom VPC with controlled routing
- **Subnet**: `/24` primary CIDR
- **Pod CIDR**: `/16` secondary range (10.1.0.0/16)
- **Service CIDR**: `/16` secondary range (10.2.0.0/16)

### Node Pools

#### CPU Node Pool
- Machine Type: n2-standard-4 (4 vCPU, 16GB RAM)
- Disk: 100GB standard persistent disk
- Runtime: gVisor enabled
- Auto-scaling: Configurable
- Auto-repair: Enabled
- Auto-upgrade: Enabled

#### GPU Node Pool
- Machine Type: n1-standard-4 (4 vCPU, 15GB RAM)
- GPU: 1x NVIDIA Tesla T4
- Disk: 100GB standard persistent disk
- Taint: `nvidia.com/gpu=true:NoSchedule`
- Auto-repair: Enabled
- Auto-upgrade: Enabled

### Security Features

1. **Private Nodes**: Nodes have no external IPs
2. **Shielded Nodes**: Secure boot and integrity monitoring
3. **Workload Identity**: Pod-level IAM authentication
4. **Network Policies**: Enabled for pod-to-pod security
5. **Binary Authorization**: Can be configured post-deployment

## Cost Optimization

### Reduce Costs

1. **Preemptible Nodes**: Add to node pool configuration
2. **Autoscaling**: Enable cluster autoscaler
3. **Regional Clusters**: Use zonal clusters (as configured)
4. **Right-sizing**: Adjust machine types based on workload

### Estimated Monthly Costs (us-central1)

- **CPU Node Pool** (2x n2-standard-4): ~$240/month
- **GPU Node Pool** (1x n1-standard-4 + T4): ~$450/month
- **Networking**: ~$50/month
- **Storage**: Variable based on usage

**Total**: ~$740/month (approximate)

## Scaling

### Scale Node Pools

```bash
# Scale CPU nodes
gcloud container clusters resize cve-matter-cluster \
  --node-pool cpu-node-pool \
  --num-nodes 4 \
  --zone us-central1-a

# Scale GPU nodes
gcloud container clusters resize cve-matter-cluster \
  --node-pool gpu-node-pool \
  --num-nodes 2 \
  --zone us-central1-a
```

### Enable Autoscaling

Add to node pool configuration:

```hcl
autoscaling {
  min_node_count = 1
  max_node_count = 10
}
```

## Maintenance

### Update Cluster

```bash
# Update control plane
gcloud container clusters upgrade cve-matter-cluster \
  --master \
  --zone us-central1-a

# Update node pools
gcloud container clusters upgrade cve-matter-cluster \
  --node-pool cpu-node-pool \
  --zone us-central1-a
```

### Backup

Terraform state is backed up in GCS (if configured).

For cluster backup, use Velero or GKE Backup:

```bash
# Enable GKE Backup
gcloud container clusters update cve-matter-cluster \
  --enable-backup-restore \
  --zone us-central1-a
```

## Cleanup

### Destroy Infrastructure

```bash
terraform destroy
```

**Warning**: This will delete all resources including:
- GKE cluster and all workloads
- Node pools
- VPC network and subnets

Ensure you have backups before destroying!

### Manual Cleanup

If Terraform destroy fails, manually delete:

1. GKE cluster via Cloud Console
2. Persistent disks
3. Load balancers
4. VPC network

## Troubleshooting

### Issue: Insufficient Quota

**Error**: `Quota 'NVIDIA_T4_GPUS' exceeded`

**Solution**: Request quota increase in GCP Console:
- Navigate to IAM & Admin > Quotas
- Filter for "GPUs (all regions)"
- Request increase

### Issue: Cluster Creation Timeout

**Solution**: 
- Increase timeout in Terraform configuration
- Check GCP service health status
- Verify IAM permissions

### Issue: Nodes Not Ready

**Solution**:
```bash
# Check node status
kubectl get nodes -o wide

# Check node events
kubectl describe node <node-name>

# Check system pods
kubectl get pods -n kube-system
```

## Advanced Configuration

### Enable Binary Authorization

```hcl
binary_authorization {
  evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
}
```

### Enable GKE Backup

```hcl
addons_config {
  gke_backup_agent_config {
    enabled = true
  }
}
```

### Configure Node Taints

```hcl
taint {
  key    = "dedicated"
  value  = "gpu"
  effect = "NoSchedule"
}
```

## Security Checklist

- [ ] Enable private cluster
- [ ] Configure authorized networks for master access
- [ ] Enable Workload Identity
- [ ] Enable Shielded Nodes
- [ ] Configure network policies
- [ ] Set up Pod Security Standards
- [ ] Enable binary authorization
- [ ] Configure Cloud Armor for ingress
- [ ] Set up logging and monitoring
- [ ] Rotate cluster credentials regularly

## References

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Security Hardening](https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster)
