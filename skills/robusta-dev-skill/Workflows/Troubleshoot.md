# Troubleshoot Robusta

Common issues and debugging steps for Robusta installations.

## Quick Diagnostics

```bash
# Check pod status
kubectl get pods -n robusta

# Check runner logs
kubectl logs -n robusta deploy/robusta-runner --tail=100

# Check forwarder logs
kubectl logs -n robusta deploy/robusta-forwarder --tail=100

# Check events
kubectl get events -n robusta --sort-by='.lastTimestamp'
```

## Common Issues

### 1. Pods Not Starting

**Symptoms:** Pods stuck in Pending, CrashLoopBackOff, or ImagePullBackOff

```bash
# Check pod events
kubectl describe pod -n robusta -l app=robusta-runner

# Check resource limits
kubectl get pods -n robusta -o yaml | grep -A5 resources

# For small clusters, reduce resources
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set isSmallCluster=true
```

### 2. Alerts Not Firing

**Symptoms:** Prometheus alerts exist but Robusta doesn't process them

```bash
# Verify AlertManager is sending to Robusta
kubectl get svc -n robusta

# Check AlertManager config
kubectl get secret -n robusta alertmanager-robusta-kube-prometheus-alertmanager \
  -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d

# Verify webhook URL in AlertManager
# Should have receiver pointing to robusta-runner:5000

# Test AlertManager connection
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -s http://alertmanager-operated:9093/api/v2/alerts
```

### 3. Slack Messages Not Sending

**Symptoms:** Alerts processed but no Slack notifications

```bash
# Check sink configuration in logs
kubectl logs -n robusta deploy/robusta-runner | grep -i slack

# Verify API key is set
kubectl get secret -n robusta robusta-runner-secret \
  -o jsonpath='{.data.SLACK_API_KEY}' | base64 -d

# Test Slack API directly
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer xoxb-your-token"

# Common issues:
# - Wrong channel name (don't include #)
# - Bot not invited to channel
# - Missing chat:write scope
```

### 4. Playbooks Not Loading

**Symptoms:** Custom playbooks defined but not executing

```bash
# List loaded playbooks
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta playbooks list

# Check for YAML syntax errors
kubectl logs -n robusta deploy/robusta-runner | grep -i "playbook\|error\|yaml"

# Validate YAML syntax locally
python -c "import yaml; yaml.safe_load(open('generated_values.yaml'))"
```

### 5. High Memory/CPU Usage

**Symptoms:** Runner pod consuming excessive resources

```bash
# Check current usage
kubectl top pod -n robusta

# Check for alert storms
kubectl logs -n robusta deploy/robusta-runner | grep -c "Processing alert"

# Add rate limiting to playbooks
# In generated_values.yaml:
globalConfig:
  alertThrottleMinutes: 5

# Reduce concurrent processing
runner:
  resources:
    limits:
      memory: 512Mi
      cpu: 500m
```

### 6. Prometheus Stack Issues

**Symptoms:** Prometheus/Grafana pods failing (all-in-one install)

```bash
# Check Prometheus pods
kubectl get pods -n robusta -l app.kubernetes.io/name=prometheus

# Check PVC status (EKS/AKS may need storage class)
kubectl get pvc -n robusta

# For EKS without EBS CSI:
# Install EBS CSI driver first

# Check Grafana
kubectl logs -n robusta deploy/robusta-grafana
```

### 7. Multi-Cluster Issues

**Symptoms:** Alerts from wrong cluster or missing cluster context

```bash
# Verify cluster name is set
helm get values robusta -n robusta | grep clusterName

# Update cluster name
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=correct-cluster-name
```

## Advanced Debugging

### Enable Debug Logging

```yaml
# In generated_values.yaml
runner:
  log_level: DEBUG
```

### Check Robusta Internals

```bash
# Access runner shell
kubectl exec -it -n robusta deploy/robusta-runner -- bash

# Inside container:
robusta playbooks list
robusta sinks list
robusta version
```

### Test Alert Processing

```bash
# Send test alert
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta demo

# Trigger specific playbook
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta playbooks trigger prometheus_alert \
  --alert-name KubePodCrashLooping \
  --namespace default \
  --labels '{"severity":"warning","pod":"test-pod"}'
```

### Network Connectivity

```bash
# Test sink connectivity from runner
kubectl exec -n robusta deploy/robusta-runner -- \
  curl -I https://slack.com

# Test AlertManager connectivity
kubectl exec -n robusta deploy/robusta-runner -- \
  curl http://alertmanager-operated:9093/-/healthy
```

## Recovery Steps

### Reinstall Robusta

```bash
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
# Regenerate config
rm generated_values.yaml
pipx run robusta-cli gen-config --enable-prometheus-stack

# Reinstall with fresh config
helm upgrade --install robusta robusta/robusta \
  -f ./generated_values.yaml
```

## Getting Help

- [Robusta Slack Community](https://bit.ly/robusta-slack)
- [GitHub Issues](https://github.com/robusta-dev/robusta/issues)
- [Official Docs](https://docs.robusta.dev/master/)
