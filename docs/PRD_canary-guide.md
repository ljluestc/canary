# Product Requirements Document: DOCS: Canary Guide

---

## Document Information
**Project:** docs
**Document:** canary-guide
**Version:** 1.0.0
**Date:** 2025-10-13
**Status:** READY FOR TASK-MASTER PARSING

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
This PRD captures the requirements and implementation details for DOCS: Canary Guide.

### 1.2 Purpose
This document provides a structured specification that can be parsed by task-master to generate actionable tasks.

### 1.3 Scope
The scope includes all requirements, features, and implementation details from the original documentation.

---

## 2. REQUIREMENTS


## 3. TASKS

The following tasks have been identified for implementation:

**TASK_001** [MEDIUM]: Reduce deployment risk through gradual rollout

**TASK_002** [MEDIUM]: Enable automated rollback based on metrics

**TASK_003** [MEDIUM]: Minimize blast radius of faulty deployments

**TASK_004** [MEDIUM]: Increase deployment confidence with data-driven decisions

**TASK_005** [MEDIUM]: Achieve safe production releases

**TASK_006** [MEDIUM]: Progressive traffic shifting implemented (10% → 25% → 50% → 75% → 100%)

**TASK_007** [MEDIUM]: Automated analysis running at each step

**TASK_008** [MEDIUM]: Automatic rollback on metric failures

**TASK_009** [MEDIUM]: Zero-downtime during rollout

**TASK_010** [MEDIUM]: Rollback time < 2 minutes

**TASK_011** [MEDIUM]: setWeight: 10

**TASK_012** [MEDIUM]: pause: {duration: 2m}

**TASK_013** [MEDIUM]: templateName: success-rate

**TASK_014** [MEDIUM]: setWeight: 25

**TASK_015** [MEDIUM]: pause: {duration: 2m}

**TASK_016** [MEDIUM]: `maxSurge`: Maximum additional pods during rollout

**TASK_017** [MEDIUM]: `maxUnavailable`: Minimum available pods

**TASK_018** [MEDIUM]: `stableService`: Service for stable version

**TASK_019** [MEDIUM]: `canaryService`: Service for canary version

**TASK_020** [MEDIUM]: `trafficRouting`: How traffic is split

**TASK_021** [MEDIUM]: `steps`: Progression stages with weights and analysis

**TASK_022** [MEDIUM]: name: success-rate

**TASK_023** [MEDIUM]: name: error-rate

**TASK_024** [MEDIUM]: Uses ingress controller annotations

**TASK_025** [MEDIUM]: `canary-weight` annotation set by Argo Rollouts

**TASK_026** [MEDIUM]: Supports nginx, ALB, Istio

**TASK_027** [MEDIUM]: Uses Istio VirtualServices

**TASK_028** [MEDIUM]: More fine-grained control

**TASK_029** [MEDIUM]: Additional traffic management features

**TASK_030** [HIGH]: **Initial State**: 100% traffic to stable version

**TASK_031** [HIGH]: **New Version Deployed**: Canary pods start

**TASK_032** [MEDIUM]: Traffic shifts to 10% canary

**TASK_033** [MEDIUM]: Pause for 2 minutes

**TASK_034** [MEDIUM]: Run analysis

**TASK_035** [MEDIUM]: If pass → continue, if fail → rollback

**TASK_036** [HIGH]: **Step 2 (25%)**: Increase to 25%, analyze

**TASK_037** [HIGH]: **Step 3 (50%)**: Increase to 50%, analyze

**TASK_038** [HIGH]: **Step 4 (75%)**: Increase to 75%, analyze

**TASK_039** [HIGH]: **Step 5 (100%)**: Full promotion complete

**TASK_040** [HIGH]: **Cleanup**: Scale down stable version

**TASK_041** [MEDIUM]: Threshold: >= 0.95 (95% success rate)

**TASK_042** [MEDIUM]: Threshold: <= 0.05 (5% error rate)

**TASK_043** [MEDIUM]: Threshold: <= 0.5 seconds

**TASK_044** [MEDIUM]: name: custom-metric

**TASK_045** [MEDIUM]: setWeight: 10

**TASK_046** [MEDIUM]: pause: {duration: 2m}

**TASK_047** [MEDIUM]: templateName: success-rate

**TASK_048** [MEDIUM]: templateName: latency-check

**TASK_049** [MEDIUM]: templateName: custom-business-metrics

**TASK_050** [MEDIUM]: name: service-name

**TASK_051** [MEDIUM]: Review application metrics available

**TASK_052** [MEDIUM]: Identify key metrics for analysis (error rate, latency, etc.)

