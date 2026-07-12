# Troubleshooting Reference

Comprehensive troubleshooting guide for Robusta.

## Quick Health Check

```bash
# Overall status
kubectl get pods -n robusta
kubectl get events -n robusta --sort-by='.lastTimestamp'

# Runner logs (main processor)
kubectl logs -n robusta deploy/robusta-runner --tail=100

# Forwarder logs (event collector)
kubectl logs -n robusta deploy/robusta-forwarder --tail=100
```

## Common Issues

### 1. Pods Not Starting

**Symptoms:** Pending, CrashLoopBackOff, ImagePullBackOff

```bash
# Diagnose
kubectl describe pod -n robusta -l app=robusta-runner
kubectl get events -n robusta --sort-by='.lastTimestamp'

# Solutions

# Insufficient resources
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set isSmallCluster=true

# Image pull issues
kubectl get secret -n robusta | grep regcred
```

**Resource Limits:**

```yaml
runner:
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 500m
```

### 2. Alerts Not Received

**Symptoms:** Prometheus alerts exist but Robusta doesn't process them

```bash
# Check AlertManager webhook config
kubectl get secret -n robusta alertmanager-robusta-kube-prometheus-alertmanager \
  -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d

# Verify webhook receiver points to robusta-runner:5000

# Test AlertManager connectivity
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -s http://alertmanager-operated:9093/api/v2/alerts

# Check for webhook delivery errors in AlertManager
kubectl logs -n robusta alertmanager-robusta-kube-prometheus-alertmanager-0
```

### 3. Slack Notifications Failing

**Symptoms:** Alerts processed but no Slack messages

```bash
# Check Slack configuration
kubectl logs -n robusta deploy/robusta-runner | grep -i slack

# Verify API key
kubectl get secret -n robusta robusta-runner-secret \
  -o jsonpath='{.data}' | base64 -d

# Test Slack API
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer xoxb-your-token"
```

**Common Slack Issues:**

| Issue | Solution |
|-------|----------|
| Wrong channel name | Don't include # prefix |
| Bot not in channel | Invite bot to channel |
| Missing scope | Add chat:write, files:write |
| Rate limited | Check Slack API limits |

### 4. Playbooks Not Loading

**Symptoms:** Custom playbooks not executing

```bash
# List loaded playbooks
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta playbooks list

# Check for YAML errors
kubectl logs -n robusta deploy/robusta-runner | grep -i "playbook\|error\|yaml"

# Validate YAML locally
python3 -c "import yaml; yaml.safe_load(open('generated_values.yaml'))"

# Check ConfigMap
kubectl get configmap -n robusta robusta-runner-playbooks -o yaml
```

### 5. High Resource Usage

**Symptoms:** Runner pod consuming excessive CPU/memory

```bash
# Check usage
kubectl top pod -n robusta

# Check for alert storms
kubectl logs -n robusta deploy/robusta-runner | grep -c "Processing alert"
```

**Solutions:**

```yaml
# Add rate limiting
globalConfig:
  alertThrottleMinutes: 5

# Reduce workers
runner:
  workers: 2

# Increase resources
runner:
  resources:
    limits:
      memory: 1Gi
      cpu: 1000m
```

### 6. Prometheus Stack Issues

**Symptoms:** Prometheus/Grafana pods failing

```bash
# Check Prometheus
kubectl get pods -n robusta -l app.kubernetes.io/name=prometheus
kubectl logs -n robusta prometheus-robusta-kube-prometheus-prometheus-0

# Check PVCs
kubectl get pvc -n robusta

# Check Grafana
kubectl logs -n robusta deploy/robusta-grafana
```

**EKS Storage Issue:**

```bash
# Ensure EBS CSI driver is installed
kubectl get csidrivers | grep ebs
```

### 7. Multi-Cluster Issues

**Symptoms:** Alerts from wrong cluster or missing cluster context

```bash
# Verify cluster name
helm get values robusta -n robusta | grep clusterName

# Update cluster name
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=correct-cluster-name
```

### 8. Webhook Connectivity

**Symptoms:** External sinks not receiving data

```bash
# Test outbound connectivity
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -I https://hooks.slack.com

# Check network policies
kubectl get networkpolicies -n robusta

# Test specific endpoints
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -I https://api.pagerduty.com
```

## Advanced Debugging

### Enable Debug Logging

```yaml
# In generated_values.yaml
runner:
  log_level: DEBUG
```

### Access Runner Shell

```bash
kubectl exec -it -n robusta deploy/robusta-runner -- bash

# Inside container
robusta playbooks list
robusta sinks list
robusta version
```

### Test Alert Processing

```bash
# Send test alert
kubectl exec -n robusta deploy/robusta-runner -- robusta demo

# Trigger specific playbook
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta playbooks trigger prometheus_alert \
  --alert-name KubePodCrashLooping \
  --namespace default \
  --labels '{"severity":"warning","pod":"test-pod"}'
```

### Inspect Internal State

```bash
# Check runner metrics
kubectl exec -n robusta deploy/robusta-runner -- \
  curl http://localhost:5000/metrics

# Check health endpoint
kubectl exec -n robusta deploy/robusta-runner -- \
  curl http://localhost:5000/health
```

## Recovery Procedures

### Reinstall Robusta

```bash
# Backup values
cp generated_values.yaml generated_values.yaml.bak

# Uninstall
helm uninstall robusta -n robusta

# Wait for cleanup
kubectl get pods -n robusta -w

# Reinstall
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --namespace robusta
```

### Reset Configuration

```bash
# Regenerate config (keeps signing keys)
mv generated_values.yaml generated_values.yaml.old
pipx run robusta-cli gen-config --enable-prometheus-stack

# Merge old sink/playbook configs back
# Then reinstall
```

### Force Pod Restart

```bash
kubectl rollout restart deployment -n robusta robusta-runner
kubectl rollout restart deployment -n robusta robusta-forwarder
```

## Log Analysis

### Common Log Patterns

| Pattern | Meaning |
|---------|---------|
| `Processing alert` | Alert received from AlertManager |
| `Sink error` | Failed to send to notification sink |
| `Playbook matched` | Playbook triggered for alert |
| `Action completed` | Action executed successfully |
| `Rate limited` | Alert throttled |

### Useful Log Commands

```bash
# Find errors
kubectl logs -n robusta deploy/robusta-runner | grep -i error

# Find specific alert processing
kubectl logs -n robusta deploy/robusta-runner | grep "KubePodCrashLooping"

# Watch logs in real-time
kubectl logs -n robusta deploy/robusta-runner -f
```

## Getting Help

- [Robusta Slack Community](https://bit.ly/robusta-slack)
- [GitHub Issues](https://github.com/robusta-dev/robusta/issues)
- [Official Documentation](https://docs.robusta.dev/master/)
