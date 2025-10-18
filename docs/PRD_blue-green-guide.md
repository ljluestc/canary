# Product Requirements Document: DOCS: Blue Green Guide

---

## Document Information
**Project:** docs
**Document:** blue-green-guide
**Version:** 1.0.0
**Date:** 2025-10-13
**Status:** READY FOR TASK-MASTER PARSING

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview
This PRD captures the requirements and implementation details for DOCS: Blue Green Guide.

### 1.2 Purpose
This document provides a structured specification that can be parsed by task-master to generate actionable tasks.

### 1.3 Scope
The scope includes all requirements, features, and implementation details from the original documentation.

---

## 2. REQUIREMENTS

### 2.1 Functional Requirements
**Priority:** HIGH

**REQ-001:** (2x capacity during rollout)


## 3. TASKS

The following tasks have been identified for implementation:

**TASK_001** [MEDIUM]: Achieve zero-downtime deployments

**TASK_002** [MEDIUM]: Enable instant rollback capability

**TASK_003** [MEDIUM]: Provide preview environment for testing before production

**TASK_004** [MEDIUM]: Reduce deployment risk

**TASK_005** [MEDIUM]: Improve deployment confidence

**TASK_006** [MEDIUM]: Zero-downtime deployment achieved

**TASK_007** [MEDIUM]: Rollback time < 30 seconds

**TASK_008** [MEDIUM]: Preview environment accessible before promotion

**TASK_009** [MEDIUM]: All health checks passing before traffic switch

**TASK_010** [MEDIUM]: Deployment automation working end-to-end

**TASK_011** [MEDIUM]: `activeService`: Service for production traffic

**TASK_012** [MEDIUM]: `previewService`: Service for preview traffic

**TASK_013** [MEDIUM]: `autoPromotionEnabled`: false = manual promotion required

**TASK_014** [MEDIUM]: `scaleDownDelaySeconds`: Delay before scaling down old version

**TASK_015** [MEDIUM]: `previewReplicaCount`: Number of preview replicas

**TASK_016** [MEDIUM]: Routes to pods with current rollout hash

**TASK_017** [MEDIUM]: Receives production traffic

**TASK_018** [MEDIUM]: Updated during promotion

**TASK_019** [MEDIUM]: Routes to pods with new rollout hash

**TASK_020** [MEDIUM]: Receives preview traffic

**TASK_021** [MEDIUM]: Always points to new version

**TASK_022** [MEDIUM]: host: blue-green.local

**TASK_023** [MEDIUM]: host: blue-green-preview.local

**TASK_024** [HIGH]: Deploy rollout manifest

**TASK_025** [HIGH]: Argo Rollouts creates initial ReplicaSet

**TASK_026** [HIGH]: Pods start and pass health checks

**TASK_027** [HIGH]: Active service points to new pods

**TASK_028** [HIGH]: Application is accessible via production URL

**TASK_029** [HIGH]: Update container image in rollout spec

**TASK_030** [HIGH]: Commit and push changes to Git

**TASK_031** [HIGH]: ArgoCD detects change and syncs

**TASK_032** [HIGH]: Argo Rollouts creates new ReplicaSet (green)

**TASK_033** [HIGH]: New pods start in preview environment

**TASK_034** [HIGH]: Preview service points to new pods

**TASK_035** [HIGH]: Rollout pauses waiting for promotion

**TASK_036** [HIGH]: Active service selector updated to new hash

**TASK_037** [HIGH]: Production traffic switches to green (new) pods

**TASK_038** [HIGH]: Blue (old) pods remain running for `scaleDownDelaySeconds`

**TASK_039** [HIGH]: After delay, old pods are scaled down

**TASK_040** [HIGH]: Deployment complete

**TASK_041** [HIGH]: Active service selector reverted to previous hash

**TASK_042** [HIGH]: Traffic switches back to blue (old) pods instantly

**TASK_043** [HIGH]: Takes < 30 seconds

**TASK_044** [HIGH]: No pods need to restart

**TASK_045** [MEDIUM]: Review current deployment strategy

**TASK_046** [MEDIUM]: Identify applications for blue-green deployment

