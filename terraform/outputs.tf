# Terraform outputs
output "cluster_name" {
  description = "Name of the Kubernetes cluster"
  value       = var.cluster_name
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "argocd_url" {
  description = "ArgoCD URL"
  value       = "http://argocd.${var.domain_suffix}:30080"
}

output "rollouts_url" {
  description = "Argo Rollouts Dashboard URL"
  value       = "http://rollouts.${var.domain_suffix}:31000"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = var.enable_monitoring ? "http://grafana.${var.domain_suffix}:30090" : null
}

output "ingress_nginx_url" {
  description = "Ingress NGINX URL"
  value       = "http://localhost:30000"
}

output "namespaces" {
  description = "Created namespaces"
  value = {
    argocd     = kubernetes_namespace.argocd.metadata[0].name
    rollouts   = kubernetes_namespace.argocd_rollouts.metadata[0].name
    monitoring = var.enable_monitoring ? kubernetes_namespace.monitoring.metadata[0].name : null
    ingress    = kubernetes_namespace.ingress_nginx.metadata[0].name
    blue_green = kubernetes_namespace.blue_green.metadata[0].name
    canary     = kubernetes_namespace.canary.metadata[0].name
  }
}

output "helm_releases" {
  description = "Deployed Helm releases"
  value = {
    argocd         = helm_release.argocd.name
    argocd_rollouts = helm_release.argocd_rollouts.name
    prometheus     = var.enable_monitoring ? helm_release.prometheus.name : null
    ingress_nginx  = helm_release.ingress_nginx.name
  }
}

output "service_endpoints" {
  description = "Service endpoints"
  value = {
    argocd_server = {
      host = "argocd.${var.domain_suffix}"
      port = 30080
      protocol = "http"
    }
    rollouts_dashboard = {
      host = "rollouts.${var.domain_suffix}"
      port = 31000
      protocol = "http"
    }
    grafana = var.enable_monitoring ? {
      host = "grafana.${var.domain_suffix}"
      port = 30090
      protocol = "http"
    } : null
    ingress_nginx = {
      host = "localhost"
      port = 30000
      protocol = "http"
    }
  }
}

output "kubeconfig_path" {
  description = "Path to kubeconfig file"
  value       = var.kubeconfig_path
}

output "domain_suffix" {
  description = "Domain suffix for local development"
  value       = var.domain_suffix
}

output "resource_limits" {
  description = "Applied resource limits"
  value       = var.resource_limits
}

output "monitoring_enabled" {
  description = "Whether monitoring is enabled"
  value       = var.enable_monitoring
}

output "logging_enabled" {
  description = "Whether logging is enabled"
  value       = var.enable_logging
}

output "tracing_enabled" {
  description = "Whether distributed tracing is enabled"
  value       = var.enable_tracing
}

output "backup_configuration" {
  description = "Backup configuration"
  value = {
    enabled = var.backup_enabled
    schedule = var.backup_schedule
    retention_days = var.backup_retention_days
  }
}

# kind cluster specific outputs
output "kind_cluster_name" {
  description = "Name of the kind cluster"
  value       = kind_cluster.canary.name
}

output "kind_cluster_endpoint" {
  description = "Kubernetes API endpoint for kind cluster"
  value       = kind_cluster.canary.endpoint
}

output "kind_cluster_client_certificate" {
  description = "Client certificate for kind cluster authentication"
  value       = kind_cluster.canary.client_certificate
  sensitive   = true
}

output "kind_cluster_client_key" {
  description = "Client key for kind cluster authentication"
  value       = kind_cluster.canary.client_key
  sensitive   = true
}

output "kind_cluster_ca_certificate" {
  description = "CA certificate for kind cluster"
  value       = kind_cluster.canary.cluster_ca_certificate
  sensitive   = true
}

output "kind_kubeconfig" {
  description = "Kubeconfig for kind cluster"
  value       = kind_cluster.canary.kubeconfig
  sensitive   = true
}

output "local_registry_url" {
  description = "Local Docker registry URL (if enabled)"
  value       = var.kind_create_local_registry ? "localhost:${var.kind_registry_port}" : null
}
