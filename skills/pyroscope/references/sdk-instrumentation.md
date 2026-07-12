# Pyroscope SDK Instrumentation Reference

Complete guide for instrumenting applications with Pyroscope SDKs and Grafana Alloy.

## Client Configuration Methods

### Method 1: SDK Instrumentation (Push Mode)

Applications directly push profiles to Pyroscope server.

```text
Application with SDK → Pyroscope Server (port 4040)
```

### Method 2: Grafana Alloy (Pull Mode)

Alloy scrapes pprof endpoints from applications.

```text
Application ← Grafana Alloy (collector) → Pyroscope Server
```

### Method 3: Hybrid Mode

SDKs send to local Alloy, which forwards to Pyroscope.

```text
Application with SDK → Alloy → Pyroscope Server
```

## Profile Types

| Type | Description | Languages |
|------|-------------|-----------|
| `cpu` | Wall/CPU time | All |
| `alloc_objects` | Allocation count | Go, Java, .NET |
| `alloc_space` | Allocation bytes | Go, Java, .NET |
| `inuse_objects` | Heap objects | Go, Java, .NET |
| `inuse_space` | Heap bytes | Go, Java, .NET |
| `goroutines` | Goroutine count | Go |
| `mutex_count` | Lock acquisitions | Go, Java, .NET |
| `mutex_duration` | Lock wait time | Go, Java, .NET |
| `block_count` | Block events | Go |
| `block_duration` | Block wait time | Go |
| `exceptions` | Exception tracking | Python |

## Language SDKs

### Go SDK

**Installation:**

```bash
go get github.com/grafana/pyroscope-go
```

**Basic Usage:**

```go
package main

import (
    "github.com/grafana/pyroscope-go"
)

func main() {
    // Start profiling
    pyroscope.Start(pyroscope.Config{
        ApplicationName: "my-app",
        ServerAddress:   "http://pyroscope:4040",
        Logger:          pyroscope.StandardLogger,

        // Tags for filtering
        Tags: map[string]string{
            "env":     "production",
            "version": "1.0.0",
        },

        // Profile types to collect
        ProfileTypes: []pyroscope.ProfileType{
            pyroscope.ProfileCPU,
            pyroscope.ProfileAllocObjects,
            pyroscope.ProfileAllocSpace,
            pyroscope.ProfileInuseObjects,
            pyroscope.ProfileInuseSpace,
            pyroscope.ProfileGoroutines,
            pyroscope.ProfileMutexCount,
            pyroscope.ProfileMutexDuration,
            pyroscope.ProfileBlockCount,
            pyroscope.ProfileBlockDuration,
        },
    })
    defer pyroscope.Stop()

    // Application code
}
```

**With Basic Authentication:**

```go
pyroscope.Start(pyroscope.Config{
    ApplicationName: "my-app",
    ServerAddress:   "http://pyroscope:4040",
    BasicAuthUser:   "user",
    BasicAuthPassword: "password",
})
```

**With Tenant ID (Multi-tenant):**

```go
pyroscope.Start(pyroscope.Config{
    ApplicationName: "my-app",
    ServerAddress:   "http://pyroscope:4040",
    TenantID:        "my-tenant",
})
```

**Dynamic Tags:**

```go
// Add dynamic tags for specific code sections
pyroscope.TagWrapper(context.Background(), pyroscope.Labels(
    "controller", "OrderController",
    "method", "CreateOrder",
), func(ctx context.Context) {
    // Profiled code with these tags
    processOrder(ctx)
})
```

**OpenTelemetry Integration (Span Profiles):**

```go
import (
    "github.com/grafana/pyroscope-go"
    otelpyroscope "github.com/grafana/otel-profiling-go"
    "go.opentelemetry.io/otel/sdk/trace"
)

// Configure tracer with span profiling
tp := trace.NewTracerProvider(
    trace.WithSpanProcessor(otelpyroscope.NewSpanProcessor()),
    // ... other options
)
```

### Java SDK

**Maven Dependency:**

```xml
<dependency>
    <groupId>io.pyroscope</groupId>
    <artifactId>agent</artifactId>
    <version>0.12.0</version>
</dependency>
```

**Gradle:**

```groovy
implementation 'io.pyroscope:agent:0.12.0'
```

**Programmatic Configuration:**

