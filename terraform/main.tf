# Terraform configuration for Kubernetes cluster setup
# Note: Provider and terraform configuration is in providers.tf

# Variables (duplicates removed - see variables.tf)

# Namespaces
# All namespaces depend on the kind cluster being ready
resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "${var.namespace_prefix}-argocd"
    labels = {
      "app.kubernetes.io/name"    = "argocd"
      "app.kubernetes.io/part-of" = "canary-deployment"
    }
  }

  depends_on = [null_resource.cluster_ready]
}

resource "kubernetes_namespace" "argocd_rollouts" {
  metadata {
    name = "${var.namespace_prefix}-rollouts"
    labels = {
      "app.kubernetes.io/name"    = "argocd-rollouts"
      "app.kubernetes.io/part-of" = "canary-deployment"
    }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "${var.namespace_prefix}-monitoring"
    labels = {
      "app.kubernetes.io/name"    = "monitoring"
      "app.kubernetes.io/part-of" = "canary-deployment"
    }
  }
}

resource "kubernetes_namespace" "ingress_nginx" {
  metadata {
    name = "${var.namespace_prefix}-ingress-nginx"
    labels = {
      "app.kubernetes.io/name"    = "ingress-nginx"
      "app.kubernetes.io/part-of" = "canary-deployment"
    }
  }
}

resource "kubernetes_namespace" "blue_green" {
  metadata {
    name = "${var.namespace_prefix}-blue-green"
    labels = {
      "app.kubernetes.io/name"    = "blue-green"
      "app.kubernetes.io/part-of" = "canary-deployment"
    }
  }
}

resource "kubernetes_namespace" "canary" {
  metadata {
    name = "${var.namespace_prefix}-canary"
    labels = {
      "app.kubernetes.io/name"    = "canary"
      "app.kubernetes.io/part-of" = "canary-deployment"
    }
  }
}

# ArgoCD Helm Chart
resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = var.argocd_version
  namespace  = kubernetes_namespace.argocd.metadata[0].name

  values = [
    yamlencode({
      global = {
        domain = "argocd.local"
      }
      server = {
        service = {
          type = "NodePort"
          nodePorts = {
            http = 30080
          }
        }
        ingress = {
          enabled = true
          ingressClassName = "nginx"
          hosts = ["argocd.local"]
          tls = []
        }
        config = {
          "url" = "https://argocd.local"
        }
      }
      configs = {
        cm = {
          "application.instanceLabelKey" = "argocd.argoproj.io/instance"
        }
      }
    })
  ]

  depends_on = [helm_release.ingress_nginx]
}

# Argo Rollouts Helm Chart
resource "helm_release" "argocd_rollouts" {
  name       = "argo-rollouts"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-rollouts"
  version    = var.argocd_rollouts_version
  namespace  = kubernetes_namespace.argocd_rollouts.metadata[0].name

  values = [
    yamlencode({
      dashboard = {
        enabled = true
        service = {
          type = "NodePort"
          nodePorts = {
            http = 31000
          }
        }
        ingress = {
          enabled = true
          ingressClassName = "nginx"
          hosts = ["rollouts.local"]
          tls = []
        }
      }
    })
  ]

  depends_on = [helm_release.ingress_nginx]
}

# Prometheus Operator Helm Chart
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = var.prometheus_version
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    yamlencode({
      grafana = {
        service = {
          type = "NodePort"
          nodePorts = {
            grafana = 30090
          }
        }
        ingress = {
          enabled = true
          ingressClassName = "nginx"
          hosts = ["grafana.local"]
          tls = []
        }
        adminPassword = "admin"
      }
      prometheus = {
        prometheusSpec = {
          serviceMonitorSelectorNilUsesHelmValues = false
          ruleSelectorNilUsesHelmValues = false
        }
      }
    })
  ]

  depends_on = [helm_release.ingress_nginx]
}

# Ingress NGINX Helm Chart
resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = var.ingress_nginx_version
  namespace  = kubernetes_namespace.ingress_nginx.metadata[0].name

  values = [
    yamlencode({
      controller = {
        service = {
          type = "NodePort"
          nodePorts = {
            http = 30000
            https = 30443
          }
        }
        config = {
          "use-forwarded-headers" = "true"
          "compute-full-forwarded-for" = "true"
        }
      }
    })
  ]
}

# Local file for hosts configuration
resource "local_file" "hosts_config" {
  content = templatefile("${path.module}/templates/hosts.tpl", {
    cluster_name = var.cluster_name
  })
  filename = "${path.module}/hosts_config.txt"
}

# Outputs (moved to outputs.tf)
# All Helm releases now depend on the kind cluster being ready
# This ensures the cluster exists before any Kubernetes resources are created
