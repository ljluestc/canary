# PRD: Blue-Green Deployment Guide

## 1. Executive Summary

### 1.1 Overview
This document provides a comprehensive guide for implementing and managing blue-green deployments using Argo Rollouts on Kubernetes. Blue-green deployment is a release strategy that reduces downtime and risk by running two identical production environments (blue and green).

### 1.2 Business Objectives
- Achieve zero-downtime deployments
- Enable instant rollback capability
- Provide preview environment for testing before production
- Reduce deployment risk
- Improve deployment confidence

### 1.3 Success Criteria
- [ ] Zero-downtime deployment achieved
- [ ] Rollback time < 30 seconds
- [ ] Preview environment accessible before promotion
- [ ] All health checks passing before traffic switch
- [ ] Deployment automation working end-to-end

## 2. Blue-Green Deployment Strategy

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

### 2.2 Key Concepts

**Blue Environment**: Currently running production version serving live traffic

**Green Environment**: New version deployed to preview environment for testing

**Active Service**: Routes production traffic to the current version

**Preview Service**: Routes preview traffic to the new version for testing

**Promotion**: Switching traffic from blue to green by updating active service

**Rollback**: Switching traffic back to previous version instantly

## 3. Implementation Guide

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

## 4. Deployment Workflow

### 4.1 Initial Deployment

1. Deploy rollout manifest
2. Argo Rollouts creates initial ReplicaSet
3. Pods start and pass health checks
4. Active service points to new pods
5. Application is accessible via production URL

### 4.2 New Version Deployment

1. Update container image in rollout spec
2. Commit and push changes to Git
3. ArgoCD detects change and syncs
4. Argo Rollouts creates new ReplicaSet (green)
5. New pods start in preview environment
6. Preview service points to new pods
7. Rollout pauses waiting for promotion

### 4.3 Testing Preview

Before promoting to production:

```bash
# Access preview environment
curl http://blue-green-preview.local

# Run integration tests
./scripts/test-preview.sh blue-green-preview.local

# Check application logs
kubectl logs -n canary-blue-green -l rollouts-pod-template-hash=<new-hash>

# Check metrics
curl http://blue-green-preview.local/metrics
```

### 4.4 Promotion

When preview tests pass:

```bash
# Promote new version to production
kubectl argo rollouts promote blue-green-app -n canary-blue-green
```

What happens:
1. Active service selector updated to new hash
2. Production traffic switches to green (new) pods
3. Blue (old) pods remain running for `scaleDownDelaySeconds`
4. After delay, old pods are scaled down
5. Deployment complete

### 4.5 Rollback

If issues are detected after promotion:

```bash
# Instant rollback to previous version
kubectl argo rollouts undo blue-green-app -n canary-blue-green
```

What happens:
1. Active service selector reverted to previous hash
2. Traffic switches back to blue (old) pods instantly
3. Takes < 30 seconds
4. No pods need to restart

## 5. Operational Commands

### 5.1 View Rollout Status

```bash
# Get rollout status
kubectl argo rollouts get rollout blue-green-app -n canary-blue-green

# Watch rollout in real-time
kubectl argo rollouts get rollout blue-green-app -n canary-blue-green --watch

# View rollout history
kubectl argo rollouts history blue-green-app -n canary-blue-green
```

### 5.2 Manage Rollouts

```bash
# Promote to production
kubectl argo rollouts promote blue-green-app -n canary-blue-green

# Abort rollout
kubectl argo rollouts abort blue-green-app -n canary-blue-green

# Rollback to previous version
kubectl argo rollouts undo blue-green-app -n canary-blue-green

# Restart rollout
kubectl argo rollouts restart blue-green-app -n canary-blue-green

# Pause rollout (if auto-promotion enabled)
kubectl argo rollouts pause blue-green-app -n canary-blue-green
```

### 5.3 Debug and Inspect

```bash
# Describe rollout for details
kubectl describe rollout blue-green-app -n canary-blue-green

# Get ReplicaSets
kubectl get replicasets -n canary-blue-green

# View pods with labels
kubectl get pods -n canary-blue-green --show-labels

# Check service endpoints
kubectl get endpoints -n canary-blue-green

# View events
kubectl get events -n canary-blue-green --sort-by='.lastTimestamp'
```

## 6. Implementation Phases

### Phase 1: Preparation (Priority: Critical)
- [ ] Review current deployment strategy
- [ ] Identify applications for blue-green deployment
- [ ] Assess resource requirements (2x capacity during rollout)
- [ ] Plan rollback procedures
- [ ] Create deployment checklist

### Phase 2: Manifest Creation (Priority: Critical)
- [ ] Create rollout manifest with blue-green strategy
- [ ] Define active and preview services
- [ ] Configure ingress for both environments
- [ ] Set appropriate replica counts
- [ ] Configure health checks
- [ ] Set resource limits and requests