```java
import io.pyroscope.javaagent.PyroscopeAgent;
import io.pyroscope.javaagent.config.Config;
import io.pyroscope.javaagent.EventType;
import io.pyroscope.http.Format;

public class Application {
    public static void main(String[] args) {
        PyroscopeAgent.start(
            new Config.Builder()
                .setApplicationName("my-java-app")
                .setServerAddress("http://pyroscope:4040")
                .setProfilingEvent(EventType.ITIMER)  // CPU profiling
                .setProfilingAlloc("512k")            // Memory profiling
                .setProfilingLock("10ms")             // Lock profiling
                .setFormat(Format.JFR)
                .setLabels(Map.of(
                    "env", "production",
                    "version", "1.0.0"
                ))
                .build()
        );

        // Application code
    }
}
```

**Java Agent (JVM Argument):**

```bash
java -javaagent:pyroscope.jar \
  -Dpyroscope.application.name=my-app \
  -Dpyroscope.server.address=http://pyroscope:4040 \
  -Dpyroscope.profiling.event=itimer \
  -Dpyroscope.profiling.alloc=512k \
  -Dpyroscope.profiling.lock=10ms \
  -jar myapp.jar
```

**Spring Boot Integration:**

```yaml
# application.yml
pyroscope:
  application-name: my-spring-app
  server-address: http://pyroscope:4040
  profiling-event: itimer
  labels:
    env: ${ENVIRONMENT:development}
```

**Dynamic Labels:**

```java
import io.pyroscope.javaagent.api.Pyroscope;

public void processRequest(String userId) {
    Pyroscope.LabelsWrapper.run(
        new LabelsSet("user_id", userId),
        () -> {
            // Code profiled with user_id label
            doWork();
        }
    );
}
```

### Python SDK

**Installation:**

```bash
pip install pyroscope-io
```

**Basic Usage:**

```python
import pyroscope

pyroscope.configure(
    application_name="my-python-app",
    server_address="http://pyroscope:4040",
    tags={
        "env": "production",
        "version": "1.0.0",
    },
)

# Application code
```

**With Authentication:**

```python
pyroscope.configure(
    application_name="my-python-app",
    server_address="http://pyroscope:4040",
    basic_auth_username="user",
    basic_auth_password="password",
)
```

**Multi-tenant:**

```python
pyroscope.configure(
    application_name="my-python-app",
    server_address="http://pyroscope:4040",
    tenant_id="my-tenant",
)
```

**Django Integration:**

```python
# settings.py
import pyroscope

pyroscope.configure(
    application_name="my-django-app",
    server_address="http://pyroscope:4040",
    tags={
        "env": os.environ.get("ENVIRONMENT", "development"),
    },
)
```

**Flask Integration:**

```python
from flask import Flask
import pyroscope

app = Flask(__name__)

pyroscope.configure(
    application_name="my-flask-app",
    server_address="http://pyroscope:4040",
)

@app.route("/")
def index():
    return "Hello World"
```

**Dynamic Tags:**

```python
with pyroscope.tag_wrapper({"endpoint": "/api/users", "method": "GET"}):
    # Code profiled with these tags
    process_request()
```

### .NET SDK

**NuGet Package:**

```bash
dotnet add package Pyroscope
```

**Basic Usage:**

```csharp
using Pyroscope;

public class Program
{
    public static void Main(string[] args)
    {
        Pyroscope.Profiler.Instance.Configure(new Configuration
        {
            ApplicationName = "my-dotnet-app",
            ServerAddress = "http://pyroscope:4040",
            Labels = new Dictionary<string, string>
            {
                {"env", "production"},
                {"version", "1.0.0"}
            }
        });

        Pyroscope.Profiler.Instance.Start();

        // Application code

        Pyroscope.Profiler.Instance.Stop();
    }
}
```

**ASP.NET Core Integration:**

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

// Configure Pyroscope
Pyroscope.Profiler.Instance.Configure(new Configuration
{
    ApplicationName = "my-aspnet-app",
    ServerAddress = "http://pyroscope:4040",
});
Pyroscope.Profiler.Instance.Start();

var app = builder.Build();
// ... rest of app
```

### Ruby SDK

**Gemfile:**

```ruby
gem 'pyroscope'
```

**Basic Usage:**

```ruby
require 'pyroscope'

Pyroscope.configure do |config|
  config.application_name = 'my-ruby-app'
  config.server_address = 'http://pyroscope:4040'
  config.tags = {
    env: 'production',
    version: '1.0.0'
  }
end

# Application code
```

**Rails Integration:**

```ruby
# config/initializers/pyroscope.rb
Pyroscope.configure do |config|
  config.application_name = 'my-rails-app'
  config.server_address = ENV.fetch('PYROSCOPE_SERVER', 'http://pyroscope:4040')
  config.tags = {
    env: Rails.env,
    version: ENV.fetch('APP_VERSION', 'unknown')
  }