**TASK_047** [MEDIUM]: Assess resource requirements (2x capacity during rollout)

**TASK_048** [MEDIUM]: Plan rollback procedures

**TASK_049** [MEDIUM]: Create deployment checklist

**TASK_050** [MEDIUM]: Create rollout manifest with blue-green strategy

**TASK_051** [MEDIUM]: Define active and preview services

**TASK_052** [MEDIUM]: Configure ingress for both environments

**TASK_053** [MEDIUM]: Set appropriate replica counts

**TASK_054** [MEDIUM]: Configure health checks

**TASK_055** [MEDIUM]: Set resource limits and requests

**TASK_056** [MEDIUM]: Apply namespace if not exists

**TASK_057** [MEDIUM]: Deploy rollout manifest

**TASK_058** [MEDIUM]: Wait for pods to be ready

**TASK_059** [MEDIUM]: Verify active service endpoints

**TASK_060** [MEDIUM]: Test production URL access

**TASK_061** [MEDIUM]: Verify health check endpoints

**TASK_062** [MEDIUM]: Check application functionality

**TASK_063** [MEDIUM]: Update container image to new version

**TASK_064** [MEDIUM]: Commit changes to Git

**TASK_065** [MEDIUM]: Wait for ArgoCD to sync

**TASK_066** [MEDIUM]: Verify new ReplicaSet created

**TASK_067** [MEDIUM]: Check preview pods are running

**TASK_068** [MEDIUM]: Verify preview service endpoints

**TASK_069** [MEDIUM]: Test preview URL access

**TASK_070** [MEDIUM]: Access preview environment

**TASK_071** [MEDIUM]: Run smoke tests on preview

**TASK_072** [MEDIUM]: Execute integration test suite

**TASK_073** [MEDIUM]: Perform manual QA testing

**TASK_074** [MEDIUM]: Check application logs for errors

**TASK_075** [MEDIUM]: Monitor preview metrics

**TASK_076** [MEDIUM]: Validate database migrations if any

**TASK_077** [MEDIUM]: Test critical user journeys

**TASK_078** [MEDIUM]: Review performance metrics

**TASK_079** [MEDIUM]: Get stakeholder approval

**TASK_080** [MEDIUM]: Execute promotion command

**TASK_081** [MEDIUM]: Monitor active service update

**TASK_082** [MEDIUM]: Verify traffic switch to new pods

**TASK_083** [MEDIUM]: Check production URL serves new version

**TASK_084** [MEDIUM]: Monitor error rates in production

**TASK_085** [MEDIUM]: Watch application logs

**TASK_086** [MEDIUM]: Verify all health checks passing

**TASK_087** [MEDIUM]: Monitor database connections

**TASK_088** [MEDIUM]: Check external integrations working

**TASK_089** [MEDIUM]: Run production smoke tests

**TASK_090** [MEDIUM]: Execute synthetic monitoring tests

**TASK_091** [MEDIUM]: Verify all endpoints responding

**TASK_092** [MEDIUM]: Check application metrics

**TASK_093** [MEDIUM]: Monitor error logs

**TASK_094** [MEDIUM]: Validate user reports

**TASK_095** [MEDIUM]: Review performance dashboards

**TASK_096** [MEDIUM]: Confirm database query performance

**TASK_097** [MEDIUM]: Check cache hit rates

**TASK_098** [MEDIUM]: Verify CDN invalidation if needed

**TASK_099** [MEDIUM]: Wait for scale-down delay to complete

**TASK_100** [MEDIUM]: Verify old pods scaled down

**TASK_101** [MEDIUM]: Check only new ReplicaSet is running

**TASK_102** [MEDIUM]: Clean up old container images

**TASK_103** [MEDIUM]: Update documentation

**TASK_104** [MEDIUM]: Archive rollout logs

**TASK_105** [MEDIUM]: Document rollback procedure

**TASK_106** [MEDIUM]: Test rollback in non-prod environment

**TASK_107** [MEDIUM]: Time rollback duration

**TASK_108** [MEDIUM]: Verify rollback completes successfully

**TASK_109** [MEDIUM]: Practice rollback with team

**TASK_110** [MEDIUM]: Create rollback runbook

