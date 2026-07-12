---
name: python-infrastructure
description: Python patterns for system reliability — background jobs and task queues (Celery, async), resilience and recovery (retries, backoff, timeouts, circuit breakers via tenacity), and observability (structured logging via structlog, metrics, distributed tracing, golden signals). USE WHEN building async workers, queueing tasks, handling transient network/IO failures, instrumenting Python services for production, designing retry policies, configuring logging or tracing, or any combination of these system-reliability concerns. NOT FOR language idioms or type hygiene (use `writing-python`) or project setup and dependency management (use `uv`).
---

# Python Infrastructure

System-reliability concerns for Python services, grouped because real code uses them together: a task you queue (background-jobs) needs retries (resilience) and instrumentation (observability) on the same call path.

## Scope routing

| If you need to… | Read |
|---|---|
| Design a task queue, schedule recurring jobs, or run async workers (Celery, RQ, asyncio task pools) | `References/background-jobs.md` |
| Decide what to retry, with what backoff, and when to stop (tenacity patterns, idempotency, circuit breakers) | `References/resilience.md` |
| Instrument a service with structured logs, metrics, and traces (structlog, OpenTelemetry, the four golden signals) | `References/observability.md` |

## Decision tree

```
Operation can fail transiently (network/IO/3rd-party API)?
  -> resilience.md (retry policy)
Operation runs out-of-request (email, image processing, batch)?
  -> background-jobs.md (queue + worker)
Need to know what's happening in production?
  -> observability.md (logs/metrics/traces)
All three at once for one feature?
  -> all three references, in that order.
```

## Cross-skill boundaries

- **`writing-python`** — *how* to write the function. This skill — *how it survives in production*.
- **`python-error-handling`** — *what exception to raise*. This skill — *what to do when it's raised across a network boundary*.
- **`python-resource-management`** — *how to clean up resources* (context managers). This skill — *how to keep retrying when resources fail to acquire*.

## Gotchas

- **Retry without backoff is a DoS amplifier.** A failed downstream + immediate retry from N clients = traffic burst that keeps the downstream down. Default to exponential backoff + jitter from day one.
- **Retrying non-idempotent operations duplicates side effects.** A failed POST + retry can mean two charges. Always pair retry-on-failure with an idempotency key OR mark the operation non-retryable.
- **Synchronous code inside an async worker blocks the event loop.** A "fast" `requests` call in an asyncio worker kills throughput. Use the async client (`httpx`, `aiohttp`) or run sync code in an executor.
- **Structured logs and metrics serve different audiences.** Logs answer "what happened to this one request"; metrics answer "what's happening across all requests". Don't try to derive one from the other — instrument both.
- **Trace context propagation needs explicit plumbing across the queue boundary.** Pushing a task to Celery loses the current trace unless you serialize the trace context into the task headers and restore it in the worker. Read the OpenTelemetry-Celery propagator docs before assuming it "just works".