end
```

### Node.js SDK

**Installation:**

```bash
npm install @pyroscope/nodejs
```

**Basic Usage:**

```javascript
const Pyroscope = require('@pyroscope/nodejs');

Pyroscope.init({
  serverAddress: 'http://pyroscope:4040',
  appName: 'my-nodejs-app',
  tags: {
    env: 'production',
    version: '1.0.0'
  }
});

Pyroscope.start();

// Application code
```

**Express Integration:**

```javascript
const express = require('express');
const Pyroscope = require('@pyroscope/nodejs');

Pyroscope.init({
  serverAddress: 'http://pyroscope:4040',
  appName: 'my-express-app',
});
Pyroscope.start();

const app = express();

app.get('/', (req, res) => {
  res.send('Hello World');
});

app.listen(3000);
```

### Rust SDK

**Cargo.toml:**

```toml
[dependencies]
pyroscope = "0.5"
pyroscope_pprofrs = "0.2"
```

**Basic Usage:**

```rust
use pyroscope::PyroscopeAgent;
use pyroscope_pprofrs::{pprof_backend, PprofConfig};

fn main() {
    let agent = PyroscopeAgent::builder(
        "http://pyroscope:4040",
        "my-rust-app"
    )
    .backend(pprof_backend(PprofConfig::new().sample_rate(100)))
    .tags([("env", "production")].to_vec())
    .build()
    .unwrap();

    agent.start();

    // Application code

    agent.stop();
}
```

## Grafana Alloy Configuration

### eBPF Profiling (Linux)

For compiled languages without code modification:

```river
// discovery.kubernetes.pods for target discovery
discovery.kubernetes "pods" {
  role = "pod"
}

// eBPF profiler
pyroscope.ebpf "default" {
  forward_to = [pyroscope.write.default.receiver]

  targets = discovery.kubernetes.pods.targets

  demangle = "none"
}

// Write to Pyroscope
pyroscope.write "default" {
  endpoint {
    url = "http://pyroscope:4040"
  }
}
```

**Supported Languages (eBPF):**

- Go (with frame pointers)
- C/C++ (with frame pointers)
- Rust (with frame pointers)
- Python (with `python_enabled=true`)

### Pull Mode (pprof Scraping)

For Go applications with pprof endpoints:

```river
// Scrape pprof endpoints
pyroscope.scrape "default" {
  targets = [
    {"__address__" = "my-app:6060", "service_name" = "my-app"},
  ]

  forward_to = [pyroscope.write.default.receiver]

  profiling_config {
    profile.process_cpu {
      enabled = true
    }
    profile.memory {
      enabled = true
      path = "/debug/pprof/allocs"
    }
    profile.goroutine {
      enabled = true
    }
    profile.mutex {
      enabled = true
    }
    profile.block {
      enabled = true
    }
  }
}

pyroscope.write "default" {
  endpoint {
    url = "http://pyroscope:4040"
  }
}
```

### Java Pull Mode

```river
pyroscope.java "default" {
  forward_to = [pyroscope.write.default.receiver]

  targets = discovery.kubernetes.pods.targets
}
```

### Kubernetes Discovery with Annotations

```river
// Discover pods with profile annotations
discovery.kubernetes "pods" {
  role = "pod"
}

// Relabel for annotation-based scraping
discovery.relabel "pods" {
  targets = discovery.kubernetes.pods.targets

  rule {
    source_labels = ["__meta_kubernetes_pod_annotation_profiles_grafana_com_cpu_scrape"]
    action = "keep"
    regex = "true"
  }

  rule {
    source_labels = ["__meta_kubernetes_pod_annotation_profiles_grafana_com_cpu_port"]
    target_label = "__address__"
    regex = "(\\d+)"
    replacement = "${1}"
  }
}

pyroscope.scrape "kubernetes" {
  targets = discovery.relabel.pods.output
  forward_to = [pyroscope.write.default.receiver]
}
```

## Kubernetes Pod Annotations

Enable profile scraping with annotations:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        # CPU profiling
        profiles.grafana.com/cpu.scrape: "true"
        profiles.grafana.com/cpu.port: "8080"
        profiles.grafana.com/cpu.path: "/debug/pprof/profile"

        # Memory profiling
        profiles.grafana.com/memory.scrape: "true"
        profiles.grafana.com/memory.port: "8080"
        profiles.grafana.com/memory.path: "/debug/pprof/allocs"

        # Goroutine profiling
        profiles.grafana.com/goroutine.scrape: "true"
        profiles.grafana.com/goroutine.port: "8080"

        # Block profiling
        profiles.grafana.com/block.scrape: "true"
        profiles.grafana.com/block.port: "8080"

        # Mutex profiling
        profiles.grafana.com/mutex.scrape: "true"
        profiles.grafana.com/mutex.port: "8080"
```

