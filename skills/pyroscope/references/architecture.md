# Pyroscope Architecture Reference

Complete reference for Grafana Pyroscope architecture, deployment modes, and scaling.

## Deployment Modes

### Monolithic Mode

**Flag:** `-target=all` (default)

All components run in a single process. Simplest configuration for getting started.

```text
┌─────────────────────────────────────────────┐
│              Pyroscope (Single Process)     │
│                                             │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │Distributor│ │ Ingester │ │   Querier   │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │Compactor │ │Store-GW  │ │Query-Frontend│ │
│  └──────────┘ └──────────┘ └─────────────┘ │
└─────────────────────────────────────────────┘
```

**Use Cases:**

- Development and testing
- Small-scale deployments (~20GB profiles/day)
- Quick experimentation

**Limitations:**

- No horizontal scaling
- Multiple instances don't share data
- Not suitable for production at scale

**Query URL:** `http://pyroscope:4040/`

### Microservices Mode

**Flag:** `-target=[component_name]`

Each component runs as a separate process, enabling horizontal scaling and
fault isolation.

```text
                    ┌───────────────┐
                    │  SDK / Alloy  │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  Distributor  │  (Stateless)
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │   Ingesters   │  (Stateful - 3+ replicas)
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
      ┌───────▼───────┐     │     ┌───────▼───────┐
      │   Compactor   │     │     │ Store-Gateway │
      └───────────────┘     │     └───────────────┘
                            │
                    ┌───────▼───────┐
                    │Object Storage │
                    │(S3/GCS/Azure) │
                    └───────────────┘

Query Path:
┌─────────────┐   ┌────────────────┐   ┌─────────────┐
│Query-Frontend│──▶│Query-Scheduler │──▶│   Querier   │
└─────────────┘   └────────────────┘   └─────────────┘
```

**Use Cases:**

- Production environments
- High-scale deployments
- Multi-tenant systems
- Independent component scaling

**Query URL:** `http://pyroscope-querier:4040/`

## Core Components

### Distributor (Stateless)

**Purpose:** Entry point for profile ingestion. Routes profiles to ingesters.

**Responsibilities:**

1. **Data Validation** - Validates incoming profiles
2. **Series Sharding** - Distributes series across ingesters using consistent hashing
3. **Replication** - Replicates each series to multiple ingesters

**Replication Model:**

- Dynamo-style quorum consistency
- Default replication factor: 3
- Write success requires n/2 + 1 confirmations (2 of 3)

**Configuration:**

```yaml
distributor:
  push_timeout: 5s
  ingestion_tenant_shard_size: 4  # Shuffle sharding
  ring:
    kvstore: memberlist
    heartbeat_timeout: 5m
```

**Scaling:** Horizontally scalable, stateless

### Ingester (Stateful)

**Purpose:** Receives and temporarily stores profiles before writing to
long-term storage.

**Responsibilities:**

1. **Profile Reception** - Receives profiles from distributors
2. **In-Memory Buffering** - Stores recent data in memory
3. **Batch Compression** - Compresses and batches samples
4. **Storage Upload** - Writes blocks to object storage

**Ring States:**

| State | Description |
|-------|-------------|
| PENDING | Starting up |
| JOINING | Initializing |
| ACTIVE | Operational |
| LEAVING | Shutting down |
| UNHEALTHY | Failed heartbeat |

**Configuration:**

```yaml
ingester:
  num_tokens: 128
  heartbeat_interval: 5s
  heartbeat_timeout: 10s
  lifecycle:
    num_flush_instances: 3
    claim_on_rollout: true
    ring_timeout: 5m
```

**Data Safety:**

- Each profile replicates to 3 ingesters by default
- Single ingester failure causes no data loss
- Write-ahead log for crash recovery

**Scaling:** Stateful, minimum 3 replicas for production

### Querier (Stateless)

**Purpose:** Handles query execution on the read path.

