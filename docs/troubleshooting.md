# PRD: Troubleshooting Guide for Argo Rollouts Deployment System

## 1. Executive Summary

### 1.1 Overview
This document provides comprehensive troubleshooting procedures for the Blue-Green and Canary deployment system using Argo Rollouts, ArgoCD, and Kubernetes. It covers common issues, diagnostic steps, and resolution procedures.

### 1.2 Objectives
- Provide systematic approach to problem diagnosis
- Document common issues and solutions
- Enable quick problem resolution
- Reduce mean time to recovery (MTTR)
- Build team troubleshooting capability

### 1.3 Success Criteria
- [ ] All documented issues have clear resolution steps
- [ ] Diagnostic commands provided for each scenario
- [ ] Root cause analysis included
- [ ] Prevention measures documented
- [ ] MTTR < 15 minutes for common issues

## 2. Troubleshooting Framework

### 2.1 Diagnostic Approach

1. **Identify Symptoms**: What is failing or behaving incorrectly?
2. **Gather Information**: Run diagnostic commands
3. **Analyze Data**: Review logs, events, status
4. **Form Hypothesis**: What might be causing the issue?
5. **Test Solution**: Apply fix and verify
6. **Document**: Record issue and resolution

### 2.2 Essential Tools

```bash
# kubectl - Kubernetes CLI
kubectl version

# argo rollouts plugin
kubectl argo rollouts version

# argocd CLI
argocd version

# Other tools
curl, jq, watch, stern (log aggregator)
```

## 3. ArgoCD Issues

### 3.1 ArgoCD Server Not Starting

**Symptoms**:
- ArgoCD UI not accessible
- Pods in CrashLoopBackOff or Pending state

**Diagnostic Commands**:
```bash
# Check pod status
kubectl get pods -n argocd

# View pod logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server --tail=100

# Check events
kubectl get events -n argocd --sort-by='.lastTimestamp' | head -20

# Describe pod
kubectl describe pod -n argocd -l app.kubernetes.io/name=argocd-server
```

**Common Causes and Solutions**:

1. **Insufficient Resources**
   - Check: Node resource availability
   - Solution: Scale cluster or adjust resource requests

2. **Image Pull Errors**
   - Check: `kubectl describe pod` for ImagePullBackOff
   - Solution: Check image registry access, credentials

3. **PVC Issues**
   - Check: PersistentVolumeClaims status
   - Solution: Verify storage class, provision volumes

### 3.2 Application Not Syncing

**Symptoms**:
- Application shows "OutOfSync" status
- Changes in Git not reflected in cluster

**Diagnostic Commands**:
```bash
# Check application status
argocd app get <app-name>

# View sync status
kubectl get application -n argocd <app-name> -o yaml

# Check ArgoCD repo server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server --tail=100

# Test Git repository access
argocd repo list
```

**Solutions**:

1. **Repository Access Issues**
   ```bash
   # Re-add repository with correct credentials
   argocd repo add https://github.com/org/repo.git --username <user> --password <token>
   ```

2. **Sync Policy**
   ```bash
   # Enable auto-sync
   argocd app set <app-name> --sync-policy automated

   # Force sync
   argocd app sync <app-name> --force
   ```

3. **Resource Hooks Failing**
   ```bash
   # Check hook status
   kubectl get all -n <namespace> -l argocd.argoproj.io/hook

   # Delete failed hooks
   kubectl delete pod -n <namespace> -l argocd.argoproj.io/hook
   ```

### 3.3 Cannot Access ArgoCD UI

**Symptoms**:
- Connection refused or timeout
- 502 Bad Gateway

**Diagnostic Commands**:
```bash
# Check service
kubectl get svc -n argocd argocd-server

# Check port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Check ingress (if using)
kubectl get ingress -n argocd
kubectl describe ingress -n argocd argocd-server-ingress
```

**Solutions**:

1. **Port Forward Issues**
   ```bash
   # Kill existing port-forwards
   pkill -f "port-forward.*argocd"

   # Restart port-forward
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```

2. **Ingress Configuration**
   - Verify ingress controller is running
   - Check ingress annotations
   - Verify DNS/hosts file