**TASK_053** [MEDIUM]: Determine appropriate traffic split percentages

**TASK_054** [MEDIUM]: Calculate pause durations for analysis

**TASK_055** [MEDIUM]: Assess Prometheus metric collection

**TASK_056** [MEDIUM]: Plan canary rollout steps

**TASK_057** [MEDIUM]: Create rollout manifest with canary strategy

**TASK_058** [MEDIUM]: Define stable and canary services

**TASK_059** [MEDIUM]: Configure traffic routing (nginx/istio)

**TASK_060** [MEDIUM]: Create AnalysisTemplate with Prometheus queries

**TASK_061** [MEDIUM]: Set up success criteria for each metric

**TASK_062** [MEDIUM]: Configure rollout steps with weights and pauses

**TASK_063** [MEDIUM]: Set maxSurge and maxUnavailable parameters

**TASK_064** [MEDIUM]: Configure ingress for traffic management

**TASK_065** [MEDIUM]: Verify Prometheus is installed and running

**TASK_066** [MEDIUM]: Configure application to export metrics

**TASK_067** [MEDIUM]: Set up ServiceMonitor for metric scraping

**TASK_068** [MEDIUM]: Test Prometheus queries return data

**TASK_069** [MEDIUM]: Verify metric labels match AnalysisTemplate

**TASK_070** [MEDIUM]: Set up Grafana dashboards for visualization

**TASK_071** [MEDIUM]: Configure alerting rules

**TASK_072** [MEDIUM]: Create namespace if not exists

**TASK_073** [MEDIUM]: Deploy AnalysisTemplate

**TASK_074** [MEDIUM]: Deploy rollout manifest

**TASK_075** [MEDIUM]: Deploy services (stable and canary)

**TASK_076** [MEDIUM]: Deploy ingress configuration

**TASK_077** [MEDIUM]: Wait for initial pods to be ready

**TASK_078** [MEDIUM]: Verify stable service has endpoints

**TASK_079** [MEDIUM]: Test application via ingress

**TASK_080** [MEDIUM]: Verify metrics are being collected

**TASK_081** [MEDIUM]: Update container image to new version

**TASK_082** [MEDIUM]: Commit and push to Git repository

**TASK_083** [MEDIUM]: Wait for ArgoCD to sync

**TASK_084** [MEDIUM]: Monitor rollout status

**TASK_085** [MEDIUM]: Verify canary pods created

**TASK_086** [MEDIUM]: Check traffic split at 10%

**TASK_087** [MEDIUM]: Wait for analysis to run

**TASK_088** [MEDIUM]: Review analysis results

**TASK_089** [MEDIUM]: Verify automatic progression to 25%

**TASK_090** [MEDIUM]: Access canary endpoint to generate traffic

**TASK_091** [MEDIUM]: Run load tests against application

**TASK_092** [MEDIUM]: Monitor Prometheus metrics in real-time

**TASK_093** [MEDIUM]: Verify AnalysisRun is created

**TASK_094** [MEDIUM]: Check analysis success/failure status

**TASK_095** [MEDIUM]: Review metric thresholds

**TASK_096** [MEDIUM]: Validate automatic progression works

**TASK_097** [MEDIUM]: Test automatic rollback on failure

**TASK_098** [MEDIUM]: Verify rollback completes successfully

**TASK_099** [MEDIUM]: Monitor traffic at each weight (10%, 25%, 50%, 75%)

**TASK_100** [MEDIUM]: Watch for error rate increases

**TASK_101** [MEDIUM]: Track latency metrics

**TASK_102** [MEDIUM]: Monitor resource utilization

**TASK_103** [MEDIUM]: Check application logs for errors

**TASK_104** [MEDIUM]: Verify database performance

**TASK_105** [MEDIUM]: Monitor external API calls

**TASK_106** [MEDIUM]: Check cache hit rates

**TASK_107** [MEDIUM]: Review custom business metrics

**TASK_108** [MEDIUM]: Wait for 100% traffic to canary

**TASK_109** [MEDIUM]: Verify all traffic switched

**TASK_110** [MEDIUM]: Run production smoke tests

**TASK_111** [MEDIUM]: Execute full integration test suite

**TASK_112** [MEDIUM]: Monitor production metrics

**TASK_113** [MEDIUM]: Check error rates remain low

**TASK_114** [MEDIUM]: Verify latency is acceptable

**TASK_115** [MEDIUM]: Confirm stable version scaled down

**TASK_116** [MEDIUM]: Clean up old ReplicaSets

**TASK_117** [MEDIUM]: Trigger analysis failure intentionally