**Responsibilities:**

1. **Query Evaluation** - Executes profile queries
2. **Data Fetching** - Retrieves from ingesters (recent) and store-gateways (historical)
3. **Result Aggregation** - Merges results from multiple sources

**Data Sources:**

- **Ingesters** - Recent profile data (not yet flushed)
- **Store-Gateways** - Historical data from object storage

**Configuration:**

```yaml
querier:
  query_store_after: 4h
  query_ingesters_within: 1h
  shuffle_sharding_ingesters_enabled: true
  max_query_lookback: 30d
```

**Scaling:** Horizontally scalable, stateless

### Query Frontend (Stateless)

**Purpose:** API gateway for the read path. Optimizes query execution.

**Responsibilities:**

1. **Query Reception** - Receives incoming queries
2. **Queue Management** - Enqueues queries via query-scheduler
3. **Result Aggregation** - Collects and returns results

**Benefits:**

- Fair scheduling across tenants
- Query splitting and caching
- Horizontal scaling of query capacity

**Configuration:**

```yaml
query_frontend:
  max_outstanding_per_tenant: 200
  querier_forget_delay: 15m
```

**Scaling:** Horizontally scalable, minimum 2 replicas for HA

### Query Scheduler (Stateless)

**Purpose:** Manages query queue and distributes work to queriers.

**Flow:**

1. Query-frontend receives and processes queries
2. Query-frontend enqueues to query-scheduler
3. Query-scheduler maintains in-memory queue
4. Queriers pull and execute queries
5. Results route back through query-frontend

**Configuration:**

```yaml
query_scheduler:
  max_outstanding_requests_per_tenant: 2048
```

**Scaling:** Minimum 2 replicas for HA

### Compactor (Stateless)

**Purpose:** Optimizes storage by merging blocks and managing retention.

**Responsibilities:**

1. **Block Compaction** - Merges small blocks into larger ones
2. **De-duplication** - Removes duplicate data from replication
3. **Retention Enforcement** - Deletes expired data
4. **Bucket Index** - Maintains per-tenant block index

**Compaction Process:**

**Stage 1 - Vertical Compaction:**

- Merges blocks from same time range
- Eliminates duplicates from replication

**Stage 2 - Horizontal Compaction:**

- Combines adjacent time ranges
- Reduces index size significantly

**Configuration:**

```yaml
compactor:
  data_dir: ./data
  block_ranges:
    - 1h
    - 2h
    - 8h
  compaction_interval: 30m
  compaction_concurrency: 4
  deletion_delay: 12h
```

**Disk Requirements:**

```text
Minimum disk = compaction_concurrency × max_block_size × 2
```

**Scaling:** Stateless, shuffle sharding for horizontal scaling

### Store Gateway (Distributed)

**Purpose:** Provides access to long-term storage for historical queries.

**Responsibilities:**

1. **Block Management** - Each instance manages subset of blocks
2. **Query Serving** - Retrieves profile data from object storage
3. **Caching** - Caches frequently accessed blocks

**Configuration:**

```yaml
store_gateway:
  sharding_ring:
    enabled: true
    kvstore: memberlist
  sync_interval: 15m
  ignore_blocks_within: 3h
```

**Scaling:** Distributed block assignment enables horizontal scaling

## Data Structures

### Block Format

Each block contains profiling data for a single tenant:

```text
<block-ulid>/
├── meta.json      # Block metadata (time range, etc.)
├── index.tsdb     # TSDB index (labels → profiles)
├── profiles.parquet  # Profile data (Parquet format)
└── symbols.symdb  # Symbol information for profiles
```

**Characteristics:**

- Unique ULID identifier
- Single-tenant isolation
- Google pprof protocol compatible
- Label-based organization

### Bucket Index

Per-tenant file listing all blocks:

```json
{
  "blocks": [...],
  "block_deletion_marks": [...],
  "updated_at": 1234567890
}
```

