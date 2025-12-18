# HolmesGPT HTTP API Reference

REST API documentation for HolmesGPT server deployments.

## Overview

HolmesGPT provides a REST API for programmatic access when deployed
in Kubernetes. The API supports both synchronous requests and
Server-Sent Events (SSE) for streaming responses.

## Base URL

After Helm installation:

```text
http://holmesgpt-holmes.<namespace>.svc.cluster.local
```

For local testing:

```bash
kubectl port-forward -n holmesgpt svc/holmesgpt-holmes 8080:80
# Base URL: http://localhost:8080
```

## Endpoints

### GET /api/model

List available AI models.

**Request:**

```bash
curl http://localhost:8080/api/model
```

**Response:**

```json
{
  "models": ["sonnet", "opus", "gpt4", "gpt4o"]
}
```

### POST /api/chat

General-purpose conversational interface.

**Request:**

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "ask": "what pods are unhealthy in production namespace?",
    "model": "sonnet",
    "conversation_history": [],
    "include_tool_calls": true
  }'
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ask` | string | Yes | User question |
| `model` | string | Yes | Model name from modelList |
| `conversation_history` | array | No | Previous messages for context |
| `include_tool_calls` | boolean | No | Include tool execution details |
| `prompt_template` | string | No | Custom Jinja2 template |

**Response:**

```json
{
  "analysis": "Based on my investigation...",
  "sections": {
    "alert_explanation": "...",
    "key_findings": "...",
    "root_causes": "...",
    "next_steps": "..."
  },
  "conversation_history": [...],
  "tool_calls": [...],
  "metadata": {
    "token_count": 1500,
    "model": "sonnet"
  }
}
```

### POST /api/investigate

Automated incident investigation.

**Request:**

```bash
curl -X POST http://localhost:8080/api/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "KubePodCrashLooping",
    "alert_labels": {
      "namespace": "production",
      "pod": "api-gateway-xxx"
    },
    "model": "sonnet"
  }'
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alert_name` | string | No | Alert name for investigation |
| `alert_labels` | object | No | Alert labels for context |
| `model` | string | Yes | Model name |
| `runbook` | string | No | Custom runbook instructions |

**Response:**

```json
{
  "analysis": "Investigation complete...",
  "sections": {
    "alert_explanation": "This alert fires when...",
    "key_findings": "1. Pod restarted 5 times...",
    "root_causes": "Memory limit exceeded...",
    "next_steps": "1. Increase memory limits..."
  },
  "tool_calls": [
    {
      "tool": "kubectl_get_pods",
      "parameters": {"namespace": "production"},
      "result": "...",
      "status": "success"
    }
  ]
}
```

### POST /api/stream/investigate

Streaming investigation with SSE.

**Request:**

```bash
curl -X POST http://localhost:8080/api/stream/investigate \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "alert_name": "HighMemoryUsage",
    "model": "sonnet"
  }'
```

**SSE Event Types:**

| Event | Description |
|-------|-------------|
| `start_tool_calling` | Tool execution beginning |
| `tool_calling_result` | Tool output with status |
| `ai_message` | AI reasoning/text |
| `approval_required` | Request for user approval |
| `ai_answer_end` | Final response |
| `token_count` | Token usage update |
| `conversation_history_compacted` | History truncated |
| `error` | Processing failure |

**Example SSE Stream:**

```text
event: start_tool_calling
data: {"tool": "kubectl_get_pods"}

event: tool_calling_result
data: {"tool": "kubectl_get_pods", "status": "success", "result": "..."}

event: ai_message
data: {"content": "I found several issues..."}

event: ai_answer_end
data: {"analysis": "...", "sections": {...}}
```

### POST /api/issue_chat

Discuss specific issues with context.

**Request:**

```bash
curl -X POST http://localhost:8080/api/issue_chat \
  -H "Content-Type: application/json" \
  -d '{
    "ask": "what are the next steps?",
    "model": "sonnet",
    "issue_context": {
      "previous_analysis": "Memory limit issue identified...",
      "alert_name": "KubePodCrashLooping"
    },
    "conversation_history": [...]
  }'
```

### POST /api/workload_health_check

Kubernetes workload health analysis.

**Request:**

```bash
curl -X POST http://localhost:8080/api/workload_health_check \
  -H "Content-Type: application/json" \
  -d '{
    "workload_name": "api-gateway",
    "workload_type": "Deployment",
    "namespace": "production",
    "model": "sonnet",
    "include_alert_history": true
  }'
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workload_name` | string | Yes | Workload name |
| `workload_type` | string | Yes | Deployment, StatefulSet, DaemonSet |
| `namespace` | string | Yes | Kubernetes namespace |
| `model` | string | Yes | Model name |
| `include_alert_history` | boolean | No | Include past alerts |

### POST /api/workload_health_chat

Conversational workload health discussion.

**Request:**

```bash
curl -X POST http://localhost:8080/api/workload_health_chat \
  -H "Content-Type: application/json" \
  -d '{
    "ask": "why is memory usage increasing?",
    "workload_name": "api-gateway",
    "namespace": "production",
    "model": "sonnet",
    "conversation_history": [...]
  }'