**TASK_118** [MEDIUM]: Verify automatic rollback occurs

**TASK_119** [MEDIUM]: Check traffic reverts to stable version

**TASK_120** [MEDIUM]: Measure rollback duration

**TASK_121** [MEDIUM]: Verify application remains available

**TASK_122** [MEDIUM]: Test manual abort command

**TASK_123** [MEDIUM]: Practice emergency rollback procedure

**TASK_124** [MEDIUM]: Document rollback steps in runbook

**TASK_125** [MEDIUM]: Fine-tune traffic split percentages

**TASK_126** [MEDIUM]: Adjust pause durations

**TASK_127** [MEDIUM]: Optimize analysis query intervals

**TASK_128** [MEDIUM]: Add additional metrics to analysis

**TASK_129** [MEDIUM]: Configure multiple analysis templates

**TASK_130** [MEDIUM]: Implement baseline vs canary comparison

**TASK_131** [MEDIUM]: Set up automated notifications

**TASK_132** [MEDIUM]: Create custom dashboards

**TASK_133** [MEDIUM]: Implement experiment-based canary (A/B testing)

**TASK_134** [MEDIUM]: Configure header-based routing

**TASK_135** [MEDIUM]: Set up canary with Istio service mesh

**TASK_136** [MEDIUM]: Implement traffic mirroring/shadowing

**TASK_137** [MEDIUM]: Configure ALB for AWS environments

**TASK_138** [MEDIUM]: Set up multi-stage canary (dev→staging→prod)

**TASK_139** [MEDIUM]: Implement automated approval gates

**TASK_140** [MEDIUM]: Create deployment templates

**TASK_141** [MEDIUM]: Start with small percentages (5-10%)

**TASK_142** [MEDIUM]: Increase gradually (10% → 25% → 50% → 75%)

**TASK_143** [MEDIUM]: Spend more time at critical thresholds

**TASK_144** [MEDIUM]: Allow enough time for metrics to stabilize

**TASK_145** [MEDIUM]: Use multiple metrics (error rate, latency, custom)

**TASK_146** [MEDIUM]: Set realistic thresholds based on baselines

**TASK_147** [MEDIUM]: Use appropriate time windows (5m, 10m)

**TASK_148** [MEDIUM]: Include both technical and business metrics

**TASK_149** [MEDIUM]: Short pauses for low-risk changes (1-2 minutes)

**TASK_150** [MEDIUM]: Longer pauses for high-risk changes (5-10 minutes)

**TASK_151** [MEDIUM]: Allow time for metric collection and analysis

**TASK_152** [MEDIUM]: Consider peak vs off-peak traffic patterns

**TASK_153** [MEDIUM]: Automatic: Failed analysis, health checks

**TASK_154** [MEDIUM]: Manual: Stakeholder decision, user reports

**TASK_155** [MEDIUM]: Set clear rollback criteria

**TASK_156** [MEDIUM]: Practice rollback procedures regularly

**TASK_157** [MEDIUM]: Set appropriate `maxSurge` to control resource usage

**TASK_158** [MEDIUM]: Use `maxUnavailable: 0` for zero-downtime

**TASK_159** [MEDIUM]: Monitor cluster capacity during rollout

**TASK_160** [MEDIUM]: Consider pod disruption budgets

**TASK_161** [MEDIUM]: Verify Prometheus is accessible from cluster

**TASK_162** [MEDIUM]: Check PromQL queries return data

**TASK_163** [MEDIUM]: Verify service labels match queries

**TASK_164** [MEDIUM]: Check metric names and labels

**TASK_165** [MEDIUM]: Test queries in Prometheus UI

**TASK_166** [MEDIUM]: Verify time windows are appropriate

**TASK_167** [MEDIUM]: Check ingress controller supports canary annotations

**TASK_168** [MEDIUM]: Verify ingress name matches rollout config

**TASK_169** [MEDIUM]: Check ingress controller logs

**TASK_170** [MEDIUM]: Verify canary service has endpoints

**TASK_171** [MEDIUM]: Test ingress annotations manually

**TASK_172** [MEDIUM]: Check if analysis is running: `kubectl get analysisrun`

**TASK_173** [MEDIUM]: Review analysis results for failures

**TASK_174** [MEDIUM]: Check pause duration hasn't expired

**TASK_175** [MEDIUM]: Verify no manual pause was issued

**TASK_176** [MEDIUM]: Check rollout controller logs

**TASK_177** [MEDIUM]: Verify analysis template has failure conditions

**TASK_178** [MEDIUM]: Check `successCondition` is correct (result[0] >= threshold)

