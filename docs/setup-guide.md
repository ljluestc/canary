# Setup Guide

Complete guide for setting up the Blue-Green and Canary deployment system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [ArgoCD Installation](#argocd-installation)
4. [Argo Rollouts Installation](#argo-rollouts-installation)
5. [Application Deployment](#application-deployment)
6. [Verification](#verification)

## Prerequisites

### Required Tools

- **Docker** (v20.10+)
  ```bash
  docker --version
  ```

- **kubectl** (v1.24+)
  ```bash
  kubectl version --client
  ```

- **kind** (for local Kubernetes cluster)
  ```bash
  kind --version
  ```

  Install if not present:
  ```bash
  curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
  chmod +x ./kind
  sudo mv ./kind /usr/local/bin/kind
  ```

- **Terraform** (v1.0+) - Optional
  ```bash
  terraform --version
  ```

- **Python** (3.8+) - For task management
  ```bash
  python3 --version
  ```

## Infrastructure Setup

### Option 1: Using kind (Local Development)

1. Create kind cluster:

```bash
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: rollouts-cluster
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF
```

2. Verify cluster:

```bash
kubectl cluster-info --context kind-rollouts-cluster
kubectl get nodes
```

### Option 2: Using Terraform

1. Navigate to terraform directory:

```bash
cd terraform
```

2. Initialize Terraform:

```bash
terraform init
```

3. Review and apply:

```bash
terraform plan
terraform apply -auto-approve
```

4. Configure kubectl:

```bash
# For cloud providers, configure kubeconfig
terraform output kubeconfig > ~/.kube/config
```

## ArgoCD Installation

### 1. Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2. Wait for ArgoCD to be ready

```bash
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=300s
```

### 3. Expose ArgoCD Server

**Option A: Port Forward (Development)**

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Access at: https://localhost:8080

**Option B: Ingress (Production)**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
  - host: argocd.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
```

### 4. Get Initial Admin Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

### 5. Login to ArgoCD

**Via UI:**
- Navigate to https://localhost:8080
- Username: `admin`
- Password: (from step 4)

**Via CLI:**

```bash
# Install ArgoCD CLI
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# Login
argocd login localhost:8080 --username admin --password <password> --insecure
```

### 6. Change Admin Password

```bash
argocd account update-password --current-password <old> --new-password <new>
```

## Argo Rollouts Installation

### 1. Install Argo Rollouts Controller

```bash
# Create namespace
kubectl create namespace argo-rollouts

# Install Argo Rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### 2. Install Kubectl Plugin

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

### 3. Verify Installation

```bash
kubectl argo rollouts version
```

### 4. Access Rollouts Dashboard (Optional)

```bash
kubectl argo rollouts dashboard
```

Access at: http://localhost:3100

## Ingress-nginx Installation

### 1. Install Ingress Controller

**For kind:**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/kind/deploy.yaml
```

**For cloud providers:**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
```

### 2. Wait for Ingress Controller

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

## Prometheus Installation (Optional)

### 1. Install Prometheus

```bash
# Create namespace
kubectl create namespace monitoring

# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  -n monitoring \
  --set alertmanager.enabled=false \
  --set pushgateway.enabled=false
```

### 2. Verify Installation

```bash
kubectl get pods -n monitoring
```

### 3. Access Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus-server 9090:80
```

Access at: http://localhost:9090

## Application Deployment

### 1. Create Namespaces

```bash
kubectl apply -f k8s/namespaces/namespace.yaml
```

### 2. Create ArgoCD Project

```bash
kubectl apply -f argocd/projects/rollouts-project.yaml
```

### 3. Update Git Repository URLs

Edit the following files and replace the repository URL with your own:

- `argocd/applications/blue-green-app.yaml`
- `argocd/applications/canary-app.yaml`

```yaml
spec:
  source:
    repoURL: https://github.com/YOUR-ORG/YOUR-REPO.git  # Update this
```

### 4. Deploy Applications

```bash
# Deploy Blue-Green Application
kubectl apply -f argocd/applications/blue-green-app.yaml

# Deploy Canary Application
kubectl apply -f argocd/applications/canary-app.yaml
```

### 5. Wait for Sync

```bash
# Watch Blue-Green app
argocd app get blue-green-app --watch

# Watch Canary app
argocd app get canary-app --watch
```

## Verification

### 1. Check Application Status

```bash
# ArgoCD applications
kubectl get applications -n argocd

# Rollouts
kubectl get rollouts -A

# Pods
kubectl get pods -n canary-blue-green
kubectl get pods -n canary-canary
```

### 2. Check Rollout Health

```bash
# Blue-Green
kubectl argo rollouts get rollout blue-green-app -n canary-blue-green

# Canary
kubectl argo rollouts get rollout canary-app -n canary-canary
```

### 3. Configure /etc/hosts

Add these entries to `/etc/hosts` (or Windows equivalent):

```
127.0.0.1 blue-green.local
127.0.0.1 blue-green-preview.local
127.0.0.1 canary.local
```

**For kind clusters:**

```bash
# Get the kind node IP
docker inspect rollouts-cluster-control-plane \
  --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

# Use that IP instead of 127.0.0.1 in /etc/hosts if needed
```

### 4. Test Applications

```bash
# Test Blue-Green (Active)
curl http://blue-green.local

# Test Blue-Green (Preview)
curl http://blue-green-preview.local

# Test Canary
curl http://canary.local
```

### 5. Verify Ingress

```bash
# Check ingress resources
kubectl get ingress -n canary-blue-green
kubectl get ingress -n canary-canary

# Describe ingress for details
kubectl describe ingress blue-green-ingress -n canary-blue-green
```

## Task Management Setup

### 1. Set Up Task Manager

```bash
cd task-manager
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Parse PRD

```bash
./venv/bin/python prd_parser.py ../PRD.md --output tasks.json
```

### 3. View Tasks

```bash
./venv/bin/python task_manager.py --tasks tasks.json progress
```

### 4. Set Up Task Master

```bash
cd ../task-master
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Troubleshooting

### ArgoCD Not Starting

```bash
# Check pod logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server

# Check events
kubectl get events -n argocd --sort-by='.lastTimestamp'

# Restart ArgoCD
kubectl rollout restart deployment argocd-server -n argocd
```

### Argo Rollouts Not Installing

```bash
# Check controller logs
kubectl logs -n argo-rollouts -l app.kubernetes.io/name=argo-rollouts

# Verify CRDs
kubectl get crd | grep rollouts
```

### Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify ingress class
kubectl get ingressclass
```

### Applications Not Syncing

```bash
# Check application status
argocd app get <app-name>

# Force sync
argocd app sync <app-name> --force

# Check repository access
argocd repo list
```

## Next Steps

- [Blue-Green Deployment Guide](blue-green-guide.md)
- [Canary Deployment Guide](canary-guide.md)
- [Troubleshooting Guide](troubleshooting.md)

## 6. Implementation Phases

### Phase 1: Prerequisites Verification (Priority: Critical)
- [ ] Verify Docker installation and version
- [ ] Verify kubectl installation and version
- [ ] Install kind for local Kubernetes cluster
- [ ] Verify Terraform installation
- [ ] Verify Python 3.8+ installation
- [ ] Verify Helm installation

### Phase 2: Infrastructure Setup (Priority: Critical)
- [ ] Create kind cluster with ingress configuration
- [ ] Verify cluster is running and accessible
- [ ] Configure kubectl context for new cluster
- [ ] Verify nodes are Ready status

### Phase 3: Core Components Installation (Priority: Critical)
- [ ] Create argocd namespace
- [ ] Install ArgoCD manifests
- [ ] Wait for ArgoCD pods to be ready
- [ ] Expose ArgoCD server via port-forward or ingress
- [ ] Retrieve ArgoCD initial admin password
- [ ] Login to ArgoCD UI and CLI
- [ ] Change ArgoCD admin password

### Phase 4: Argo Rollouts Installation (Priority: Critical)
- [ ] Create argo-rollouts namespace
- [ ] Install Argo Rollouts controller
- [ ] Install kubectl argo rollouts plugin
- [ ] Verify Argo Rollouts installation
- [ ] Start Argo Rollouts dashboard

### Phase 5: Ingress Setup (Priority: High)
- [ ] Install ingress-nginx controller
- [ ] Wait for ingress controller to be ready
- [ ] Verify ingress class is available
- [ ] Test ingress with sample application

### Phase 6: Monitoring Setup (Priority: Medium)
- [ ] Create monitoring namespace
- [ ] Add Prometheus Helm repository
- [ ] Install Prometheus with Helm
- [ ] Verify Prometheus pods are running
- [ ] Expose Prometheus via port-forward
- [ ] Verify Prometheus is scraping metrics

### Phase 7: Application Deployment (Priority: High)
- [ ] Create application namespaces
- [ ] Create ArgoCD project for rollouts
- [ ] Update Git repository URLs in application manifests
- [ ] Deploy blue-green application via ArgoCD
- [ ] Deploy canary application via ArgoCD
- [ ] Wait for ArgoCD to sync applications
- [ ] Verify all applications are healthy

### Phase 8: Verification and Testing (Priority: High)
- [ ] Check ArgoCD application status
- [ ] Check rollout status for all deployments
- [ ] Verify pod status in all namespaces
- [ ] Check rollout health via kubectl plugin
- [ ] Configure /etc/hosts for local access
- [ ] Test blue-green active endpoint
- [ ] Test blue-green preview endpoint
- [ ] Test canary endpoint
- [ ] Verify ingress resources are configured
- [ ] Check ingress routing is working

### Phase 9: Task Management Setup (Priority: Medium)
- [ ] Navigate to task-manager directory
- [ ] Create Python virtual environment
- [ ] Install task-manager dependencies
- [ ] Parse PRD to generate tasks.json
- [ ] View task progress report
- [ ] Navigate to task-master directory
- [ ] Create Python virtual environment for task-master
- [ ] Install task-master dependencies
- [ ] Test task master execution

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kind Documentation](https://kind.sigs.k8s.io/)
