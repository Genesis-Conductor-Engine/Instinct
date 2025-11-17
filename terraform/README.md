# Terraform Infrastructure

This directory contains Terraform configurations for provisioning the CVE Matter-Analysis OS infrastructure on Google Cloud Platform (GKE).

## Structure

- **Main Configuration**: Core infrastructure setup
- **GKE Cluster**: Kubernetes cluster configuration
- **Node Pools**: Default and GPU node pool definitions
- **Storage**: GCS buckets for artifacts, capsules, and logs
- **Networking**: VPC, subnets, and firewall rules
- **IAM**: Service accounts and role bindings
- **Monitoring**: Cloud Monitoring and Logging setup

## Files to be Created (per tasks)

### Core Infrastructure
- `main.tf` - Main Terraform configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Provider version constraints
- `terraform.tfvars.example` - Example variable values

### GKE Configuration
- `gke.tf` - GKE cluster definition
- `node-pools.tf` - Node pool configurations
- `workload-identity.tf` - Workload Identity setup

### Task 080: GPU Support
- `gpu.tf` - GPU node pool and accelerator configuration
- `gpu-drivers.tf` - GPU driver installation (daemonset)

### Storage and Networking
- `storage.tf` - GCS buckets for artifacts, capsules, logs
- `network.tf` - VPC and subnet configuration
- `firewall.tf` - Firewall rules

### IAM and Security
- `iam.tf` - Service accounts and IAM bindings
- `secrets.tf` - Secret Manager configurations

## Prerequisites

1. **GCP Project**: Create or identify a GCP project
2. **Service Account**: Create a service account with necessary permissions
3. **Enable APIs**:
   - Kubernetes Engine API
   - Compute Engine API
   - Cloud Storage API
   - Cloud Logging API
   - IAM API
   - Secret Manager API (if using)

4. **Terraform**: Install Terraform 1.5+
5. **gcloud CLI**: Install and configure gcloud

## Setup

```bash
# Initialize Terraform
cd terraform
terraform init

# Create terraform.tfvars from example
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Validate configuration
terraform validate

# Format Terraform files
terraform fmt -recursive

# Plan infrastructure changes
terraform plan -out=plan.tfplan

# Review the plan carefully
less plan.tfplan

# Apply infrastructure changes
terraform apply plan.tfplan
```

## Configuration Variables

Key variables to configure in `terraform.tfvars`:

```hcl
# GCP Project
project_id = "your-gcp-project-id"
region     = "us-central1"
zone       = "us-central1-a"

# GKE Cluster
cluster_name = "cve-analysis-cluster"
environment  = "production"  # or "staging", "development"

# Node Pools
default_node_pool_machine_type = "n1-standard-4"
default_node_pool_min_nodes    = 1
default_node_pool_max_nodes    = 10

# GPU Node Pool (if enabled)
gpu_node_pool_enabled          = false  # Set to true for GPU support
gpu_node_pool_machine_type     = "n1-standard-4"
gpu_accelerator_type           = "nvidia-tesla-t4"
gpu_accelerator_count          = 1
gpu_node_pool_min_nodes        = 0
gpu_node_pool_max_nodes        = 3

# Storage
capsules_bucket_name  = "cve-capsules-bucket"
artifacts_bucket_name = "cve-artifacts-bucket"
logs_bucket_name      = "cve-logs-bucket"

# Networking
network_name    = "cve-analysis-network"
subnet_name     = "cve-analysis-subnet"
subnet_cidr     = "10.0.0.0/24"
pods_cidr       = "10.1.0.0/16"
services_cidr   = "10.2.0.0/16"
```

## GKE Cluster Configuration

The GKE cluster is configured with:
- **Workload Identity**: Enabled for secure pod-to-GCP authentication
- **gVisor Runtime**: Available for enhanced container isolation
- **Binary Authorization**: Enabled for image verification (optional)
- **Network Policy**: Enabled for pod-to-pod network isolation
- **Vertical Pod Autoscaling**: Enabled for resource optimization
- **Maintenance Window**: Configured for minimal disruption

## GPU Node Pool

GPU node pool configuration (Task 080):
- **Machine Type**: n1-standard-4 (or custom)
- **Accelerator**: NVIDIA Tesla T4 (or T4, V100, A100)
- **Auto-scaling**: 0 to 3 nodes (scales to zero when idle)
- **Taints**: `nvidia.com/gpu:NoSchedule` (only GPU pods scheduled)
- **Labels**: `macrosegment: code` for policy enforcement

## Storage Buckets

Three GCS buckets are provisioned:
1. **Capsules Bucket**: Stores capsule configuration artifacts
2. **Artifacts Bucket**: Stores Argo workflow artifacts
3. **Logs Bucket**: Stores application logs (optional)

All buckets are configured with:
- Encryption at rest
- Versioning enabled
- Lifecycle policies for automatic cleanup
- IAM bindings for service accounts

## Workload Identity

Workload Identity maps Kubernetes Service Accounts to Google Service Accounts:
```
KSA: cve-pipeline@cve-analysis.serviceaccount
GSA: cve-pipeline@{project_id}.iam.gserviceaccount.com
```

This eliminates the need for node-level service account keys.

## Outputs

After applying, Terraform outputs:
- GKE cluster name and endpoint
- Cluster CA certificate
- Service account emails
- Bucket names and URLs
- Network configuration

## Maintenance

```bash
# Check current state
terraform show

# List resources
terraform state list

# View specific resource
terraform state show google_container_cluster.primary

# Update infrastructure
terraform plan -out=plan.tfplan
terraform apply plan.tfplan

# Destroy infrastructure (CAUTION)
terraform destroy
```

## Security Considerations

- **No secrets in code**: Use environment variables or Secret Manager
- **State backend**: Store Terraform state in encrypted GCS bucket
- **Least privilege**: Service accounts have minimal required permissions
- **Network isolation**: Private GKE cluster with authorized networks
- **Encryption**: All data encrypted at rest and in transit

## Cost Optimization

- GPU nodes auto-scale to zero when idle
- Use preemptible nodes for non-production workloads
- Set resource quotas to prevent cost overruns
- Monitor with Cloud Billing alerts

## Troubleshooting

**Issue**: `terraform init` fails
**Solution**: Check provider version constraints in `versions.tf`

**Issue**: `terraform apply` fails with permission errors
**Solution**: Verify service account has required IAM roles

**Issue**: GKE cluster creation timeout
**Solution**: Increase timeout in `gke.tf` or check for quota limits

**Issue**: GPU nodes not available
**Solution**: Verify GPU quota in GCP project and region

## References

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Terraform Module](https://registry.terraform.io/modules/terraform-google-modules/kubernetes-engine/google/latest)
- [GCP Best Practices](https://cloud.google.com/architecture/best-practices-for-running-cost-effective-kubernetes-applications-on-gke)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