**TASK_179** [MEDIUM]: Review analysisrun status and message

**TASK_180** [MEDIUM]: Check rollout strategy includes analysis

**TASK_181** [MEDIUM]: Verify analysis interval and count settings

**TASK_182** [MEDIUM]: Verify application exports metrics

**TASK_183** [MEDIUM]: Check ServiceMonitor configuration

**TASK_184** [MEDIUM]: Verify Prometheus is scraping application

**TASK_185** [MEDIUM]: Check metric names and labels

**TASK_186** [MEDIUM]: Test metrics endpoint: `curl http://pod-ip:port/metrics`

**TASK_187** [MEDIUM]: name: baseline-hash

**TASK_188** [MEDIUM]: name: canary-hash

**TASK_189** [MEDIUM]: name: success-rate-comparison

**TASK_190** [MEDIUM]: **Rollout Duration**: Total time for canary to complete

**TASK_191** [MEDIUM]: **Analysis Pass Rate**: % of analysis runs that pass

**TASK_192** [MEDIUM]: **Rollback Frequency**: Number of automatic rollbacks

**TASK_193** [MEDIUM]: **Time to Detect Issues**: Time from deployment to rollback

**TASK_194** [MEDIUM]: **Traffic Distribution**: Actual vs expected traffic split

**TASK_195** [MEDIUM]: **Resource Utilization**: CPU/Memory during rollout

**TASK_196** [MEDIUM]: Rollout status timeline

**TASK_197** [MEDIUM]: Traffic weight over time

**TASK_198** [MEDIUM]: Error rate comparison (stable vs canary)

**TASK_199** [MEDIUM]: Latency comparison

**TASK_200** [MEDIUM]: Analysis run results

**TASK_201** [MEDIUM]: Resource utilization