### Phase 3: Initial Deployment (Priority: High)
- [ ] Apply namespace if not exists
- [ ] Deploy rollout manifest
- [ ] Wait for pods to be ready
- [ ] Verify active service endpoints
- [ ] Test production URL access
- [ ] Verify health check endpoints
- [ ] Check application functionality

### Phase 4: First Update Deployment (Priority: High)
- [ ] Update container image to new version
- [ ] Commit changes to Git
- [ ] Wait for ArgoCD to sync
- [ ] Verify new ReplicaSet created
- [ ] Check preview pods are running
- [ ] Verify preview service endpoints
- [ ] Test preview URL access

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

### Phase 8: Cleanup (Priority: Medium)
- [ ] Wait for scale-down delay to complete
- [ ] Verify old pods scaled down
- [ ] Check only new ReplicaSet is running
- [ ] Clean up old container images
- [ ] Update documentation
- [ ] Archive rollout logs

### Phase 9: Rollback Testing (Priority: High)
- [ ] Document rollback procedure
- [ ] Test rollback in non-prod environment
- [ ] Time rollback duration
- [ ] Verify rollback completes successfully
- [ ] Practice rollback with team
- [ ] Create rollback runbook

### Phase 10: Automation (Priority: Medium)
- [ ] Create deployment scripts
- [ ] Automate preview testing
- [ ] Set up automated health checks
- [ ] Configure monitoring alerts
- [ ] Create promotion approval workflow
- [ ] Set up deployment notifications
- [ ] Integrate with CI/CD pipeline

## 7. Best Practices

### 7.1 Health Checks
- Always configure liveness and readiness probes
- Set appropriate `initialDelaySeconds` for app startup
- Use HTTP endpoints that verify critical dependencies
- Keep probe timeouts reasonable

### 7.2 Resource Planning
- Ensure cluster has capacity for 2x pods during rollout
- Set resource requests and limits
- Use horizontal pod autoscaling if needed
- Monitor resource utilization

### 7.3 Testing
- Test preview thoroughly before promotion
- Run automated test suites
- Perform manual verification of critical features
- Check all external integrations
- Validate data migrations

### 7.4 Monitoring
- Monitor application metrics during rollout
- Watch for error rate increases
- Track response time changes
- Monitor database connection pools
- Set up alerts for anomalies

### 7.5 Rollback Readiness
- Keep previous version running during scale-down delay
- Extend `scaleDownDelaySeconds` if needed
- Practice rollback procedures regularly
- Document rollback triggers
- Have rollback decision tree ready

## 8. Troubleshooting

### 8.1 Rollout Stuck in Progressing
**Problem**: Rollout doesn't progress to preview

**Solutions**:
- Check pod status: `kubectl get pods -n canary-blue-green`
- Check events: `kubectl describe rollout blue-green-app -n canary-blue-green`
- Verify image pull: Check for ImagePullBackOff errors
- Check resource availability: Node capacity issues
- Review health check failures

### 8.2 Preview Not Accessible
**Problem**: Cannot access preview environment

**Solutions**:
- Verify preview service exists and has endpoints
- Check ingress configuration
- Verify DNS/hosts file configuration
- Test service directly: `kubectl port-forward`
- Check ingress controller logs

### 8.3 Traffic Not Switching on Promotion
**Problem**: Production still serves old version after promotion

**Solutions**:
- Verify active service selector updated
- Check service endpoints: `kubectl get endpoints`
- Verify ingress pointing to correct service
- Check for caching issues
- Verify pod labels match service selector

### 8.4 Old Pods Not Scaling Down
**Problem**: Previous version pods remain running

**Solutions**:
- Check `scaleDownDelaySeconds` hasn't passed
- Verify no errors in rollout controller logs
- Check if pods have PreStop hooks delaying shutdown
- Manually scale down if needed

## 9. Metrics and Monitoring

### 9.1 Key Metrics

- **Deployment Frequency**: Deployments per week
- **Rollout Duration**: Time from sync to promotion
- **Preview Test Duration**: Time spent testing preview
- **Promotion Time**: Time for traffic to switch
- **Rollback Count**: Number of rollbacks needed
- **Success Rate**: % of successful promotions

### 9.2 Monitoring Setup

```bash
# View rollout metrics
kubectl get rollout blue-green-app -n canary-blue-green -o json | jq '.status'

# Check pod metrics
kubectl top pods -n canary-blue-green

# Monitor service endpoints
watch kubectl get endpoints -n canary-blue-green
```

## 10. References

- [Argo Rollouts Blue-Green Documentation](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Blue-Green Deployment Pattern](https://martinfowler.com/bliki/BlueGreenDeployment.html)

## 11. Appendix

### A. Example Rollout YAML

See `k8s/blue-green/rollout.yaml` for complete configuration.

### B. Example Services YAML

See `k8s/blue-green/services.yaml` for service and ingress configuration.

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