**Benefits:**

- Eliminates costly "list objects" API calls
- Store-gateways consult index directly
- Updated by compactor periodically

## Hash Rings

Used for consistent data distribution:

**Memberlist Configuration:**

```yaml
memberlist:
  bind_addr: 0.0.0.0
  bind_port: 7946
  join:
    - dnssrv+pyroscope-memberlist._tcp.pyroscope.svc.cluster.local
  gossip_interval: 1s
  gossip_nodes: 3
  retransmit_factor: 4
```

**Ring Types:**

- **Ingester Ring** - Distributes profiles across ingesters
- **Store-Gateway Ring** - Assigns blocks to store-gateways
- **Compactor Ring** - Coordinates compaction work

## Shuffle Sharding

Limits which components handle specific tenants:

```yaml
# Ingesters per tenant
distributor:
  ingestion_tenant_shard_size: 4

# Queriers per tenant
query_frontend:
  max_queriers_per_tenant: 2

# Store-gateways per tenant
store_gateway:
  tenant_shard_size: 3

# Compactors per tenant
compactor:
  compactor_tenant_shard_size: 1
```

**Benefits:**

- Failure isolation between tenants
- Resource fairness
- Reduced blast radius

## Scaling Guidelines

### Horizontal Scaling

| Component | Scaling Approach | Trigger |
|-----------|-----------------|---------|
| Distributor | Add replicas | High ingestion rate |
| Ingester | Add replicas | Memory pressure, ingestion lag |
| Querier | Add replicas | Query latency, queue depth |
| Query Frontend | Add replicas | Request rate |
| Store Gateway | Add replicas | Query latency on historical data |
| Compactor | Increase concurrency | Compaction backlog |

### Vertical Scaling

| Component | Key Resource | Tuning |
|-----------|--------------|--------|
| Ingester | Memory | Increase for higher cardinality |
| Compactor | CPU, Disk | More concurrency = more CPU |
| Store Gateway | Memory | Cache size for query performance |

### Production Replica Counts

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Distributor | 2 | 3 |
| Ingester | 3 | 5 |
| Querier | 2 | 3-5 |
| Query Frontend | 2 | 2 |
| Query Scheduler | 2 | 2 |
| Compactor | 1 | 3 |
| Store Gateway | 2 | 3 |

## Data Flow Details

### Write Path

```text
1. SDK/Alloy pushes profile to Distributor
2. Distributor validates and hashes profile labels
3. Distributor identifies target ingesters via hash ring
4. Profile replicated to N ingesters (default: 3)
5. Ingester buffers profile in memory
6. After block duration, ingester flushes to object storage
7. Compactor merges and optimizes blocks
```

### Read Path

```text
1. Query arrives at Query Frontend
2. Query Frontend enqueues to Query Scheduler
3. Querier pulls query from scheduler
4. Querier determines time range:
   - Recent: Query ingesters
   - Historical: Query store-gateways
5. Store-gateways fetch blocks from object storage
6. Results aggregated and returned via Query Frontend
```

## Consistency Model

**Write Consistency:**

- Quorum-based (n/2 + 1 replicas)
- Default: 2 of 3 ingesters must confirm

**Read Consistency:**

- Eventual consistency for recent data
- Strong consistency for flushed data

**Data Durability:**

- 3-way replication prevents data loss
- WAL recovery for crash scenarios

## Deployment Decision Matrix

| Factor | Monolithic | Microservices |
|--------|-----------|--------------|
| Setup Complexity | Simple | Complex |
| Horizontal Scaling | Not viable | Excellent |
| Failure Isolation | None | Per-component |
| Resource Efficiency | Good (small) | Better (large) |
| Production Ready | Dev/test only | Fully |
| Kubernetes | Yes | Recommended |
| Data Sharing | Single instance | Multi-instance |
| Configuration | Minimal | Extensive |