**TASK_202** [MEDIUM]: [Argo Rollouts Canary Documentation](https://argoproj.github.io/argo-rollouts/features/canary/)

**TASK_203** [MEDIUM]: [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)

**TASK_204** [MEDIUM]: [Traffic Management](https://argoproj.github.io/argo-rollouts/features/traffic-management/)

**TASK_205** [MEDIUM]: [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)


## 4. DETAILED SPECIFICATIONS

### 4.1 Original Content

The following sections contain the original documentation:


#### Prd Canary Deployment Guide

# PRD: Canary Deployment Guide


#### 1 Executive Summary

## 1. Executive Summary


#### 1 1 Overview

### 1.1 Overview
This document provides a comprehensive guide for implementing and managing canary deployments using Argo Rollouts on Kubernetes. Canary deployment is a progressive delivery strategy that gradually shifts traffic from an old version to a new version while monitoring metrics for issues.


#### 1 2 Business Objectives

### 1.2 Business Objectives
- Reduce deployment risk through gradual rollout
- Enable automated rollback based on metrics
- Minimize blast radius of faulty deployments
- Increase deployment confidence with data-driven decisions
- Achieve safe production releases


#### 1 3 Success Criteria

### 1.3 Success Criteria
- [ ] Progressive traffic shifting implemented (10% → 25% → 50% → 75% → 100%)
- [ ] Automated analysis running at each step
- [ ] Automatic rollback on metric failures
- [ ] Zero-downtime during rollout
- [ ] Rollback time < 2 minutes


#### 2 Canary Deployment Strategy

## 2. Canary Deployment Strategy


#### 2 1 Architecture

### 2.1 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Ingress Controller                           │
│                  (canary.local)                               │
│                                                               │
│         Traffic Split: 75% Stable / 25% Canary               │
└───────────────────────┬──────────────────────────────────────┘
                        │
           ┌────────────┴─────────────┐
           │                          │
    ┌──────▼──────┐           ┌──────▼──────┐
    │   Stable    │           │   Canary    │
    │   Service   │           │   Service   │
    └──────┬──────┘           └──────┬──────┘
           │                          │
    ┌──────▼──────────────┐   ┌──────▼──────────────┐
    │ Stable ReplicaSet   │   │ Canary ReplicaSet   │
    │   v1.0 (Old)        │   │   v2.0 (New)        │
    │   - Pod 1           │   │   - Pod 1           │
    │   - Pod 2           │   │   - Pod 2           │
    │   - Pod 3           │   │                     │
    │   - Pod 4           │   │                     │
    └─────────────────────┘   └─────────────────────┘
```


#### 2 2 Traffic Progression

### 2.2 Traffic Progression

```
Step 1: 10% Canary → Analyze → Wait
Step 2: 25% Canary → Analyze → Wait
Step 3: 50% Canary → Analyze → Wait
Step 4: 75% Canary → Analyze → Wait
Step 5: 100% Canary → Complete
```


#### 2 3 Key Concepts

### 2.3 Key Concepts

**Stable Version**: Current production version serving majority of traffic

**Canary Version**: New version receiving percentage of traffic for testing

**Weight**: Percentage of traffic routed to canary version

**Analysis**: Automated metric evaluation at each step

**Auto-promotion**: Automatic progression when analysis passes

**Auto-rollback**: Automatic revert when analysis fails


#### 3 Implementation Guide

## 3. Implementation Guide


#### 3 1 Rollout Configuration

### 3.1 Rollout Configuration

The canary rollout is defined in `k8s/canary/rollout.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-app
  namespace: canary-canary
spec:
  replicas: 5
  strategy:
    canary:
      maxSurge: "25%"
      maxUnavailable: 0
      stableService: canary-stable
      canaryService: canary-canary-svc
      trafficRouting:
        nginx:
          stableIngress: canary-ingress
      steps:
      - setWeight: 10
      - pause: {duration: 2m}
      - analysis:
          templates:
          - templateName: success-rate
      - setWeight: 25
      - pause: {duration: 2m}
      # ... more steps
```

**Key Parameters:**
- `maxSurge`: Maximum additional pods during rollout
- `maxUnavailable`: Minimum available pods
- `stableService`: Service for stable version
- `canaryService`: Service for canary version
- `trafficRouting`: How traffic is split
- `steps`: Progression stages with weights and analysis


#### 3 2 Analysis Template

### 3.2 Analysis Template

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
  - name: success-rate
    successCondition: result[0] >= 0.95
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc:9090
        query: |
          sum(rate(http_requests_total{status!~"5.."}[5m])) /
          sum(rate(http_requests_total[5m]))
  - name: error-rate
    successCondition: result[0] <= 0.05
    provider:
      prometheus:
        query: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) /
          sum(rate(http_requests_total[5m]))
```


#### 3 3 Traffic Routing

### 3.3 Traffic Routing

**Ingress-based**:
- Uses ingress controller annotations
- `canary-weight` annotation set by Argo Rollouts
- Supports nginx, ALB, Istio

**Service Mesh**:
- Uses Istio VirtualServices
- More fine-grained control
- Additional traffic management features


#### 4 Deployment Workflow

## 4. Deployment Workflow


#### 4 1 Automated Canary Rollout

### 4.1 Automated Canary Rollout

1. **Initial State**: 100% traffic to stable version
2. **New Version Deployed**: Canary pods start
3. **Step 1 (10%)**:
   - Traffic shifts to 10% canary
   - Pause for 2 minutes
   - Run analysis
   - If pass → continue, if fail → rollback
4. **Step 2 (25%)**: Increase to 25%, analyze
5. **Step 3 (50%)**: Increase to 50%, analyze
6. **Step 4 (75%)**: Increase to 75%, analyze
7. **Step 5 (100%)**: Full promotion complete
8. **Cleanup**: Scale down stable version


#### 4 2 Manual Intervention

### 4.2 Manual Intervention

At any point:

```bash

#### Pause The Rollout

# Pause the rollout
kubectl argo rollouts pause canary-app -n canary-canary


#### Promote To Next Step

# Promote to next step
kubectl argo rollouts promote canary-app -n canary-canary


#### Abort And Rollback

# Abort and rollback
kubectl argo rollouts abort canary-app -n canary-canary


#### 4 3 Monitoring During Rollout

### 4.3 Monitoring During Rollout

```bash

#### Watch Rollout Progress

# Watch rollout progress
kubectl argo rollouts get rollout canary-app -n canary-canary --watch


#### View Analysis Runs

# View analysis runs
kubectl get analysisrun -n canary-canary


#### Check Current Traffic Weight

# Check current traffic weight
kubectl get ingress canary-ingress -n canary-canary -o jsonpath='{.metadata.annotations}'
```


#### 5 Analysis Configuration

## 5. Analysis Configuration


#### 5 1 Prometheus Metrics

### 5.1 Prometheus Metrics

**Success Rate**:
```promql
sum(rate(http_requests_total{service="canary",status!~"5.."}[5m])) /
sum(rate(http_requests_total{service="canary"}[5m]))
```
- Threshold: >= 0.95 (95% success rate)

**Error Rate**:
```promql
sum(rate(http_requests_total{service="canary",status=~"5.."}[5m])) /
sum(rate(http_requests_total{service="canary"}[5m]))
```
- Threshold: <= 0.05 (5% error rate)

**Latency (P95)**:
```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{service="canary"}[5m])) by (le)
)
```
- Threshold: <= 0.5 seconds


#### 5 2 Custom Metrics

### 5.2 Custom Metrics

Add custom metrics from your application:

```yaml
metrics:
- name: custom-metric
  successCondition: result[0] >= threshold
  provider:
    prometheus:
      query: your_custom_metric{service="canary"}
