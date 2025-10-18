# Terraform variables
variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "cluster_name" {
  description = "Name of the Kubernetes cluster"
  type        = string
  default     = "canary-cluster"
}

variable "namespace_prefix" {
  description = "Prefix for namespaces"
  type        = string
  default     = "canary"
}

variable "argocd_version" {
  description = "ArgoCD version"
  type        = string
  default     = "stable"
}

variable "argocd_rollouts_version" {
  description = "Argo Rollouts version"
  type        = string
  default     = "latest"
}

variable "prometheus_version" {
  description = "Prometheus Operator version"
  type        = string
  default     = "latest"
}

variable "ingress_nginx_version" {
  description = "Ingress NGINX version"
  type        = string
  default     = "4.8.3"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "domain_suffix" {
  description = "Domain suffix for local development"
  type        = string
  default     = "local"
}

variable "node_port_range" {
  description = "Range for NodePort services"
  type        = string
  default     = "30000-32767"
}

variable "resource_limits" {
  description = "Resource limits for components"
  type = object({
    cpu_limit    = string
    memory_limit = string
    cpu_request  = string
    memory_request = string
  })
  default = {
    cpu_limit     = "1000m"
    memory_limit  = "1Gi"
    cpu_request   = "100m"
    memory_request = "128Mi"
  }
}

variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable logging stack"
  type        = bool
  default     = true
}

variable "enable_tracing" {
  description = "Enable distributed tracing"
  type        = bool
  default     = false
}

variable "backup_enabled" {
  description = "Enable backup for persistent data"
  type        = bool
  default     = false
}

variable "backup_schedule" {
  description = "Cron schedule for backups"
  type        = string
  default     = "0 2 * * *"
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

# kind cluster specific variables
variable "kind_api_server_address" {
  description = "API server address for kind cluster"
  type        = string
  default     = "127.0.0.1"
}

variable "kind_api_server_port" {
  description = "API server port for kind cluster"
  type        = number
  default     = 6443
}

variable "kind_pod_subnet" {
  description = "Pod subnet CIDR for kind cluster"
  type        = string
  default     = "10.244.0.0/16"
}

variable "kind_service_subnet" {
  description = "Service subnet CIDR for kind cluster"
  type        = string
  default     = "10.96.0.0/12"
}

variable "kind_create_local_registry" {
  description = "Create a local Docker registry for kind"
  type        = bool
  default     = true
}

variable "kind_registry_port" {
  description = "Port for local Docker registry"
  type        = number
  default     = 5001
}

variable "kind_image" {
  description = "kind node Docker image version"
  type        = string
  default     = "kindest/node:v1.27.3"
}
