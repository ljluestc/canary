# Hosts configuration for ${cluster_name}
# Add these entries to your /etc/hosts file for local development

# ArgoCD
127.0.0.1 argocd.local

# Argo Rollouts Dashboard
127.0.0.1 rollouts.local

# Grafana (if monitoring is enabled)
127.0.0.1 grafana.local

# Blue-Green Deployment
127.0.0.1 blue-green.local
127.0.0.1 blue-green-preview.local

# Canary Deployment
127.0.0.1 canary.local

# Additional services
127.0.0.1 prometheus.local
127.0.0.1 alertmanager.local
127.0.0.1 jaeger.local
127.0.0.1 elasticsearch.local
127.0.0.1 kibana.local

# Application domains
127.0.0.1 app.local
127.0.0.1 api.local
127.0.0.1 web.local
127.0.0.1 admin.local

# Development domains
127.0.0.1 dev.local
127.0.0.1 staging.local
127.0.0.1 test.local
