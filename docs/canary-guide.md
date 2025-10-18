# PRD: Canary Deployment Guide

## 1. Executive Summary

### 1.1 Overview
This document provides a comprehensive guide for implementing and managing canary deployments using Argo Rollouts on Kubernetes. Canary deployment is a progressive delivery strategy that gradually shifts traffic from an old version to a new version while monitoring metrics for issues.

### 1.2 Business Objectives
- Reduce deployment risk through gradual rollout
- Enable automated rollback based on metrics
- Minimize blast radius of faulty deployments
- Increase deployment confidence with data-driven decisions
- Achieve safe production releases

### 1.3 Success Criteria
- [ ] Progressive traffic shifting implemented (10% → 25% → 50% → 75% → 100%)
- [ ] Automated analysis running at each step
- [ ] Automatic rollback on metric failures
- [ ] Zero-downtime during rollout
- [ ] Rollback time < 2 minutes

## 2. Canary Deployment Strategy

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

### 2.2 Traffic Progression

```
Step 1: 10% Canary → Analyze → Wait
Step 2: 25% Canary → Analyze → Wait
Step 3: 50% Canary → Analyze → Wait
Step 4: 75% Canary → Analyze → Wait
Step 5: 100% Canary → Complete
```

### 2.3 Key Concepts

**Stable Version**: Current production version serving majority of traffic

**Canary Version**: New version receiving percentage of traffic for testing

**Weight**: Percentage of traffic routed to canary version

**Analysis**: Automated metric evaluation at each step

**Auto-promotion**: Automatic progression when analysis passes

**Auto-rollback**: Automatic revert when analysis fails

## 3. Implementation Guide

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

### 3.3 Traffic Routing

**Ingress-based**:
- Uses ingress controller annotations
- `canary-weight` annotation set by Argo Rollouts
- Supports nginx, ALB, Istio

**Service Mesh**:
- Uses Istio VirtualServices
- More fine-grained control
- Additional traffic management features

## 4. Deployment Workflow

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

### 4.2 Manual Intervention

At any point:

```bash
# Pause the rollout
kubectl argo rollouts pause canary-app -n canary-canary

# Promote to next step
kubectl argo rollouts promote canary-app -n canary-canary

# Abort and rollback
kubectl argo rollouts abort canary-app -n canary-canary
```

### 4.3 Monitoring During Rollout

```bash
# Watch rollout progress
kubectl argo rollouts get rollout canary-app -n canary-canary --watch

# View analysis runs
kubectl get analysisrun -n canary-canary

# Check current traffic weight
kubectl get ingress canary-ingress -n canary-canary -o jsonpath='{.metadata.annotations}'
```

## 5. Analysis Configuration

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

## 6. Operational Commands

### 6.1 View Rollout Status

```bash
# Current rollout status
kubectl argo rollouts get rollout canary-app -n canary-canary

# Watch in real-time with visualization
kubectl argo rollouts get rollout canary-app -n canary-canary --watch

# Check specific revision
kubectl argo rollouts history canary-app -n canary-canary
```

### 6.2 Control Rollout

```bash
# Promote to next step (manual progression)
kubectl argo rollouts promote canary-app -n canary-canary

# Skip current pause/analysis
kubectl argo rollouts promote --skip-current-step canary-app -n canary-canary

# Pause rollout
kubectl argo rollouts pause canary-app -n canary-canary

# Resume rollout
kubectl argo rollouts resume canary-app -n canary-canary

# Abort and rollback
kubectl argo rollouts abort canary-app -n canary-canary

# Rollback to previous stable
kubectl argo rollouts undo canary-app -n canary-canary
```

### 6.3 Analysis Management

```bash
# List analysis runs
kubectl get analysisrun -n canary-canary

# Describe analysis run
kubectl describe analysisrun <name> -n canary-canary

# View analysis run status
kubectl get analysisrun <name> -n canary-canary -o jsonpath='{.status.phase}'

# Delete failed analysis runs
kubectl delete analysisrun -l rollout=canary-app -n canary-canary
```

## 7. Implementation Phases

### Phase 1: Preparation (Priority: Critical)
- [ ] Review application metrics available
- [ ] Identify key metrics for analysis (error rate, latency, etc.)
- [ ] Determine appropriate traffic split percentages
- [ ] Calculate pause durations for analysis
- [ ] Assess Prometheus metric collection
- [ ] Plan canary rollout steps

### Phase 2: Manifest Creation (Priority: Critical)
- [ ] Create rollout manifest with canary strategy
- [ ] Define stable and canary services
- [ ] Configure traffic routing (nginx/istio)
- [ ] Create AnalysisTemplate with Prometheus queries
- [ ] Set up success criteria for each metric
- [ ] Configure rollout steps with weights and pauses
- [ ] Set maxSurge and maxUnavailable parameters
- [ ] Configure ingress for traffic management

### Phase 3: Prometheus Setup (Priority: Critical)
- [ ] Verify Prometheus is installed and running
- [ ] Configure application to export metrics
- [ ] Set up ServiceMonitor for metric scraping
- [ ] Test Prometheus queries return data
- [ ] Verify metric labels match AnalysisTemplate
- [ ] Set up Grafana dashboards for visualization
- [ ] Configure alerting rules

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