## 4. Argo Rollouts Issues

### 4.1 Rollout Stuck in Progressing

**Symptoms**:
- Rollout shows "Progressing" indefinitely
- New pods not starting or not ready

**Diagnostic Commands**:
```bash
# Check rollout status
kubectl argo rollouts get rollout <rollout-name> -n <namespace>

# View rollout details
kubectl describe rollout <rollout-name> -n <namespace>

# Check pods
kubectl get pods -n <namespace> -l rollout=<rollout-name>

# Check replica sets
kubectl get rs -n <namespace> -l rollout=<rollout-name>

# View events
kubectl get events -n <namespace> --field-selector involvedObject.name=<rollout-name>
```

**Common Causes and Solutions**:

1. **Image Pull Failures**
   ```bash
   # Check pod status
   kubectl describe pod <pod-name> -n <namespace>

   # Solution: Fix image tag or registry access
   ```

2. **Insufficient Resources**
   ```bash
   # Check node resources
   kubectl top nodes
   kubectl describe nodes

   # Solution: Scale cluster or reduce requests
   ```

3. **Health Check Failures**
   ```bash
   # Check probe configuration
   kubectl get rollout <name> -n <namespace> -o yaml | grep -A 10 'Probe'

   # Check pod logs for startup issues
   kubectl logs <pod-name> -n <namespace>
   ```

4. **Missing Services**
   ```bash
   # Verify services exist
   kubectl get svc -n <namespace>

   # Check service selectors match pod labels
   kubectl get svc <service-name> -n <namespace> -o yaml
   ```

### 4.2 Analysis Always Failing

**Symptoms**:
- AnalysisRun status shows "Failed"
- Automatic rollback occurring
- Canary not progressing

**Diagnostic Commands**:
```bash
# List analysis runs
kubectl get analysisrun -n <namespace>

# Describe analysis run
kubectl describe analysisrun <name> -n <namespace>

# View analysis run details
kubectl get analysisrun <name> -n <namespace> -o yaml

# Check Prometheus connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://prometheus.monitoring.svc:9090/api/v1/query?query=up
```

**Common Causes and Solutions**:

1. **Prometheus Not Accessible**
   ```bash
   # Verify Prometheus service
   kubectl get svc -n monitoring prometheus-server

   # Test from within cluster
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
     curl http://prometheus.monitoring.svc:9090/-/healthy
   ```

2. **Incorrect PromQL Query**
   ```bash
   # Test query in Prometheus UI
   kubectl port-forward -n monitoring svc/prometheus-server 9090:80
   # Then open http://localhost:9090 and test query
   ```

3. **No Metrics Available**
   ```bash
   # Check if application exports metrics
   kubectl port-forward <pod-name> -n <namespace> 8080:8080
   curl http://localhost:8080/metrics

   # Verify ServiceMonitor
   kubectl get servicemonitor -n <namespace>
   ```

4. **Wrong Metric Labels**
   ```bash
   # Check available metrics and labels
   # In Prometheus UI, explore metrics with autocomplete
   # Verify labels match those in AnalysisTemplate
   ```

### 4.3 Traffic Not Shifting

**Symptoms**:
- Canary weight doesn't change
- All traffic still going to stable version

**Diagnostic Commands**:
```bash
# Check ingress annotations
kubectl get ingress <ingress-name> -n <namespace> -o jsonpath='{.metadata.annotations}'

# View rollout status
kubectl argo rollouts get rollout <name> -n <namespace>

# Check services have endpoints
kubectl get endpoints -n <namespace>

# Test traffic distribution
for i in {1..100}; do curl http://app.local; done | sort | uniq -c
```

**Common Causes and Solutions**:

1. **Ingress Controller Doesn't Support Canary**
   ```bash
   # Verify ingress class supports canary
   kubectl get ingressclass

   # For nginx, check version supports canary annotations
   kubectl get pods -n ingress-nginx
   ```

2. **Wrong Ingress Referenced**
   ```bash
   # Verify rollout points to correct ingress
   kubectl get rollout <name> -n <namespace> -o yaml | grep ingress

   # Check ingress name matches
   kubectl get ingress -n <namespace>
   ```