**TASK_111** [MEDIUM]: Create deployment scripts

**TASK_112** [MEDIUM]: Automate preview testing

**TASK_113** [MEDIUM]: Set up automated health checks

**TASK_114** [MEDIUM]: Configure monitoring alerts

**TASK_115** [MEDIUM]: Create promotion approval workflow

**TASK_116** [MEDIUM]: Set up deployment notifications

**TASK_117** [MEDIUM]: Integrate with CI/CD pipeline

**TASK_118** [MEDIUM]: Always configure liveness and readiness probes

**TASK_119** [MEDIUM]: Set appropriate `initialDelaySeconds` for app startup

**TASK_120** [MEDIUM]: Use HTTP endpoints that verify critical dependencies

**TASK_121** [MEDIUM]: Keep probe timeouts reasonable

**TASK_122** [MEDIUM]: Ensure cluster has capacity for 2x pods during rollout

**TASK_123** [MEDIUM]: Set resource requests and limits

**TASK_124** [MEDIUM]: Use horizontal pod autoscaling if needed

**TASK_125** [MEDIUM]: Monitor resource utilization

**TASK_126** [MEDIUM]: Test preview thoroughly before promotion

**TASK_127** [MEDIUM]: Run automated test suites

**TASK_128** [MEDIUM]: Perform manual verification of critical features

**TASK_129** [MEDIUM]: Check all external integrations

**TASK_130** [MEDIUM]: Validate data migrations

**TASK_131** [MEDIUM]: Monitor application metrics during rollout

**TASK_132** [MEDIUM]: Watch for error rate increases

**TASK_133** [MEDIUM]: Track response time changes

**TASK_134** [MEDIUM]: Monitor database connection pools

**TASK_135** [MEDIUM]: Set up alerts for anomalies

**TASK_136** [MEDIUM]: Keep previous version running during scale-down delay

**TASK_137** [MEDIUM]: Extend `scaleDownDelaySeconds` if needed

**TASK_138** [MEDIUM]: Practice rollback procedures regularly

**TASK_139** [MEDIUM]: Document rollback triggers

**TASK_140** [MEDIUM]: Have rollback decision tree ready

**TASK_141** [MEDIUM]: Check pod status: `kubectl get pods -n canary-blue-green`

**TASK_142** [MEDIUM]: Check events: `kubectl describe rollout blue-green-app -n canary-blue-green`

**TASK_143** [MEDIUM]: Verify image pull: Check for ImagePullBackOff errors

**TASK_144** [MEDIUM]: Check resource availability: Node capacity issues

**TASK_145** [MEDIUM]: Review health check failures

**TASK_146** [MEDIUM]: Verify preview service exists and has endpoints

**TASK_147** [MEDIUM]: Check ingress configuration

**TASK_148** [MEDIUM]: Verify DNS/hosts file configuration

**TASK_149** [MEDIUM]: Test service directly: `kubectl port-forward`

**TASK_150** [MEDIUM]: Check ingress controller logs

**TASK_151** [MEDIUM]: Verify active service selector updated

**TASK_152** [MEDIUM]: Check service endpoints: `kubectl get endpoints`

**TASK_153** [MEDIUM]: Verify ingress pointing to correct service

**TASK_154** [MEDIUM]: Check for caching issues

**TASK_155** [MEDIUM]: Verify pod labels match service selector

**TASK_156** [MEDIUM]: Check `scaleDownDelaySeconds` hasn't passed

**TASK_157** [MEDIUM]: Verify no errors in rollout controller logs

**TASK_158** [MEDIUM]: Check if pods have PreStop hooks delaying shutdown

**TASK_159** [MEDIUM]: Manually scale down if needed

**TASK_160** [MEDIUM]: **Deployment Frequency**: Deployments per week

**TASK_161** [MEDIUM]: **Rollout Duration**: Time from sync to promotion

**TASK_162** [MEDIUM]: **Preview Test Duration**: Time spent testing preview

**TASK_163** [MEDIUM]: **Promotion Time**: Time for traffic to switch

**TASK_164** [MEDIUM]: **Rollback Count**: Number of rollbacks needed

**TASK_165** [MEDIUM]: **Success Rate**: % of successful promotions