```


#### 5 3 Multiple Analysis Templates

### 5.3 Multiple Analysis Templates

```yaml
steps:
- setWeight: 10
- pause: {duration: 2m}
- analysis:
    templates:
    - templateName: success-rate
    - templateName: latency-check
    - templateName: custom-business-metrics
    args:
    - name: service-name
      value: canary-canary-svc
```


#### 6 Operational Commands

## 6. Operational Commands


#### 6 1 View Rollout Status

### 6.1 View Rollout Status

```bash

#### Current Rollout Status

# Current rollout status
kubectl argo rollouts get rollout canary-app -n canary-canary


#### Watch In Real Time With Visualization

# Watch in real-time with visualization
kubectl argo rollouts get rollout canary-app -n canary-canary --watch


#### Check Specific Revision

# Check specific revision
kubectl argo rollouts history canary-app -n canary-canary
```


#### 6 2 Control Rollout

### 6.2 Control Rollout

```bash

#### Promote To Next Step Manual Progression 

# Promote to next step (manual progression)
kubectl argo rollouts promote canary-app -n canary-canary


#### Skip Current Pause Analysis

# Skip current pause/analysis
kubectl argo rollouts promote --skip-current-step canary-app -n canary-canary


#### Pause Rollout

# Pause rollout
kubectl argo rollouts pause canary-app -n canary-canary


#### Resume Rollout

# Resume rollout
kubectl argo rollouts resume canary-app -n canary-canary


#### Rollback To Previous Stable

# Rollback to previous stable
kubectl argo rollouts undo canary-app -n canary-canary
```


#### 6 3 Analysis Management

### 6.3 Analysis Management

```bash

#### List Analysis Runs

# List analysis runs
kubectl get analysisrun -n canary-canary


#### Describe Analysis Run

# Describe analysis run
kubectl describe analysisrun <name> -n canary-canary


#### View Analysis Run Status

# View analysis run status
kubectl get analysisrun <name> -n canary-canary -o jsonpath='{.status.phase}'


#### Delete Failed Analysis Runs