3. **Canary Service Has No Endpoints**
   ```bash
   # Check both services
   kubectl get endpoints -n <namespace>

   # Verify pod labels match service selectors
   kubectl get pods -n <namespace> --show-labels
   ```

### 4.4 Rollout Not Starting

**Symptoms**:
- Rollout stays in "Healthy" after image change
- No new ReplicaSet created

**Diagnostic Commands**:
```bash
# Check if image actually changed
kubectl get rollout <name> -n <namespace> -o jsonpath='{.spec.template.spec.containers[0].image}'

# View rollout events
kubectl describe rollout <name> -n <namespace>

# Check Argo Rollouts controller logs
kubectl logs -n argo-rollouts -l app.kubernetes.io/name=argo-rollouts
```

**Solutions**:

1. **Image Tag Not Changed**
   - Verify image tag is different from current
   - Don't use `:latest` tag in production

2. **ArgoCD Not Syncing**
   - Check ArgoCD application status
   - Force sync if needed

3. **Rollout Paused**
   ```bash
   # Check if paused
   kubectl get rollout <name> -n <namespace> -o jsonpath='{.spec.paused}'

   # Resume if paused
   kubectl argo rollouts resume <name> -n <namespace>
   ```

## 5. Kubernetes Infrastructure Issues

### 5.1 Pods Not Starting

**Diagnostic Commands**:
```bash
# Pod status
kubectl get pods -n <namespace>

# Detailed pod info
kubectl describe pod <pod-name> -n <namespace>

# Pod logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous  # For crashed pods

# Events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

**Common Issues**:

1. ImagePullBackOff
2. CrashLoopBackOff
3. Pending (resource constraints)
4. CreateContainerConfigError

### 5.2 Service Not Accessible

**Diagnostic Commands**:
```bash
# Check service
kubectl get svc <service-name> -n <namespace>

# Check endpoints
kubectl get endpoints <service-name> -n <namespace>

# Test from within cluster
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- \
  curl http://<service-name>.<namespace>.svc.cluster.local

# Check pod labels vs service selector
kubectl get svc <service-name> -n <namespace> -o yaml | grep selector
kubectl get pods -n <namespace> --show-labels
```

**Solutions**:

1. **No Endpoints**
   - Verify pod labels match service selector
   - Check pods are Ready

2. **DNS Not Working**
   ```bash
   # Test DNS
   kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup <service-name>.<namespace>.svc.cluster.local
   ```

### 5.3 Ingress Not Working

**Diagnostic Commands**:
```bash
# Check ingress
kubectl get ingress -n <namespace>
kubectl describe ingress <ingress-name> -n <namespace>

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Test ingress directly
curl -H "Host: app.local" http://<ingress-controller-ip>
```

**Solutions**:

1. **Ingress Controller Not Running**
   ```bash
   kubectl get pods -n ingress-nginx
   ```

2. **DNS/Hosts Not Configured**
   - Add entries to /etc/hosts
   - Or use `-H "Host: app.local"` with curl

3. **Backend Service Issues**
   - Verify service exists and has endpoints

## 6. Implementation Phases

### Phase 1: Documentation and Knowledge Base (Priority: Critical)
- [ ] Document all common issues encountered
- [ ] Create troubleshooting decision trees
- [ ] Build runbook library
- [ ] Create quick reference cards
- [ ] Set up internal wiki/knowledge base
- [ ] Train team on troubleshooting procedures

### Phase 2: Diagnostic Tooling (Priority: High)
- [ ] Install kubectl plugins (stern, ctx, ns)
- [ ] Set up log aggregation
- [ ] Create diagnostic scripts
- [ ] Build health check automation
- [ ] Configure monitoring dashboards
- [ ] Set up alerting rules

### Phase 3: Common Issue Resolution (Priority: Critical)
- [ ] Test ArgoCD server restart procedure
- [ ] Verify application sync troubleshooting
- [ ] Test rollout stuck scenarios
- [ ] Practice analysis failure debugging
- [ ] Validate traffic routing issues
- [ ] Test pod startup failures
- [ ] Practice service accessibility checks
- [ ] Validate ingress troubleshooting

### Phase 4: Automated Diagnostics (Priority: Medium)
- [ ] Create health check scripts
- [ ] Build automated log analysis
- [ ] Set up anomaly detection
- [ ] Create self-healing mechanisms
- [ ] Implement auto-remediation for common issues
- [ ] Build diagnostic CLI tool

### Phase 5: Monitoring and Alerting (Priority: High)
- [ ] Set up ArgoCD alerts
- [ ] Configure Rollout failure alerts
- [ ] Create analysis failure notifications
- [ ] Set up pod health alerts
- [ ] Configure service availability alerts
- [ ] Set up ingress health monitoring
- [ ] Create alert runbooks

### Phase 6: Incident Response (Priority: High)
- [ ] Create incident response playbook
- [ ] Define severity levels
- [ ] Set up on-call rotation
- [ ] Create escalation procedures
- [ ] Build incident postmortem template
- [ ] Conduct incident response drills
- [ ] Create communication templates

### Phase 7: Continuous Improvement (Priority: Medium)
- [ ] Review incidents monthly
- [ ] Update troubleshooting guides
- [ ] Add new issues to knowledge base
- [ ] Improve automation
- [ ] Conduct postmortems
- [ ] Share learnings across team
- [ ] Update runbooks based on feedback

## 7. Quick Reference

### 7.1 Essential Commands

```bash
# Rollouts
kubectl argo rollouts get rollout <name> -n <namespace> --watch
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts undo <name> -n <namespace>