**Annotation Parameters:**

| Annotation | Description | Default |
|------------|-------------|---------|
| `<type>.scrape` | Enable scraping | false |
| `<type>.port` | Port number | Auto-detect |
| `<type>.port_name` | Named port | http2 |
| `<type>.scheme` | HTTP/HTTPS | http |
| `<type>.path` | Endpoint path | Go default |

## Trace-to-Profile Linking

### Requirements

- Minimum span duration: 20ms
- CPU profile type only
- Supported: Go, Java, .NET, Python, Ruby

### Go + OpenTelemetry

```go
import (
    "github.com/grafana/pyroscope-go"
    otelpyroscope "github.com/grafana/otel-profiling-go"
    "go.opentelemetry.io/otel/sdk/trace"
)

func main() {
    // Start Pyroscope
    pyroscope.Start(pyroscope.Config{
        ApplicationName: "my-app",
        ServerAddress:   "http://pyroscope:4040",
    })

    // Configure tracer with span profiling
    tp := trace.NewTracerProvider(
        trace.WithSpanProcessor(otelpyroscope.NewSpanProcessor()),
    )
    otel.SetTracerProvider(tp)
}
```

### Java + OpenTelemetry

```java
// Use async-profiler event type for span profiles
PyroscopeAgent.start(
    new Config.Builder()
        .setApplicationName("my-java-app")
        .setServerAddress("http://pyroscope:4040")
        .setProfilingEvent(EventType.ITIMER)
        .build()
);

// OpenTelemetry SDK will automatically correlate
```

### Python + OpenTelemetry

```python
import pyroscope
from opentelemetry import trace

pyroscope.configure(
    application_name="my-python-app",
    server_address="http://pyroscope:4040",
)

# Traces will be automatically correlated with profiles
```

## AWS Lambda Extension

### Configuration

```yaml
# Environment variables
PYROSCOPE_SERVER_ADDRESS: "http://pyroscope:4040"
PYROSCOPE_APPLICATION_NAME: "my-lambda"
PYROSCOPE_TAGS: "env=production,region=us-east-1"
```

### Lambda Layer

```yaml
# serverless.yml
functions:
  myFunction:
    handler: handler.main
    layers:
      - arn:aws:lambda:us-east-1:123456789012:layer:pyroscope:1
    environment:
      PYROSCOPE_SERVER_ADDRESS: http://pyroscope:4040
      PYROSCOPE_APPLICATION_NAME: my-lambda
```

## Best Practices

### Naming Conventions

```text
# Application name format
{service-name}.{component}

# Examples
api-gateway.http
order-service.worker
payment-service.processor
```

### Tag Strategy

```go
// Recommended tags
Tags: map[string]string{
    "env":        "production",      // Environment
    "version":    "1.2.3",           // App version
    "region":     "us-east-1",       // Deployment region
    "instance":   os.Getenv("POD_NAME"), // Instance ID
}
```

### Resource Overhead

- CPU overhead: ~2-5%
- Memory overhead: ~50MB per pod
- Network: Profiles sent every 15 seconds
- Crash safety: Never crashes app if backend unavailable

### Sampling Configuration

```go
// Reduce overhead with sampling
pyroscope.Start(pyroscope.Config{
    ApplicationName: "my-app",
    ServerAddress:   "http://pyroscope:4040",
    // Default: 100Hz sampling rate
})
```

## Language Support Matrix

| Feature | Go | Java | Python | .NET | Ruby | Node.js | Rust |
|---------|----|----|--------|------|------|---------|------|
| CPU Profiling | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Memory Profiling | ✓ | ✓ | - | ✓ | - | - | - |
| Goroutine/Thread | ✓ | ✓ | - | ✓ | ✓ | - | - |
| Mutex/Lock | ✓ | ✓ | - | ✓ | - | - | - |
| Block Profiling | ✓ | - | - | - | - | - | - |
| Exceptions | - | - | ✓ | - | - | - | - |
| Span Profiles | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| eBPF Support | ✓ | - | ✓ | - | - | - | ✓ |
