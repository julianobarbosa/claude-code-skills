# Azure Service Tables Reference

## Table of Contents
- [Log Analytics / Azure Monitor](#log-analytics--azure-monitor)
- [Microsoft Sentinel](#microsoft-sentinel)
- [Application Insights](#application-insights)
- [Azure Data Explorer (ADX)](#azure-data-explorer-adx)

---

## Log Analytics / Azure Monitor

### Infrastructure & Compute
| Table | Description |
|-------|-------------|
| `Heartbeat` | Agent health signals (1-min intervals) — use for VM inventory and connectivity |
| `Perf` | Performance counters (CPU, memory, disk, network) |
| `InsightsMetrics` | VM Insights metrics (newer format, replaces some Perf data) |
| `VMConnection` | Network connection data from VM Insights |
| `VMComputer` | VM inventory and configuration from VM Insights |
| `VMProcess` | Running processes from VM Insights |
| `Event` | Windows Event Log entries |
| `Syslog` | Linux syslog messages |
| `ConfigurationData` | Change Tracking — current state |
| `ConfigurationChange` | Change Tracking — changes detected |
| `Update` | Update Management — available updates |
| `UpdateSummary` | Update Management — compliance summary |

### Azure Platform
| Table | Description |
|-------|-------------|
| `AzureActivity` | Azure control plane operations (ARM) |
| `AzureDiagnostics` | Diagnostic logs from Azure resources (legacy) |
| `AzureMetrics` | Platform metrics |
| `AzureNetworkAnalytics_CL` | Network Watcher analytics |
| `AzureDevOpsAuditing` | Azure DevOps audit events |

### Containers
| Table | Description |
|-------|-------------|
| `ContainerInventory` | Container metadata |
| `ContainerLog` | Container stdout/stderr (legacy) |
| `ContainerLogV2` | Container logs (new schema) |
| `KubeEvents` | Kubernetes events |
| `KubeNodeInventory` | K8s node inventory |
| `KubePodInventory` | K8s pod inventory |
| `KubeServices` | K8s service inventory |
| `ContainerInsights` | Perf data from Container Insights |

### Networking
| Table | Description |
|-------|-------------|
| `AzureNetworkAnalytics_CL` | Traffic analytics |
| `W3CIISLog` | IIS web server logs |
| `CommonSecurityLog` | CEF-format logs (firewalls, proxies) |

### Custom & Agent
| Table | Description |
|-------|-------------|
| `CommonSecurityLog` | CEF (Common Event Format) data |
| `Syslog` | Syslog from Linux agents |
| `CustomLogs_CL` | Custom log collection (suffix _CL) |
| `LAQueryLogs` | Query audit log for the workspace |

---

## Microsoft Sentinel

Sentinel extends Log Analytics — all tables above are available, plus these security-specific tables:

### Identity & Access
| Table | Description |
|-------|-------------|
| `SigninLogs` | Azure AD interactive sign-ins |
| `AADNonInteractiveUserSignInLogs` | Non-interactive sign-ins |
| `AADServicePrincipalSignInLogs` | Service principal sign-ins |
| `AADManagedIdentitySignInLogs` | Managed identity sign-ins |
| `AADProvisioningLogs` | Provisioning events |
| `AuditLogs` | Azure AD audit trail |
| `IdentityInfo` | UEBA identity enrichment |
| `BehaviorAnalytics` | UEBA behavioral analysis |
| `IdentityDirectoryEvents` | Directory changes (MDE) |
| `IdentityLogonEvents` | Logon events (MDE) |
| `IdentityQueryEvents` | Query events (MDE — LDAP, DNS) |

### Security Events
| Table | Description |
|-------|-------------|
| `SecurityEvent` | Windows Security Event Log |
| `SecurityAlert` | Alerts from all providers |
| `SecurityIncident` | Sentinel incidents |
| `SecurityRecommendation` | Defender recommendations |
| `SecurityBaseline` | Baseline assessment |
| `SecurityBaselineSummary` | Baseline compliance summary |

### Threat Intelligence
| Table | Description |
|-------|-------------|
| `ThreatIntelligenceIndicator` | TI indicators (IOCs) |
| `HuntingBookmark` | Saved hunting bookmarks |
| `Watchlist` | Sentinel watchlists |

### Microsoft 365 Defender
| Table | Description |
|-------|-------------|
| `DeviceEvents` | Miscellaneous device events |
| `DeviceFileEvents` | File creation, modification, deletion |
| `DeviceImageLoadEvents` | DLL loading events |
| `DeviceInfo` | Device inventory |
| `DeviceLogonEvents` | Device logons |
| `DeviceNetworkEvents` | Network connections |
| `DeviceNetworkInfo` | Network configuration |
| `DeviceProcessEvents` | Process creation and related events |
| `DeviceRegistryEvents` | Registry modifications |
| `DeviceFileCertificateInfo` | Certificate info from file events |
| `EmailEvents` | Email delivery events |
| `EmailUrlInfo` | URLs in emails |
| `EmailAttachmentInfo` | Email attachment metadata |
| `CloudAppEvents` | Cloud application events (MCAS) |
| `AlertEvidence` | Evidence linked to alerts |

### Network Security
| Table | Description |
|-------|-------------|
| `AzureNetworkAnalytics_CL` | NSG flow logs |
| `DnsEvents` | DNS query logs |
| `CommonSecurityLog` | CEF-format (firewalls, WAF, proxies) |
| `AzureDiagnostics` | Azure Firewall logs (Category = AzureFirewallNetworkRule/ApplicationRule) |

---

## Application Insights

| Table | Description |
|-------|-------------|
| `requests` | Incoming HTTP requests |
| `dependencies` | Outbound calls (HTTP, SQL, etc.) |
| `exceptions` | Handled and unhandled exceptions |
| `traces` | Log traces (ILogger, TraceSource) |
| `customEvents` | Custom tracked events |
| `customMetrics` | Custom tracked metrics |
| `pageViews` | Browser page view telemetry |
| `browserTimings` | Client-side performance |
| `availabilityResults` | Availability/ping test results |
| `performanceCounters` | Server performance counters |

### Key Columns (common across App Insights tables)
- `timestamp` — event time (NOT `TimeGenerated`)
- `operation_Id` — request correlation ID
- `operation_ParentId` — parent operation
- `cloud_RoleName` — service/app name
- `cloud_RoleInstance` — instance identifier
- `client_IP` — client IP address
- `customDimensions` — dynamic bag of custom properties

---

## Azure Data Explorer (ADX)

ADX uses custom schemas — tables are defined per database. No predefined table names.

### System Tables (available in every ADX database)
| Table / Function | Description |
|-----------------|-------------|
| `.show tables` | List tables in database |
| `.show table T schema` | Table schema |
| `.show table T details` | Table details (size, extents) |
| `.show database datastats` | Database storage stats |
| `.show queries` | Running/recent queries |
| `.show journal` | Database journal (DDL history) |

### Common Patterns for ADX
- IoT/telemetry data often uses: `Timestamp`, `DeviceId`, `Value`, `Metric`
- Time-series tables commonly have: `Timestamp` (not `TimeGenerated`)
- Ingestion tracking: `.show ingestion failures`, `.show operations`
