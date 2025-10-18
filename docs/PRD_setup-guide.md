# Product Requirements Document: DOCS: Setup Guide

---

## Document Information
**Project:** docs
**Document:** setup-guide
**Version:** 1.0.0
**Date:** 2025-10-13
**Status:** READY FOR TASK-MASTER PARSING

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
This PRD captures the requirements and implementation details for DOCS: Setup Guide.

### 1.2 Purpose
This document provides a structured specification that can be parsed by task-master to generate actionable tasks.

### 1.3 Scope
The scope includes all requirements, features, and implementation details from the original documentation.

---

## 2. REQUIREMENTS


## 3. TASKS

The following tasks have been identified for implementation:

**TASK_001** [HIGH]: [Prerequisites](#prerequisites)

**TASK_002** [HIGH]: [Infrastructure Setup](#infrastructure-setup)

**TASK_003** [HIGH]: [ArgoCD Installation](#argocd-installation)

**TASK_004** [HIGH]: [Argo Rollouts Installation](#argo-rollouts-installation)

**TASK_005** [HIGH]: [Application Deployment](#application-deployment)

**TASK_006** [HIGH]: [Verification](#verification)

**TASK_007** [MEDIUM]: **Docker** (v20.10+)

**TASK_008** [MEDIUM]: **kubectl** (v1.24+)

**TASK_009** [MEDIUM]: **kind** (for local Kubernetes cluster)

**TASK_010** [MEDIUM]: **Terraform** (v1.0+) - Optional

**TASK_011** [MEDIUM]: **Python** (3.8+) - For task management

**TASK_012** [MEDIUM]: role: control-plane

**TASK_013** [MEDIUM]: containerPort: 80

**TASK_014** [MEDIUM]: containerPort: 443

**TASK_015** [MEDIUM]: host: argocd.example.com

**TASK_016** [MEDIUM]: Navigate to https://localhost:8080

**TASK_017** [MEDIUM]: Username: `admin`

**TASK_018** [MEDIUM]: Password: (from step 4)

**TASK_019** [MEDIUM]: `argocd/applications/blue-green-app.yaml`

**TASK_020** [MEDIUM]: `argocd/applications/canary-app.yaml`

**TASK_021** [MEDIUM]: [Blue-Green Deployment Guide](blue-green-guide.md)

**TASK_022** [MEDIUM]: [Canary Deployment Guide](canary-guide.md)

**TASK_023** [MEDIUM]: [Troubleshooting Guide](troubleshooting.md)

**TASK_024** [MEDIUM]: Verify Docker installation and version

**TASK_025** [MEDIUM]: Verify kubectl installation and version

**TASK_026** [MEDIUM]: Install kind for local Kubernetes cluster

**TASK_027** [MEDIUM]: Verify Terraform installation

**TASK_028** [MEDIUM]: Verify Python 3.8+ installation

**TASK_029** [MEDIUM]: Verify Helm installation

**TASK_030** [MEDIUM]: Create kind cluster with ingress configuration

**TASK_031** [MEDIUM]: Verify cluster is running and accessible

**TASK_032** [MEDIUM]: Configure kubectl context for new cluster

**TASK_033** [MEDIUM]: Verify nodes are Ready status

**TASK_034** [MEDIUM]: Create argocd namespace

**TASK_035** [MEDIUM]: Install ArgoCD manifests

**TASK_036** [MEDIUM]: Wait for ArgoCD pods to be ready

**TASK_037** [MEDIUM]: Expose ArgoCD server via port-forward or ingress

**TASK_038** [MEDIUM]: Retrieve ArgoCD initial admin password

**TASK_039** [MEDIUM]: Login to ArgoCD UI and CLI

**TASK_040** [MEDIUM]: Change ArgoCD admin password

**TASK_041** [MEDIUM]: Create argo-rollouts namespace

**TASK_042** [MEDIUM]: Install Argo Rollouts controller

**TASK_043** [MEDIUM]: Install kubectl argo rollouts plugin

**TASK_044** [MEDIUM]: Verify Argo Rollouts installation

**TASK_045** [MEDIUM]: Start Argo Rollouts dashboard

**TASK_046** [MEDIUM]: Install ingress-nginx controller

**TASK_047** [MEDIUM]: Wait for ingress controller to be ready

**TASK_048** [MEDIUM]: Verify ingress class is available

**TASK_049** [MEDIUM]: Test ingress with sample application

**TASK_050** [MEDIUM]: Create monitoring namespace

**TASK_051** [MEDIUM]: Add Prometheus Helm repository

**TASK_052** [MEDIUM]: Install Prometheus with Helm

**TASK_053** [MEDIUM]: Verify Prometheus pods are running

**TASK_054** [MEDIUM]: Expose Prometheus via port-forward

**TASK_055** [MEDIUM]: Verify Prometheus is scraping metrics

**TASK_056** [MEDIUM]: Create application namespaces

**TASK_057** [MEDIUM]: Create ArgoCD project for rollouts

**TASK_058** [MEDIUM]: Update Git repository URLs in application manifests

**TASK_059** [MEDIUM]: Deploy blue-green application via ArgoCD

**TASK_060** [MEDIUM]: Deploy canary application via ArgoCD

**TASK_061** [MEDIUM]: Wait for ArgoCD to sync applications

**TASK_062** [MEDIUM]: Verify all applications are healthy

**TASK_063** [MEDIUM]: Check ArgoCD application status

**TASK_064** [MEDIUM]: Check rollout status for all deployments

**TASK_065** [MEDIUM]: Verify pod status in all namespaces

**TASK_066** [MEDIUM]: Check rollout health via kubectl plugin

**TASK_067** [MEDIUM]: Configure /etc/hosts for local access

**TASK_068** [MEDIUM]: Test blue-green active endpoint

**TASK_069** [MEDIUM]: Test blue-green preview endpoint

**TASK_070** [MEDIUM]: Test canary endpoint

**TASK_071** [MEDIUM]: Verify ingress resources are configured

**TASK_072** [MEDIUM]: Check ingress routing is working

**TASK_073** [MEDIUM]: Navigate to task-manager directory

**TASK_074** [MEDIUM]: Create Python virtual environment

**TASK_075** [MEDIUM]: Install task-manager dependencies

**TASK_076** [MEDIUM]: Parse PRD to generate tasks.json

**TASK_077** [MEDIUM]: View task progress report

**TASK_078** [MEDIUM]: Navigate to task-master directory

**TASK_079** [MEDIUM]: Create Python virtual environment for task-master

**TASK_080** [MEDIUM]: Install task-master dependencies

**TASK_081** [MEDIUM]: Test task master execution

**TASK_082** [MEDIUM]: [ArgoCD Documentation](https://argo-cd.readthedocs.io/)

**TASK_083** [MEDIUM]: [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)

**TASK_084** [MEDIUM]: [Kubernetes Documentation](https://kubernetes.io/docs/)

**TASK_085** [MEDIUM]: [kind Documentation](https://kind.sigs.k8s.io/)


## 4. DETAILED SPECIFICATIONS

### 4.1 Original Content

The following sections contain the original documentation:


#### Setup Guide

# Setup Guide

Complete guide for setting up the Blue-Green and Canary deployment system.


#### Table Of Contents

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [ArgoCD Installation](#argocd-installation)
4. [Argo Rollouts Installation](#argo-rollouts-installation)
5. [Application Deployment](#application-deployment)
6. [Verification](#verification)


#### Prerequisites

## Prerequisites


#### Required Tools

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


#### Infrastructure Setup

## Infrastructure Setup


#### Option 1 Using Kind Local Development 

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


#### Option 2 Using Terraform

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

#### For Cloud Providers Configure Kubeconfig

# For cloud providers, configure kubeconfig
terraform output kubeconfig > ~/.kube/config
```


#### Argocd Installation

## ArgoCD Installation


#### 1 Install Argocd

### 1. Install ArgoCD

```bash

#### Create Namespace

# Create namespace
kubectl create namespace monitoring


#### Install Argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```


#### 2 Wait For Argocd To Be Ready

### 2. Wait for ArgoCD to be ready

```bash
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=300s
```


#### 3 Expose Argocd Server

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


#### 4 Get Initial Admin Password

### 4. Get Initial Admin Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```


#### 5 Login To Argocd

### 5. Login to ArgoCD

**Via UI:**
- Navigate to https://localhost:8080
- Username: `admin`
- Password: (from step 4)

**Via CLI:**

```bash

#### Install Argocd Cli

# Install ArgoCD CLI
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd


#### Login

# Login
argocd login localhost:8080 --username admin --password <password> --insecure
```


#### 6 Change Admin Password

### 6. Change Admin Password

```bash
argocd account update-password --current-password <old> --new-password <new>
```


#### Argo Rollouts Installation

## Argo Rollouts Installation


#### 1 Install Argo Rollouts Controller

### 1. Install Argo Rollouts Controller

```bash

#### Install Argo Rollouts

# Install Argo Rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```


#### 2 Install Kubectl Plugin

### 2. Install Kubectl Plugin

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```


#### 3 Verify Installation

### 3. Verify Installation

```bash
kubectl argo rollouts version
```


#### 4 Access Rollouts Dashboard Optional 

### 4. Access Rollouts Dashboard (Optional)

```bash
kubectl argo rollouts dashboard
```

Access at: http://localhost:3100


#### Ingress Nginx Installation

## Ingress-nginx Installation


#### 1 Install Ingress Controller

### 1. Install Ingress Controller

**For kind:**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/kind/deploy.yaml
```

**For cloud providers:**

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
```


#### 2 Wait For Ingress Controller

### 2. Wait for Ingress Controller

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```


#### Prometheus Installation Optional 

## Prometheus Installation (Optional)


#### 1 Install Prometheus

### 1. Install Prometheus

```bash

#### Add Helm Repo

# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update


#### Install Prometheus

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  -n monitoring \
  --set alertmanager.enabled=false \
  --set pushgateway.enabled=false
```


#### 2 Verify Installation

### 2. Verify Installation

```bash
kubectl get pods -n monitoring
```


#### 3 Access Prometheus

### 3. Access Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus-server 9090:80
```

Access at: http://localhost:9090


#### Application Deployment

## Application Deployment


#### 1 Create Namespaces

### 1. Create Namespaces

```bash
kubectl apply -f k8s/namespaces/namespace.yaml
```


#### 2 Create Argocd Project

### 2. Create ArgoCD Project

```bash
kubectl apply -f argocd/projects/rollouts-project.yaml
```


#### 3 Update Git Repository Urls

### 3. Update Git Repository URLs

Edit the following files and replace the repository URL with your own:

- `argocd/applications/blue-green-app.yaml`
- `argocd/applications/canary-app.yaml`

```yaml
spec:
  source:
    repoURL: https://github.com/YOUR-ORG/YOUR-REPO.git  # Update this
```


#### 4 Deploy Applications

### 4. Deploy Applications

```bash

#### Deploy Blue Green Application

# Deploy Blue-Green Application
kubectl apply -f argocd/applications/blue-green-app.yaml


#### Deploy Canary Application

# Deploy Canary Application
kubectl apply -f argocd/applications/canary-app.yaml
```


#### 5 Wait For Sync

### 5. Wait for Sync

```bash

#### Watch Blue Green App

# Watch Blue-Green app
argocd app get blue-green-app --watch


#### Watch Canary App

# Watch Canary app
argocd app get canary-app --watch
```


#### Verification

## Verification


#### 1 Check Application Status

### 1. Check Application Status

```bash

#### Argocd Applications

# ArgoCD applications
kubectl get applications -n argocd


#### Rollouts

# Rollouts
kubectl get rollouts -A


#### Pods

# Pods
kubectl get pods -n canary-blue-green
kubectl get pods -n canary-canary
```


#### 2 Check Rollout Health

### 2. Check Rollout Health

```bash

#### Blue Green

# Blue-Green
kubectl argo rollouts get rollout blue-green-app -n canary-blue-green


#### Canary

# Canary
kubectl argo rollouts get rollout canary-app -n canary-canary
```


#### 3 Configure Etc Hosts

### 3. Configure /etc/hosts

Add these entries to `/etc/hosts` (or Windows equivalent):

```
127.0.0.1 blue-green.local
127.0.0.1 blue-green-preview.local
127.0.0.1 canary.local
```

**For kind clusters:**

```bash

#### Get The Kind Node Ip

# Get the kind node IP
docker inspect rollouts-cluster-control-plane \
  --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'


#### Use That Ip Instead Of 127 0 0 1 In Etc Hosts If Needed

# Use that IP instead of 127.0.0.1 in /etc/hosts if needed
```


#### 4 Test Applications

### 4. Test Applications

```bash

#### Test Blue Green Active 

# Test Blue-Green (Active)
curl http://blue-green.local


#### Test Blue Green Preview 

# Test Blue-Green (Preview)
curl http://blue-green-preview.local


#### Test Canary

# Test Canary
curl http://canary.local
```


#### 5 Verify Ingress

### 5. Verify Ingress

```bash

#### Check Ingress Resources

# Check ingress resources
kubectl get ingress -n canary-blue-green
kubectl get ingress -n canary-canary


#### Describe Ingress For Details

# Describe ingress for details
kubectl describe ingress blue-green-ingress -n canary-blue-green
```


#### Task Management Setup

## Task Management Setup


#### 1 Set Up Task Manager

### 1. Set Up Task Manager

```bash
cd task-manager
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```


#### 2 Parse Prd

### 2. Parse PRD

```bash
./venv/bin/python prd_parser.py ../PRD.md --output tasks.json
```


#### 3 View Tasks

### 3. View Tasks

```bash
./venv/bin/python task_manager.py --tasks tasks.json progress
```


#### 4 Set Up Task Master

### 4. Set Up Task Master

```bash
cd ../task-master
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


#### Troubleshooting

## Troubleshooting


#### Argocd Not Starting

### ArgoCD Not Starting

```bash

#### Check Pod Logs

# Check pod logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server


#### Check Events

# Check events
kubectl get events -n argocd --sort-by='.lastTimestamp'


#### Restart Argocd

# Restart ArgoCD
kubectl rollout restart deployment argocd-server -n argocd
```


#### Argo Rollouts Not Installing

### Argo Rollouts Not Installing

```bash

#### Check Controller Logs

# Check controller logs
kubectl logs -n argo-rollouts -l app.kubernetes.io/name=argo-rollouts


#### Verify Crds

# Verify CRDs
kubectl get crd | grep rollouts
```


#### Ingress Not Working

### Ingress Not Working

```bash

#### Check Ingress Controller

# Check ingress controller
kubectl get pods -n ingress-nginx


#### Check Ingress Logs

# Check ingress logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller


#### Verify Ingress Class

# Verify ingress class
kubectl get ingressclass
```


#### Applications Not Syncing

### Applications Not Syncing

```bash

#### Check Application Status

# Check application status
argocd app get <app-name>


#### Force Sync

# Force sync
argocd app sync <app-name> --force


#### Check Repository Access

# Check repository access
argocd repo list
```


#### Next Steps

## Next Steps

- [Blue-Green Deployment Guide](blue-green-guide.md)
- [Canary Deployment Guide](canary-guide.md)
- [Troubleshooting Guide](troubleshooting.md)


#### 6 Implementation Phases

## 6. Implementation Phases


#### Phase 1 Prerequisites Verification Priority Critical 

### Phase 1: Prerequisites Verification (Priority: Critical)
- [ ] Verify Docker installation and version
- [ ] Verify kubectl installation and version
- [ ] Install kind for local Kubernetes cluster
- [ ] Verify Terraform installation
- [ ] Verify Python 3.8+ installation
- [ ] Verify Helm installation


#### Phase 2 Infrastructure Setup Priority Critical 

### Phase 2: Infrastructure Setup (Priority: Critical)
- [ ] Create kind cluster with ingress configuration
- [ ] Verify cluster is running and accessible
- [ ] Configure kubectl context for new cluster
- [ ] Verify nodes are Ready status


#### Phase 3 Core Components Installation Priority Critical 

### Phase 3: Core Components Installation (Priority: Critical)
- [ ] Create argocd namespace
- [ ] Install ArgoCD manifests
- [ ] Wait for ArgoCD pods to be ready
- [ ] Expose ArgoCD server via port-forward or ingress
- [ ] Retrieve ArgoCD initial admin password
- [ ] Login to ArgoCD UI and CLI
- [ ] Change ArgoCD admin password


#### Phase 4 Argo Rollouts Installation Priority Critical 

### Phase 4: Argo Rollouts Installation (Priority: Critical)
- [ ] Create argo-rollouts namespace
- [ ] Install Argo Rollouts controller
- [ ] Install kubectl argo rollouts plugin
- [ ] Verify Argo Rollouts installation
- [ ] Start Argo Rollouts dashboard


#### Phase 5 Ingress Setup Priority High 

### Phase 5: Ingress Setup (Priority: High)
- [ ] Install ingress-nginx controller
- [ ] Wait for ingress controller to be ready
- [ ] Verify ingress class is available
- [ ] Test ingress with sample application


#### Phase 6 Monitoring Setup Priority Medium 

### Phase 6: Monitoring Setup (Priority: Medium)
- [ ] Create monitoring namespace
- [ ] Add Prometheus Helm repository
- [ ] Install Prometheus with Helm
- [ ] Verify Prometheus pods are running
- [ ] Expose Prometheus via port-forward
- [ ] Verify Prometheus is scraping metrics


#### Phase 7 Application Deployment Priority High 

### Phase 7: Application Deployment (Priority: High)
- [ ] Create application namespaces
- [ ] Create ArgoCD project for rollouts
- [ ] Update Git repository URLs in application manifests
- [ ] Deploy blue-green application via ArgoCD
- [ ] Deploy canary application via ArgoCD
- [ ] Wait for ArgoCD to sync applications
- [ ] Verify all applications are healthy


#### Phase 8 Verification And Testing Priority High 

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


#### Phase 9 Task Management Setup Priority Medium 

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


#### References

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kind Documentation](https://kind.sigs.k8s.io/)


---

## 5. TECHNICAL REQUIREMENTS

### 5.1 Dependencies
- All dependencies from original documentation apply
- Standard development environment
- Required tools and libraries as specified

### 5.2 Compatibility
- Compatible with existing infrastructure
- Follows project standards and conventions

---

## 6. SUCCESS CRITERIA

### 6.1 Functional Success Criteria
- All identified tasks completed successfully
- All requirements implemented as specified
- All tests passing

### 6.2 Quality Success Criteria
- Code meets quality standards
- Documentation is complete and accurate
- No critical issues remaining

---

## 7. IMPLEMENTATION PLAN

### Phase 1: Preparation
- Review all requirements and tasks
- Set up development environment
- Gather necessary resources

### Phase 2: Implementation
- Execute tasks in priority order
- Follow best practices
- Test incrementally

### Phase 3: Validation
- Run comprehensive tests
- Validate against requirements
- Document completion

---

## 8. TASK-MASTER INTEGRATION

### How to Parse This PRD

```bash
# Parse this PRD with task-master
task-master parse-prd --input="{doc_name}_PRD.md"

# List generated tasks
task-master list

# Start execution
task-master next
```

### Expected Task Generation
Task-master should generate approximately {len(tasks)} tasks from this PRD.

---

## 9. APPENDIX

### 9.1 References
- Original document: {doc_name}.md
- Project: {project_name}

### 9.2 Change History
| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | {datetime.now().strftime('%Y-%m-%d')} | Initial PRD conversion |

---

*End of PRD*
*Generated by MD-to-PRD Converter*