### Phase 9: Rollback Testing (Priority: Critical)
- [ ] Trigger analysis failure intentionally
- [ ] Verify automatic rollback occurs
- [ ] Check traffic reverts to stable version
- [ ] Measure rollback duration
- [ ] Verify application remains available
- [ ] Test manual abort command
- [ ] Practice emergency rollback procedure
- [ ] Document rollback steps in runbook

### Phase 10: Optimization (Priority: Medium)
- [ ] Fine-tune traffic split percentages
- [ ] Adjust pause durations
- [ ] Optimize analysis query intervals
- [ ] Add additional metrics to analysis
- [ ] Configure multiple analysis templates
- [ ] Implement baseline vs canary comparison
- [ ] Set up automated notifications
- [ ] Create custom dashboards

### Phase 11: Advanced Configuration (Priority: Low)
- [ ] Implement experiment-based canary (A/B testing)
- [ ] Configure header-based routing
- [ ] Set up canary with Istio service mesh
- [ ] Implement traffic mirroring/shadowing
- [ ] Configure ALB for AWS environments
- [ ] Set up multi-stage canary (dev→staging→prod)
- [ ] Implement automated approval gates
- [ ] Create deployment templates

## 8. Best Practices

### 8.1 Traffic Progression
- Start with small percentages (5-10%)
- Increase gradually (10% → 25% → 50% → 75%)
- Spend more time at critical thresholds
- Allow enough time for metrics to stabilize

### 8.2 Analysis Configuration
- Use multiple metrics (error rate, latency, custom)
- Set realistic thresholds based on baselines
- Use appropriate time windows (5m, 10m)
- Include both technical and business metrics

### 8.3 Pause Durations
- Short pauses for low-risk changes (1-2 minutes)
- Longer pauses for high-risk changes (5-10 minutes)
- Allow time for metric collection and analysis
- Consider peak vs off-peak traffic patterns

### 8.4 Rollback Triggers
- Automatic: Failed analysis, health checks
- Manual: Stakeholder decision, user reports
- Set clear rollback criteria
- Practice rollback procedures regularly

### 8.5 Resource Management
- Set appropriate `maxSurge` to control resource usage
- Use `maxUnavailable: 0` for zero-downtime
- Monitor cluster capacity during rollout
- Consider pod disruption budgets

## 9. Troubleshooting

### 9.1 Analysis Always Fails
**Problem**: AnalysisRun fails immediately

**Solutions**:
- Verify Prometheus is accessible from cluster
- Check PromQL queries return data
- Verify service labels match queries
- Check metric names and labels
- Test queries in Prometheus UI
- Verify time windows are appropriate

### 9.2 Traffic Not Shifting
**Problem**: Weight doesn't change in ingress

**Solutions**:
- Check ingress controller supports canary annotations
- Verify ingress name matches rollout config
- Check ingress controller logs
- Verify canary service has endpoints
- Test ingress annotations manually

### 9.3 Rollout Stuck at Step
**Problem**: Rollout doesn't progress

**Solutions**:
- Check if analysis is running: `kubectl get analysisrun`
- Review analysis results for failures
- Check pause duration hasn't expired
- Verify no manual pause was issued
- Check rollout controller logs

### 9.4 Automatic Rollback Not Working
**Problem**: Analysis fails but doesn't rollback

**Solutions**:
- Verify analysis template has failure conditions
- Check `successCondition` is correct (result[0] >= threshold)
- Review analysisrun status and message
- Check rollout strategy includes analysis
- Verify analysis interval and count settings

### 9.5 Metrics Not Available
**Problem**: Prometheus queries return no data

**Solutions**:
- Verify application exports metrics
- Check ServiceMonitor configuration
- Verify Prometheus is scraping application
- Check metric names and labels
- Test metrics endpoint: `curl http://pod-ip:port/metrics`

## 10. Advanced Topics

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

## 11. Metrics and Monitoring

### 11.1 Key Metrics

- **Rollout Duration**: Total time for canary to complete
- **Analysis Pass Rate**: % of analysis runs that pass
- **Rollback Frequency**: Number of automatic rollbacks
- **Time to Detect Issues**: Time from deployment to rollback
- **Traffic Distribution**: Actual vs expected traffic split
- **Resource Utilization**: CPU/Memory during rollout

### 11.2 Dashboards

Create Grafana dashboard with:
- Rollout status timeline
- Traffic weight over time
- Error rate comparison (stable vs canary)
- Latency comparison
- Analysis run results
- Resource utilization

## 12. References

- [Argo Rollouts Canary Documentation](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [Traffic Management](https://argoproj.github.io/argo-rollouts/features/traffic-management/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)

## 13. Appendix

### A. Complete Rollout Example

See `k8s/canary/rollout.yaml`

### B. Analysis Template Examples

See `k8s/canary/rollout.yaml` (AnalysisTemplate section)

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
