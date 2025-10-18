# Terraform providers configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.4"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

# Configure Kubernetes provider
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

# Configure Helm provider
provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# Configure Local provider
provider "local" {
}
