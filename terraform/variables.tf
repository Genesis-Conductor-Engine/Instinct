variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "GKE Cluster Name"
  type        = string
  default     = "cve-matter-cluster"
}

variable "network_name" {
  description = "VPC Network Name"
  type        = string
  default     = "cve-matter-network"
}

variable "subnet_name" {
  description = "Subnet Name"
  type        = string
  default     = "cve-matter-subnet"
}

variable "subnet_cidr" {
  description = "Subnet CIDR"
  type        = string
  default     = "10.0.0.0/24"
}

variable "enable_gpu" {
  description = "Enable GPU node pool"
  type        = bool
  default     = true
}

variable "gpu_type" {
  description = "GPU type for node pool"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_node_count" {
  description = "Number of GPU nodes"
  type        = number
  default     = 1
}

variable "cpu_node_count" {
  description = "Number of CPU nodes"
  type        = number
  default     = 2
}