**TASK_166** [MEDIUM]: [Argo Rollouts Blue-Green Documentation](https://argoproj.github.io/argo-rollouts/features/bluegreen/)

**TASK_167** [MEDIUM]: [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)

**TASK_168** [MEDIUM]: [Blue-Green Deployment Pattern](https://martinfowler.com/bliki/BlueGreenDeployment.html)


## 4. DETAILED SPECIFICATIONS

### 4.1 Original Content

The following sections contain the original documentation:


#### Prd Blue Green Deployment Guide

# PRD: Blue-Green Deployment Guide


#### 1 Executive Summary

## 1. Executive Summary


#### 1 1 Overview

### 1.1 Overview
This document provides a comprehensive guide for implementing and managing blue-green deployments using Argo Rollouts on Kubernetes. Blue-green deployment is a release strategy that reduces downtime and risk by running two identical production environments (blue and green).


#### 1 2 Business Objectives

### 1.2 Business Objectives
- Achieve zero-downtime deployments
- Enable instant rollback capability
- Provide preview environment for testing before production
- Reduce deployment risk
- Improve deployment confidence


#### 1 3 Success Criteria

### 1.3 Success Criteria
- [ ] Zero-downtime deployment achieved
- [ ] Rollback time < 30 seconds
- [ ] Preview environment accessible before promotion
- [ ] All health checks passing before traffic switch
- [ ] Deployment automation working end-to-end


#### 2 Blue Green Deployment Strategy

## 2. Blue-Green Deployment Strategy


#### 2 1 Architecture

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingress Controller                        │
│                                                              │
│  blue-green.local          blue-green-preview.local         │
└───────┬──────────────────────────────┬──────────────────────┘
        │                              │
        │                              │
  ┌─────▼─────┐                  ┌────▼────┐
  │  Active   │                  │ Preview │
  │  Service  │                  │ Service │
  └─────┬─────┘                  └────┬────┘
        │                              │
        │                              │
  ┌─────▼─────────────┐        ┌──────▼──────────────┐
  │   Blue (v1.0)     │        │   Green (v2.0)      │
  │   ReplicaSet      │        │   ReplicaSet        │
  │   - Pod 1         │        │   - Pod 1           │
  │   - Pod 2         │        │   - Pod 2           │
  │   - Pod 3         │        │   - Pod 3           │
  └───────────────────┘        └─────────────────────┘
```


#### 2 2 Key Concepts

### 2.2 Key Concepts

**Blue Environment**: Currently running production version serving live traffic

**Green Environment**: New version deployed to preview environment for testing

**Active Service**: Routes production traffic to the current version

**Preview Service**: Routes preview traffic to the new version for testing

**Promotion**: Switching traffic from blue to green by updating active service

**Rollback**: Switching traffic back to previous version instantly


#### 3 Implementation Guide

## 3. Implementation Guide


#### 3 1 Rollout Configuration

### 3.1 Rollout Configuration

The blue-green rollout is defined in `k8s/blue-green/rollout.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: blue-green-app
  namespace: canary-blue-green
spec:
  replicas: 3
  strategy:
    blueGreen:
      activeService: blue-green-active
      previewService: blue-green-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      previewReplicaCount: 1
```

**Key Parameters:**
- `activeService`: Service for production traffic
- `previewService`: Service for preview traffic
- `autoPromotionEnabled`: false = manual promotion required
- `scaleDownDelaySeconds`: Delay before scaling down old version
- `previewReplicaCount`: Number of preview replicas


#### 3 2 Service Configuration

### 3.2 Service Configuration

Two services are required:

**Active Service** (`blue-green-active`):
- Routes to pods with current rollout hash
- Receives production traffic
- Updated during promotion

**Preview Service** (`blue-green-preview`):
- Routes to pods with new rollout hash
- Receives preview traffic
- Always points to new version


#### 3 3 Ingress Configuration

### 3.3 Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blue-green-ingress
spec:
  rules:
  - host: blue-green.local
    http:
      paths:
      - path: /
        backend:
          service:
            name: blue-green-active
            port: 80
  - host: blue-green-preview.local
    http:
      paths:
      - path: /
        backend:
          service:
            name: blue-green-preview
            port: 80
```


#### 4 Deployment Workflow

## 4. Deployment Workflow


#### 4 1 Initial Deployment

### 4.1 Initial Deployment

1. Deploy rollout manifest
2. Argo Rollouts creates initial ReplicaSet
3. Pods start and pass health checks
4. Active service points to new pods
5. Application is accessible via production URL


#### 4 2 New Version Deployment

### 4.2 New Version Deployment

1. Update container image in rollout spec
2. Commit and push changes to Git
3. ArgoCD detects change and syncs
4. Argo Rollouts creates new ReplicaSet (green)
5. New pods start in preview environment
6. Preview service points to new pods
7. Rollout pauses waiting for promotion


#### 4 3 Testing Preview

### 4.3 Testing Preview

Before promoting to production:

```bash

#### Access Preview Environment

# Access preview environment
curl http://blue-green-preview.local


#### Run Integration Tests

# Run integration tests
./scripts/test-preview.sh blue-green-preview.local


#### Check Application Logs

# Check application logs
kubectl logs -n canary-blue-green -l rollouts-pod-template-hash=<new-hash>


#### Check Metrics

# Check metrics
curl http://blue-green-preview.local/metrics
```


#### 4 4 Promotion

### 4.4 Promotion

When preview tests pass:

```bash

#### Promote New Version To Production

# Promote new version to production
kubectl argo rollouts promote blue-green-app -n canary-blue-green
```

What happens:
1. Active service selector updated to new hash
2. Production traffic switches to green (new) pods
3. Blue (old) pods remain running for `scaleDownDelaySeconds`
4. After delay, old pods are scaled down
5. Deployment complete


#### 4 5 Rollback

### 4.5 Rollback

If issues are detected after promotion:

```bash

#### Instant Rollback To Previous Version

# Instant rollback to previous version
kubectl argo rollouts undo blue-green-app -n canary-blue-green
```

What happens:
1. Active service selector reverted to previous hash
2. Traffic switches back to blue (old) pods instantly
3. Takes < 30 seconds
4. No pods need to restart


#### 5 Operational Commands

## 5. Operational Commands


#### 5 1 View Rollout Status

### 5.1 View Rollout Status

```bash

#### Get Rollout Status

# Get rollout status
kubectl argo rollouts get rollout blue-green-app -n canary-blue-green


#### Watch Rollout In Real Time

# Watch rollout in real-time
kubectl argo rollouts get rollout blue-green-app -n canary-blue-green --watch


#### View Rollout History

# View rollout history
kubectl argo rollouts history blue-green-app -n canary-blue-green
```


#### 5 2 Manage Rollouts

### 5.2 Manage Rollouts

```bash

#### Promote To Production

# Promote to production
kubectl argo rollouts promote blue-green-app -n canary-blue-green


#### Abort Rollout

# Abort rollout
kubectl argo rollouts abort blue-green-app -n canary-blue-green


#### Rollback To Previous Version

# Rollback to previous version
kubectl argo rollouts undo blue-green-app -n canary-blue-green


#### Restart Rollout

# Restart rollout
kubectl argo rollouts restart blue-green-app -n canary-blue-green


#### Pause Rollout If Auto Promotion Enabled 

# Pause rollout (if auto-promotion enabled)
kubectl argo rollouts pause blue-green-app -n canary-blue-green
```


#### 5 3 Debug And Inspect

### 5.3 Debug and Inspect

```bash

#### Describe Rollout For Details

# Describe rollout for details
kubectl describe rollout blue-green-app -n canary-blue-green


#### Get Replicasets

# Get ReplicaSets
kubectl get replicasets -n canary-blue-green


#### View Pods With Labels

# View pods with labels
kubectl get pods -n canary-blue-green --show-labels


#### Check Service Endpoints

# Check service endpoints
kubectl get endpoints -n canary-blue-green


#### View Events

# View events
kubectl get events -n canary-blue-green --sort-by='.lastTimestamp'
```


#### 6 Implementation Phases

## 6. Implementation Phases


#### Phase 1 Preparation Priority Critical 

### Phase 1: Preparation (Priority: Critical)
- [ ] Review current deployment strategy
- [ ] Identify applications for blue-green deployment
- [ ] Assess resource requirements (2x capacity during rollout)
- [ ] Plan rollback procedures
- [ ] Create deployment checklist


#### Phase 2 Manifest Creation Priority Critical 

### Phase 2: Manifest Creation (Priority: Critical)
- [ ] Create rollout manifest with blue-green strategy
- [ ] Define active and preview services
- [ ] Configure ingress for both environments
- [ ] Set appropriate replica counts
- [ ] Configure health checks
- [ ] Set resource limits and requests


#### Phase 3 Initial Deployment Priority High 

### Phase 3: Initial Deployment (Priority: High)
- [ ] Apply namespace if not exists
- [ ] Deploy rollout manifest
- [ ] Wait for pods to be ready
- [ ] Verify active service endpoints
- [ ] Test production URL access
- [ ] Verify health check endpoints
- [ ] Check application functionality


#### Phase 4 First Update Deployment Priority High 

### Phase 4: First Update Deployment (Priority: High)
- [ ] Update container image to new version
- [ ] Commit changes to Git
- [ ] Wait for ArgoCD to sync
- [ ] Verify new ReplicaSet created
- [ ] Check preview pods are running
- [ ] Verify preview service endpoints
- [ ] Test preview URL access


#### Phase 5 Preview Testing Priority Critical 

### Phase 5: Preview Testing (Priority: Critical)
- [ ] Access preview environment
- [ ] Run smoke tests on preview
- [ ] Execute integration test suite
- [ ] Perform manual QA testing
- [ ] Check application logs for errors
- [ ] Monitor preview metrics
- [ ] Validate database migrations if any
- [ ] Test critical user journeys
- [ ] Review performance metrics
- [ ] Get stakeholder approval


#### Phase 6 Promotion Priority Critical 

### Phase 6: Promotion (Priority: Critical)
- [ ] Execute promotion command
- [ ] Monitor active service update
- [ ] Verify traffic switch to new pods
- [ ] Check production URL serves new version
- [ ] Monitor error rates in production
- [ ] Watch application logs
- [ ] Verify all health checks passing
- [ ] Monitor database connections
- [ ] Check external integrations working


#### Phase 7 Post Deployment Validation Priority High 

### Phase 7: Post-Deployment Validation (Priority: High)
- [ ] Run production smoke tests
- [ ] Execute synthetic monitoring tests
- [ ] Verify all endpoints responding
- [ ] Check application metrics
- [ ] Monitor error logs
- [ ] Validate user reports
- [ ] Review performance dashboards
- [ ] Confirm database query performance
- [ ] Check cache hit rates
- [ ] Verify CDN invalidation if needed


#### Phase 8 Cleanup Priority Medium 

### Phase 8: Cleanup (Priority: Medium)
- [ ] Wait for scale-down delay to complete
- [ ] Verify old pods scaled down
- [ ] Check only new ReplicaSet is running
- [ ] Clean up old container images
- [ ] Update documentation
- [ ] Archive rollout logs


#### Phase 9 Rollback Testing Priority High 

### Phase 9: Rollback Testing (Priority: High)
- [ ] Document rollback procedure
- [ ] Test rollback in non-prod environment
- [ ] Time rollback duration
- [ ] Verify rollback completes successfully
- [ ] Practice rollback with team
- [ ] Create rollback runbook


#### Phase 10 Automation Priority Medium 

### Phase 10: Automation (Priority: Medium)
- [ ] Create deployment scripts
- [ ] Automate preview testing
- [ ] Set up automated health checks
- [ ] Configure monitoring alerts
- [ ] Create promotion approval workflow
- [ ] Set up deployment notifications
- [ ] Integrate with CI/CD pipeline


#### 7 Best Practices

## 7. Best Practices


#### 7 1 Health Checks

### 7.1 Health Checks
- Always configure liveness and readiness probes
- Set appropriate `initialDelaySeconds` for app startup
- Use HTTP endpoints that verify critical dependencies
- Keep probe timeouts reasonable


#### 7 2 Resource Planning

### 7.2 Resource Planning
- Ensure cluster has capacity for 2x pods during rollout
- Set resource requests and limits
- Use horizontal pod autoscaling if needed
- Monitor resource utilization


#### 7 3 Testing

### 7.3 Testing
- Test preview thoroughly before promotion
- Run automated test suites
- Perform manual verification of critical features
- Check all external integrations
- Validate data migrations


#### 7 4 Monitoring

### 7.4 Monitoring
- Monitor application metrics during rollout
- Watch for error rate increases
- Track response time changes
- Monitor database connection pools
- Set up alerts for anomalies


#### 7 5 Rollback Readiness

### 7.5 Rollback Readiness
- Keep previous version running during scale-down delay
- Extend `scaleDownDelaySeconds` if needed
- Practice rollback procedures regularly
- Document rollback triggers
- Have rollback decision tree ready


#### 8 Troubleshooting

## 8. Troubleshooting


#### 8 1 Rollout Stuck In Progressing

### 8.1 Rollout Stuck in Progressing
**Problem**: Rollout doesn't progress to preview

**Solutions**:
- Check pod status: `kubectl get pods -n canary-blue-green`
- Check events: `kubectl describe rollout blue-green-app -n canary-blue-green`
- Verify image pull: Check for ImagePullBackOff errors
- Check resource availability: Node capacity issues
- Review health check failures


#### 8 2 Preview Not Accessible

### 8.2 Preview Not Accessible
**Problem**: Cannot access preview environment

**Solutions**:
- Verify preview service exists and has endpoints
- Check ingress configuration
- Verify DNS/hosts file configuration
- Test service directly: `kubectl port-forward`
- Check ingress controller logs


#### 8 3 Traffic Not Switching On Promotion

### 8.3 Traffic Not Switching on Promotion
**Problem**: Production still serves old version after promotion

**Solutions**:
- Verify active service selector updated
- Check service endpoints: `kubectl get endpoints`
- Verify ingress pointing to correct service
- Check for caching issues
- Verify pod labels match service selector


#### 8 4 Old Pods Not Scaling Down

### 8.4 Old Pods Not Scaling Down
**Problem**: Previous version pods remain running

**Solutions**:
- Check `scaleDownDelaySeconds` hasn't passed
- Verify no errors in rollout controller logs
- Check if pods have PreStop hooks delaying shutdown
- Manually scale down if needed


#### 9 Metrics And Monitoring

## 9. Metrics and Monitoring


#### 9 1 Key Metrics

### 9.1 Key Metrics

- **Deployment Frequency**: Deployments per week
- **Rollout Duration**: Time from sync to promotion
- **Preview Test Duration**: Time spent testing preview
- **Promotion Time**: Time for traffic to switch
- **Rollback Count**: Number of rollbacks needed
- **Success Rate**: % of successful promotions


#### 9 2 Monitoring Setup

### 9.2 Monitoring Setup

```bash

#### View Rollout Metrics

# View rollout metrics
kubectl get rollout blue-green-app -n canary-blue-green -o json | jq '.status'


#### Check Pod Metrics

# Check pod metrics
kubectl top pods -n canary-blue-green


#### Monitor Service Endpoints

# Monitor service endpoints
watch kubectl get endpoints -n canary-blue-green
```


#### 10 References

## 10. References

- [Argo Rollouts Blue-Green Documentation](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Blue-Green Deployment Pattern](https://martinfowler.com/bliki/BlueGreenDeployment.html)


#### 11 Appendix

## 11. Appendix


#### A Example Rollout Yaml

### A. Example Rollout YAML

See `k8s/blue-green/rollout.yaml` for complete configuration.


#### B Example Services Yaml

### B. Example Services YAML

See `k8s/blue-green/services.yaml` for service and ingress configuration.


#### C Deployment Checklist

### C. Deployment Checklist

```
[ ] Update image tag in rollout manifest
[ ] Commit and push to Git
[ ] Wait for ArgoCD sync
[ ] Verify preview pods running
[ ] Access preview URL
[ ] Run automated tests
[ ] Perform manual testing
[ ] Get approval for promotion
[ ] Execute promotion command
[ ] Verify traffic switched
[ ] Monitor production metrics
[ ] Confirm no errors
[ ] Wait for scale-down
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