# ArgoCD
argocd app get <app-name>
argocd app sync <app-name>
argocd app logs <app-name>

# Kubernetes
kubectl get pods -n <namespace>
kubectl logs <pod-name> -n <namespace> --tail=100 -f
kubectl describe <resource> <name> -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### 7.2 Emergency Procedures

**Rollback Deployment**:
```bash
kubectl argo rollouts abort <rollout-name> -n <namespace>
kubectl argo rollouts undo <rollout-name> -n <namespace>
```

**Restart Application**:
```bash
kubectl rollout restart deployment <name> -n <namespace>
# Or for rollouts:
kubectl argo rollouts restart <name> -n <namespace>
```

**Scale to Zero (Emergency Stop)**:
```bash
kubectl scale rollout <name> -n <namespace> --replicas=0
```

### 7.3 Health Check Script

```bash
#!/bin/bash
# health-check.sh

NAMESPACE=$1
ROLLOUT=$2

echo "Checking rollout status..."
kubectl argo rollouts get rollout $ROLLOUT -n $NAMESPACE

echo "\nChecking pods..."
kubectl get pods -n $NAMESPACE -l rollout=$ROLLOUT

echo "\nChecking services..."
kubectl get svc -n $NAMESPACE

echo "\nChecking ingress..."
kubectl get ingress -n $NAMESPACE

echo "\nRecent events..."
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
```

## 8. Escalation Matrix

| Issue Severity | Response Time | Escalation Path |
|---------------|---------------|-----------------|
| P1 - Critical | < 15 minutes | On-call → Team Lead → Engineering Manager |
| P2 - High | < 1 hour | Team member → On-call |
| P3 - Medium | < 4 hours | Team member → Team Lead |
| P4 - Low | < 24 hours | Team member |

## 9. Postmortem Template

```markdown
# Incident Postmortem: [Title]

## Summary
[Brief description]

## Timeline
- HH:MM - Issue detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix applied
- HH:MM - Incident resolved

## Root Cause
[Technical explanation]

## Resolution
[What fixed the issue]

## Action Items
- [ ] Prevent recurrence
- [ ] Improve detection
- [ ] Update documentation
- [ ] Add monitoring/alerts
```

## 10. References

- [Argo Rollouts Troubleshooting](https://argoproj.github.io/argo-rollouts/troubleshooting/)
- [ArgoCD Troubleshooting Guide](https://argo-cd.readthedocs.io/en/stable/operator-manual/troubleshooting/)
- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)

## 11. Contact Information

- On-call rotation: [PagerDuty/phone number]
- Slack channel: #deployments
- Email: ops@company.com
