# kind cluster configuration for local Kubernetes development

resource "kind_cluster" "canary" {
  name            = var.cluster_name
  wait_for_ready  = true
  kubeconfig_path = pathexpand(var.kubeconfig_path)

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    # Control plane node with ingress support
    node {
      role = "control-plane"

      # Extra port mappings for accessing services
      extra_port_mappings {
        container_port = 30000
        host_port      = 30000
        protocol       = "TCP"
      }

      extra_port_mappings {
        container_port = 30080
        host_port      = 30080
        protocol       = "TCP"
      }

      extra_port_mappings {
        container_port = 30090
        host_port      = 30090
        protocol       = "TCP"
      }

      extra_port_mappings {
        container_port = 30443
        host_port      = 30443
        protocol       = "TCP"
      }

      extra_port_mappings {
        container_port = 31000
        host_port      = 31000
        protocol       = "TCP"
      }

      # Label for ingress controller
      kubeadm_config_patches = [
        <<-EOF
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
        EOF
      ]
    }

    # Optional worker nodes (uncomment if needed)
    # node {
    #   role = "worker"
    # }

    # Networking configuration
    networking {
      api_server_address = var.kind_api_server_address
      api_server_port    = var.kind_api_server_port
      pod_subnet         = var.kind_pod_subnet
      service_subnet     = var.kind_service_subnet
    }
  }
}

# Optional: Local Docker registry for faster image pulls
resource "null_resource" "local_registry" {
  count = var.kind_create_local_registry ? 1 : 0

  provisioner "local-exec" {
    command = <<-EOT
      # Check if registry already exists
      if ! docker ps | grep -q kind-registry; then
        docker run -d --restart=always \
          -p ${var.kind_registry_port}:5000 \
          --name kind-registry \
          registry:2

        # Connect registry to kind network
        if [ "$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' kind-registry)" = 'null' ]; then
          docker network connect kind kind-registry
        fi
      fi
    EOT
  }

  depends_on = [kind_cluster.canary]
}

# Wait for cluster to be fully ready
resource "null_resource" "cluster_ready" {
  provisioner "local-exec" {
    command = <<-EOT
      echo "Waiting for cluster to be ready..."
      kubectl wait --for=condition=Ready nodes --all --timeout=300s --kubeconfig=${pathexpand(var.kubeconfig_path)}
      echo "Cluster is ready!"
    EOT
  }

  depends_on = [kind_cluster.canary]
}