# Delete failed analysis runs
kubectl delete analysisrun -l rollout=canary-app -n canary-canary
```


#### 7 Implementation Phases

## 7. Implementation Phases


#### Phase 1 Preparation Priority Critical 

### Phase 1: Preparation (Priority: Critical)
- [ ] Review application metrics available
- [ ] Identify key metrics for analysis (error rate, latency, etc.)
- [ ] Determine appropriate traffic split percentages
- [ ] Calculate pause durations for analysis
- [ ] Assess Prometheus metric collection
- [ ] Plan canary rollout steps


#### Phase 2 Manifest Creation Priority Critical 

### Phase 2: Manifest Creation (Priority: Critical)
- [ ] Create rollout manifest with canary strategy
- [ ] Define stable and canary services
- [ ] Configure traffic routing (nginx/istio)
- [ ] Create AnalysisTemplate with Prometheus queries
- [ ] Set up success criteria for each metric
- [ ] Configure rollout steps with weights and pauses
- [ ] Set maxSurge and maxUnavailable parameters
- [ ] Configure ingress for traffic management


#### Phase 3 Prometheus Setup Priority Critical 

### Phase 3: Prometheus Setup (Priority: Critical)
- [ ] Verify Prometheus is installed and running
- [ ] Configure application to export metrics
- [ ] Set up ServiceMonitor for metric scraping
- [ ] Test Prometheus queries return data
- [ ] Verify metric labels match AnalysisTemplate
- [ ] Set up Grafana dashboards for visualization
- [ ] Configure alerting rules


#### Phase 4 Initial Deployment Priority High 

### Phase 4: Initial Deployment (Priority: High)
- [ ] Create namespace if not exists
- [ ] Deploy AnalysisTemplate
- [ ] Deploy rollout manifest
- [ ] Deploy services (stable and canary)
- [ ] Deploy ingress configuration
- [ ] Wait for initial pods to be ready
- [ ] Verify stable service has endpoints
- [ ] Test application via ingress
- [ ] Verify metrics are being collected


#### Phase 5 First Canary Rollout Priority Critical 

### Phase 5: First Canary Rollout (Priority: Critical)
- [ ] Update container image to new version
- [ ] Commit and push to Git repository
- [ ] Wait for ArgoCD to sync
- [ ] Monitor rollout status
- [ ] Verify canary pods created
- [ ] Check traffic split at 10%
- [ ] Wait for analysis to run
- [ ] Review analysis results
- [ ] Verify automatic progression to 25%


#### Phase 6 Analysis Validation Priority Critical 

### Phase 6: Analysis Validation (Priority: Critical)
- [ ] Access canary endpoint to generate traffic
- [ ] Run load tests against application
- [ ] Monitor Prometheus metrics in real-time
- [ ] Verify AnalysisRun is created
- [ ] Check analysis success/failure status
- [ ] Review metric thresholds
- [ ] Validate automatic progression works
- [ ] Test automatic rollback on failure
- [ ] Verify rollback completes successfully


#### Phase 7 Progressive Rollout Monitoring Priority High 

### Phase 7: Progressive Rollout Monitoring (Priority: High)
- [ ] Monitor traffic at each weight (10%, 25%, 50%, 75%)
- [ ] Watch for error rate increases
- [ ] Track latency metrics
- [ ] Monitor resource utilization
- [ ] Check application logs for errors
- [ ] Verify database performance
- [ ] Monitor external API calls
- [ ] Check cache hit rates
- [ ] Review custom business metrics


#### Phase 8 Full Promotion Priority High 

### Phase 8: Full Promotion (Priority: High)
- [ ] Wait for 100% traffic to canary
- [ ] Verify all traffic switched
- [ ] Run production smoke tests
- [ ] Execute full integration test suite
- [ ] Monitor production metrics
- [ ] Check error rates remain low
- [ ] Verify latency is acceptable
- [ ] Confirm stable version scaled down
- [ ] Clean up old ReplicaSets


#### Phase 9 Rollback Testing Priority Critical 

### Phase 9: Rollback Testing (Priority: Critical)
- [ ] Trigger analysis failure intentionally
- [ ] Verify automatic rollback occurs
- [ ] Check traffic reverts to stable version
- [ ] Measure rollback duration
- [ ] Verify application remains available
- [ ] Test manual abort command
- [ ] Practice emergency rollback procedure
- [ ] Document rollback steps in runbook


#### Phase 10 Optimization Priority Medium 

### Phase 10: Optimization (Priority: Medium)
- [ ] Fine-tune traffic split percentages
- [ ] Adjust pause durations
- [ ] Optimize analysis query intervals
- [ ] Add additional metrics to analysis
- [ ] Configure multiple analysis templates
- [ ] Implement baseline vs canary comparison
- [ ] Set up automated notifications
- [ ] Create custom dashboards


#### Phase 11 Advanced Configuration Priority Low 

### Phase 11: Advanced Configuration (Priority: Low)
- [ ] Implement experiment-based canary (A/B testing)
- [ ] Configure header-based routing
- [ ] Set up canary with Istio service mesh
- [ ] Implement traffic mirroring/shadowing
- [ ] Configure ALB for AWS environments
- [ ] Set up multi-stage canary (dev→staging→prod)
- [ ] Implement automated approval gates
- [ ] Create deployment templates


#### 8 Best Practices

## 8. Best Practices


#### 8 1 Traffic Progression

### 8.1 Traffic Progression
- Start with small percentages (5-10%)
- Increase gradually (10% → 25% → 50% → 75%)
- Spend more time at critical thresholds
- Allow enough time for metrics to stabilize


#### 8 2 Analysis Configuration

### 8.2 Analysis Configuration
- Use multiple metrics (error rate, latency, custom)
- Set realistic thresholds based on baselines
- Use appropriate time windows (5m, 10m)
- Include both technical and business metrics


#### 8 3 Pause Durations

### 8.3 Pause Durations
- Short pauses for low-risk changes (1-2 minutes)
- Longer pauses for high-risk changes (5-10 minutes)
- Allow time for metric collection and analysis
- Consider peak vs off-peak traffic patterns


#### 8 4 Rollback Triggers

### 8.4 Rollback Triggers
- Automatic: Failed analysis, health checks
- Manual: Stakeholder decision, user reports
- Set clear rollback criteria
- Practice rollback procedures regularly


#### 8 5 Resource Management

### 8.5 Resource Management
- Set appropriate `maxSurge` to control resource usage
- Use `maxUnavailable: 0` for zero-downtime
- Monitor cluster capacity during rollout
- Consider pod disruption budgets


#### 9 Troubleshooting

## 9. Troubleshooting


#### 9 1 Analysis Always Fails

### 9.1 Analysis Always Fails
**Problem**: AnalysisRun fails immediately

**Solutions**:
- Verify Prometheus is accessible from cluster
- Check PromQL queries return data
- Verify service labels match queries
- Check metric names and labels
- Test queries in Prometheus UI
- Verify time windows are appropriate


#### 9 2 Traffic Not Shifting

### 9.2 Traffic Not Shifting
**Problem**: Weight doesn't change in ingress

**Solutions**:
- Check ingress controller supports canary annotations
- Verify ingress name matches rollout config
- Check ingress controller logs
- Verify canary service has endpoints
- Test ingress annotations manually


#### 9 3 Rollout Stuck At Step

### 9.3 Rollout Stuck at Step
**Problem**: Rollout doesn't progress

**Solutions**:
- Check if analysis is running: `kubectl get analysisrun`
- Review analysis results for failures
- Check pause duration hasn't expired
- Verify no manual pause was issued
- Check rollout controller logs


#### 9 4 Automatic Rollback Not Working

### 9.4 Automatic Rollback Not Working
**Problem**: Analysis fails but doesn't rollback

**Solutions**:
- Verify analysis template has failure conditions
- Check `successCondition` is correct (result[0] >= threshold)
- Review analysisrun status and message
- Check rollout strategy includes analysis
- Verify analysis interval and count settings


#### 9 5 Metrics Not Available

### 9.5 Metrics Not Available
**Problem**: Prometheus queries return no data

**Solutions**:
- Verify application exports metrics
- Check ServiceMonitor configuration
- Verify Prometheus is scraping application
- Check metric names and labels
- Test metrics endpoint: `curl http://pod-ip:port/metrics`