```

## Response Structure

### Standard Response

```json
{
  "analysis": "Full text analysis...",
  "sections": {
    "alert_explanation": "Explanation of the alert/issue",
    "key_findings": "Important discoveries",
    "root_causes": "Identified root causes",
    "next_steps": "Recommended actions"
  },
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "tool_calls": [
    {
      "tool": "tool_name",
      "parameters": {"param": "value"},
      "result": "output",
      "status": "success"
    }
  ],
  "metadata": {
    "token_count": 1500,
    "context_window_used": 0.3,
    "truncated": false,
    "model": "sonnet"
  }
}
```

### Error Response

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "additional info"
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `invalid_model` | Model not found in modelList |
| `api_key_missing` | AI provider API key not configured |
| `rate_limited` | AI provider rate limit exceeded |
| `timeout` | Request timed out |
| `invalid_request` | Malformed request body |
| `internal_error` | Server-side error |

## Authentication

By default, the API has no authentication. For production, add authentication via:

### Kubernetes NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: holmesgpt-api
  namespace: holmesgpt
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: holmes
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: allowed-namespace
```

### Ingress with Authentication

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: holmesgpt
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: holmesgpt-auth
spec:
  rules:
    - host: holmesgpt.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: holmesgpt-holmes
                port:
                  number: 80
```

## Rate Limiting

### AI Provider Rate Limits

HolmesGPT API responses are subject to the rate limits of the underlying AI provider.
When limits are exceeded, the API returns a `rate_limited` error:

```json
{
  "error": "rate_limited",
  "message": "AI provider rate limit exceeded. Retry after 60 seconds.",
  "details": {
    "provider": "anthropic",
    "retry_after_seconds": 60
  }
}
```

### Client-Side Rate Limiting

For production deployments, implement client-side rate limiting:

**Python Example:**

```python
import time
from functools import wraps

def rate_limit(max_calls: int, period: int):
    """Decorator to rate limit API calls."""
    calls = []
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove old calls outside the period
            calls[:] = [c for c in calls if now - c < period]
            if len(calls) >= max_calls:
                sleep_time = period - (now - calls[0])
                time.sleep(sleep_time)
            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=10, period=60)  # 10 calls per minute
def ask_holmes(question: str) -> dict:
    # API call implementation
    pass
```

### Kubernetes-Level Rate Limiting

Use Ingress annotations for cluster-level rate limiting:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: holmesgpt
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "10"
    nginx.ingress.kubernetes.io/limit-connections: "5"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "2"
```

### Recommended Limits by Use Case

| Use Case | Recommended Limit | Rationale |
|----------|-------------------|-----------|
| Interactive CLI | 10 req/min | Human typing speed |
| Alert investigation | 30 req/min | Batch alert processing |
| CI/CD integration | 5 req/min | Deployment frequency |
| Dashboard/monitoring | 2 req/min | Periodic health checks |

## Usage Examples

### Python Client

```python
import requests

HOLMES_URL = "http://localhost:8080"

def ask_holmes(question: str, model: str = "sonnet") -> dict:
    response = requests.post(
        f"{HOLMES_URL}/api/chat",
        json={
            "ask": question,
            "model": model,
            "include_tool_calls": True
        }
    )
    response.raise_for_status()
    return response.json()

def investigate_alert(alert_name: str, labels: dict) -> dict:
    response = requests.post(
        f"{HOLMES_URL}/api/investigate",
        json={
            "alert_name": alert_name,
            "alert_labels": labels,
            "model": "sonnet"
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
result = ask_holmes("what pods are crashing?")
print(result["analysis"])
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

const HOLMES_URL = 'http://localhost:8080';

async function askHolmes(question, model = 'sonnet') {
  const response = await axios.post(`${HOLMES_URL}/api/chat`, {
    ask: question,
    model: model,
    include_tool_calls: true
  });
  return response.data;
}

async function streamInvestigation(alertName) {
  const response = await fetch(`${HOLMES_URL}/api/stream/investigate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({
      alert_name: alertName,
      model: 'sonnet'
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    console.log(decoder.decode(value));
  }
}

// Usage
askHolmes('check cluster health').then(console.log);
```

### Curl Examples

```bash
# Basic chat
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"ask": "list unhealthy pods", "model": "sonnet"}'

# With conversation history
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "ask": "tell me more about the first one",
    "model": "sonnet",
    "conversation_history": [
      {"role": "user", "content": "list unhealthy pods"},
      {"role": "assistant", "content": "Found 3 unhealthy pods..."}
    ]
  }'

# Workload health check
curl -X POST http://localhost:8080/api/workload_health_check \
  -H "Content-Type: application/json" \
  -d '{
    "workload_name": "nginx",
    "workload_type": "Deployment",
    "namespace": "default",
    "model": "sonnet"
  }'
```
