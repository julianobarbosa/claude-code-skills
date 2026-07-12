---
name: writing-go
description: Idiomatic Go 1.25+ development. Use when writing Go code, designing APIs, discussing Go patterns, or reviewing Go implementations. Emphasizes stdlib, concrete types, simple error handling, and minimal dependencies.
allowed-tools: Read, Bash, Grep, Glob
---

# Go Development (1.25+)

## Core Principles

- **Stdlib first**: External deps only when justified
- **Concrete types**: Define interfaces at consumer, return structs
- **Composition**: Over inheritance, always
- **Fail fast**: Clear errors with context
- **Simple**: The obvious solution is usually correct

## Quick Patterns

### Error Handling

```go
if err := doThing(); err != nil {
    return fmt.Errorf("do thing: %w", err)
}
```

### Struct with Options

```go
type Server struct {
    addr    string
    timeout time.Duration
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, timeout: 30 * time.Second}
    for _, opt := range opts {
        opt(s)
    }
    return s
}
```

### Table-Driven Tests

```go
tests := []struct {
    name    string
    input   string
    want    string
    wantErr bool
}{
    {"valid", "hello", "HELLO", false},
    {"empty", "", "", true},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        got, err := Process(tt.input)
        if tt.wantErr {
            require.Error(t, err)
            return
        }
        require.NoError(t, err)
        assert.Equal(t, tt.want, got)
    })
}
```

## Go 1.25 Features

- **testing/synctest**: Deterministic concurrent testing with simulated clock
- **encoding/json/v2**: Experimental, 3-10x faster (GOEXPERIMENT=jsonv2)
- **runtime/trace.FlightRecorder**: Production trace capture on-demand
- **Container-aware GOMAXPROCS**: Auto-detects cgroup limits
- **GreenTea GC**: Experimental, lower latency (GOEXPERIMENT=greenteagc)

## References

- [PATTERNS.md](PATTERNS.md) - Detailed code patterns
- [TESTING.md](TESTING.md) - Testing strategies with testify/mockery
- [CLI.md](CLI.md) - CLI application patterns

## Tooling

```bash
go build ./...           # Build
go test -race ./...      # Test with race detector
golangci-lint run        # Lint
mockery --all            # Generate mocks
```

---

## Gotchas

- **`nil` channel sends/receives block forever; closed channel receives return zero value immediately** — `select` with a nil channel case disables that case, useful pattern but easy to do accidentally.
- **`defer` captures arguments at the call site, not at execution** — `defer fmt.Println(time.Now())` captures NOW, not the deferred time.
- **Pre-Go 1.22 for-loop variable capture closures over ONE variable across all iterations** — the goroutine-in-loop bug. Go 1.22 changed semantics; old habits create subtle bugs in mixed-version code.
- **`errors.Is` walks `Unwrap()` chains, BUT if a wrapped error implements `Is(target error) bool` itself, that custom Is wins over walking** — confusing when migrating from xerrors.
- **`sync.Pool` items can be GC'd between `Get` and the next `Put`** — never rely on a Pool to retain state.