#### 10 Advanced Topics

## 10. Advanced Topics


#### 10 1 Experiment Based Canary

### 10.1 Experiment-Based Canary

```yaml
strategy:
  canary:
    canaryMetadata:
      labels:
        version: canary
    stableMetadata:
      labels:
        version: stable
    trafficRouting:
      nginx:
        stableIngress: app-ingress
        additionalIngressAnnotations:
          canary-by-header: X-Canary
          canary-by-header-value: "always"
```


#### 10 2 Traffic Mirroring

### 10.2 Traffic Mirroring

```yaml
trafficRouting:
  istio:
    virtualService:
      name: app-vsvc
    destinationRule:
      name: app-destrule
    mirror:
      enabled: true
      percentage: 100
```


#### 10 3 Baseline Vs Canary Analysis

### 10.3 Baseline vs Canary Analysis

```yaml
spec:
  args:
  - name: baseline-hash
  - name: canary-hash
  metrics:
  - name: success-rate-comparison
    successCondition: result[0] - result[1] < 0.05
    provider:
      prometheus:
        query: |
          sum(rate(http_requests_total{rollouts_pod_template_hash="{{args.canary-hash}}"}[5m]))
```


#### 11 Metrics And Monitoring

## 11. Metrics and Monitoring


#### 11 1 Key Metrics

### 11.1 Key Metrics

- **Rollout Duration**: Total time for canary to complete
- **Analysis Pass Rate**: % of analysis runs that pass
- **Rollback Frequency**: Number of automatic rollbacks
- **Time to Detect Issues**: Time from deployment to rollback
- **Traffic Distribution**: Actual vs expected traffic split
- **Resource Utilization**: CPU/Memory during rollout


#### 11 2 Dashboards

### 11.2 Dashboards

Create Grafana dashboard with:
- Rollout status timeline
- Traffic weight over time
- Error rate comparison (stable vs canary)
- Latency comparison
- Analysis run results
- Resource utilization


#### 12 References

## 12. References

- [Argo Rollouts Canary Documentation](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [Traffic Management](https://argoproj.github.io/argo-rollouts/features/traffic-management/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)


#### 13 Appendix

## 13. Appendix


#### A Complete Rollout Example

### A. Complete Rollout Example

See `k8s/canary/rollout.yaml`


#### B Analysis Template Examples

### B. Analysis Template Examples

See `k8s/canary/rollout.yaml` (AnalysisTemplate section)


#### C Canary Deployment Checklist

### C. Canary Deployment Checklist

```
[ ] Update image tag
[ ] Commit and push to Git
[ ] Wait for ArgoCD sync
[ ] Monitor rollout status
[ ] Verify 10% traffic split
[ ] Check analysis results
[ ] Monitor error rates
[ ] Verify progression to 25%
[ ] Continue monitoring at each step
[ ] Verify 100% promotion
[ ] Run production tests
[ ] Monitor post-deployment
[ ] Clean up old versions
[ ] Document deployment
```


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
