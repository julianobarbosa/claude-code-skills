# Zabbix API Reference

## API Endpoint

All API calls go to: `https://<zabbix-server>/api_jsonrpc.php`

## Authentication Methods

### API Token (Zabbix 5.4+, Recommended)

```python
api.login(token="your_api_token")
```

### Username/Password

```python
api.login(user="Admin", password="zabbix")
api.logout()  # Required when using user/password
```

## Complete API Class Reference

### Host Management

| Method | Description |
|--------|-------------|
| `host.get` | Retrieve hosts |
| `host.create` | Create new host |
| `host.update` | Update host properties |
| `host.delete` | Delete hosts |
| `host.massadd` | Add templates/groups to multiple hosts |
| `host.massremove` | Remove templates/groups from multiple hosts |
| `host.massupdate` | Update multiple hosts |

**Key host.get parameters:**

- `output` - Fields to return
- `hostids` - Filter by host IDs
- `groupids` - Filter by group IDs
- `templateids` - Filter by linked template IDs
- `selectInterfaces` - Include interface data
- `selectGroups` - Include group data
- `selectParentTemplates` - Include linked templates
- `selectItems` - Include items
- `selectTriggers` - Include triggers
- `selectMacros` - Include host macros
- `filter` - Exact match filters
- `search` - Pattern matching
- `searchWildcardsEnabled` - Enable wildcards in search

### Host Groups

| Method | Description |
|--------|-------------|
| `hostgroup.get` | Retrieve groups |
| `hostgroup.create` | Create group |
| `hostgroup.update` | Update group |
| `hostgroup.delete` | Delete group |
| `hostgroup.massadd` | Add hosts to groups |
| `hostgroup.massremove` | Remove hosts from groups |

### Templates

| Method | Description |
|--------|-------------|
| `template.get` | Retrieve templates |
| `template.create` | Create template |
| `template.update` | Update template |
| `template.delete` | Delete template |
| `template.massadd` | Link templates to hosts |
| `template.massremove` | Unlink templates |

### Items

| Method | Description |
|--------|-------------|
| `item.get` | Retrieve items |
| `item.create` | Create item |
| `item.update` | Update item |
| `item.delete` | Delete item |

**Item types:**

| Type | Value | Description |
|------|-------|-------------|
| Zabbix agent | 0 | Passive agent checks |
| Zabbix trapper | 2 | Items for sender data |
| Simple check | 3 | ICMP/TCP checks |
| Zabbix internal | 5 | Internal metrics |
| Zabbix agent (active) | 7 | Active agent checks |
| Zabbix aggregate | 8 | Aggregate calculations |
| Web item | 9 | Web scenario items |
| External check | 10 | External scripts |
| Database monitor | 11 | Database queries |
| IPMI agent | 12 | IPMI sensors |
| SSH agent | 13 | SSH checks |
| Telnet agent | 14 | Telnet checks |
| Calculated | 15 | Calculated items |
| JMX agent | 16 | JMX monitoring |
| SNMP trap | 17 | SNMP traps |
| Dependent item | 18 | Master item derivatives |
| HTTP agent | 19 | HTTP/REST API |
| SNMP agent | 20 | SNMP polling |
| Script | 21 | Custom scripts |

**Value types:**

| Type | Value | Description |
|------|-------|-------------|
| Float | 0 | Numeric (float) |
| Character | 1 | Short text (up to 255) |
| Log | 2 | Log data |
| Unsigned | 3 | Numeric (unsigned 64-bit) |
| Text | 4 | Long text |

### Triggers

| Method | Description |
|--------|-------------|
| `trigger.get` | Retrieve triggers |
| `trigger.create` | Create trigger |
| `trigger.update` | Update trigger |
| `trigger.delete` | Delete trigger |
| `trigger.adddependencies` | Add trigger dependencies |
| `trigger.deletedependencies` | Remove dependencies |

**Trigger severities:**

| Severity | Value |
|----------|-------|
| Not classified | 0 |
| Information | 1 |
| Warning | 2 |
| Average | 3 |
| High | 4 |
| Disaster | 5 |

### Events and Problems

| Method | Description |
|--------|-------------|
| `event.get` | Retrieve events |
| `event.acknowledge` | Acknowledge events |
| `problem.get` | Get current problems |

**Event sources:**

- 0: Trigger
- 1: Discovery rule
- 2: Autoregistration
- 3: Internal

### History

| Method | Description |
|--------|-------------|
| `history.get` | Retrieve historical data |

**Important:** The `history` parameter must match the item's `value_type`.

### Maintenance

| Method | Description |
|--------|-------------|
| `maintenance.get` | Retrieve maintenance windows |
| `maintenance.create` | Create maintenance |
| `maintenance.update` | Update maintenance |
| `maintenance.delete` | Delete maintenance |

**Timeperiod types:**

- 0: One-time
- 2: Daily
- 3: Weekly
- 4: Monthly

### Actions

| Method | Description |
|--------|-------------|
| `action.get` | Retrieve actions |
| `action.create` | Create action |
| `action.update` | Update action |
| `action.delete` | Delete action |

### Users

| Method | Description |
|--------|-------------|
| `user.get` | Retrieve users |
| `user.create` | Create user |
| `user.update` | Update user |
| `user.delete` | Delete user |
| `user.login` | Authenticate |
| `user.logout` | End session |

### Configuration

| Method | Description |
|--------|-------------|
| `configuration.export` | Export to XML/JSON |
| `configuration.import` | Import from XML/JSON |

## Common Query Patterns

### Filtering

```python
# Exact match
api.host.get(filter={"host": "server01"})

# Multiple values
api.host.get(filter={"host": ["server01", "server02"]})

# Pattern search
api.host.get(search={"host": "server"}, searchWildcardsEnabled=True)
```

### Pagination

```python
# First page
api.host.get(limit=100)

# Next page
api.host.get(limit=100, offset=100)
```

### Sorting

```python
api.host.get(sortfield="host", sortorder="ASC")
api.trigger.get(sortfield=["priority", "lastchange"], sortorder=["DESC", "DESC"])
```

### Output Control

```python
# Specific fields only
api.host.get(output=["hostid", "host", "name"])

# All fields
api.host.get(output="extend")

# Count only
api.host.get(countOutput=True)
```

## Error Codes

| Code | Description |
|------|-------------|
| -32700 | Parse error (invalid JSON) |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32500 | Application error |
| -32400 | System error |
| -32300 | Transport error |

## Rate Limiting

Zabbix API does not have built-in rate limiting, but consider:

- Use batch operations (arrays) when possible
- Limit `output` to needed fields
- Use `countOutput` when only count is needed
- Implement client-side rate limiting for bulk operations
