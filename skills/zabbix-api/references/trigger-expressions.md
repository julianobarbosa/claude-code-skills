# Zabbix Trigger Expressions Reference

## Expression Syntax (Zabbix 5.4+)

```
function(/host/key,parameter)<operator><constant>
```

## Common Functions

### Value Functions

| Function | Description | Example |
|----------|-------------|---------|
| `last()` | Last value | `last(/host/key)>100` |
| `avg(period)` | Average over period | `avg(/host/key,5m)>80` |
| `min(period)` | Minimum over period | `min(/host/key,1h)<10` |
| `max(period)` | Maximum over period | `max(/host/key,1h)>95` |
| `sum(period)` | Sum over period | `sum(/host/key,1h)>1000` |
| `count(period)` | Count values | `count(/host/key,1h)>100` |
| `percentile(period,p)` | Percentile value | `percentile(/host/key,1h,95)>90` |

### Change Functions

| Function | Description | Example |
|----------|-------------|---------|
| `change()` | Absolute change | `change(/host/key)>10` |
| `diff()` | Value changed (0/1) | `diff(/host/key)=1` |
| `abschange()` | Absolute change value | `abschange(/host/key)>100` |

### Time Functions

| Function | Description | Example |
|----------|-------------|---------|
| `nodata(period)` | No data received | `nodata(/host/key,5m)=1` |
| `fuzzytime(sec)` | Time difference | `fuzzytime(/host/system.time,60)=0` |
| `now()` | Current timestamp | N/A |
| `time()` | Current time (HHMMSS) | `time()>220000` |
| `dayofweek()` | Day (1=Mon, 7=Sun) | `dayofweek()>=6` |
| `dayofmonth()` | Day of month (1-31) | `dayofmonth()=1` |

### String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `strlen()` | String length | `strlen(last(/host/key))>100` |
| `find(pattern)` | String contains | `find(/host/key,,"like","error")=1` |
| `regexp(pattern)` | Regex match | `regexp(/host/key,,".*error.*")=1` |

### Comparison Functions

| Function | Description | Example |
|----------|-------------|---------|
| `between(min,max)` | Value in range | `between(10,last(/host/key),90)=0` |
| `in(v1,v2,...)` | Value in list | `in(1,last(/host/key),2,3)=0` |

## Operators

| Operator | Description |
|----------|-------------|
| `=` | Equal |
| `<>` | Not equal |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less or equal |
| `>=` | Greater or equal |
| `and` | Logical AND |
| `or` | Logical OR |
| `not` | Logical NOT |

## Time Suffixes

| Suffix | Meaning |
|--------|---------|
| `s` | Seconds |
| `m` | Minutes |
| `h` | Hours |
| `d` | Days |
| `w` | Weeks |

## Common Expression Examples

### CPU Monitoring

```
# High CPU load
last(/host/system.cpu.load[percpu,avg1])>5

# CPU utilization over 90% for 5 minutes
avg(/host/system.cpu.util,5m)>90

# CPU spike detection
change(/host/system.cpu.util)>30
```

### Memory Monitoring

```
# Low available memory (less than 10%)
last(/host/vm.memory.size[pavailable])<10

# Memory usage trend increasing
avg(/host/vm.memory.size[used],1h)>avg(/host/vm.memory.size[used],24h)*1.2
```

### Disk Monitoring

```
# Disk space low (less than 10% free)
last(/host/vfs.fs.size[/,pfree])<10

# Disk space critically low
last(/host/vfs.fs.size[/,pfree])<5 and last(/host/vfs.fs.size[/,free])<1073741824

# Disk I/O high
avg(/host/vfs.dev.read.rate[sda],5m)>10000000
```

### Network Monitoring

```
# Interface down
last(/host/net.if.status[eth0])=2

# High network traffic
avg(/host/net.if.in[eth0],5m)>100000000

# Packet loss detected
last(/host/icmppingloss)>10
```

### Service Monitoring

```
# Process not running
last(/host/proc.num[nginx])=0

# Too many processes
last(/host/proc.num[])>300

# Service port down
last(/host/net.tcp.service[http,,80])=0
```

### Log Monitoring

```
# Error in log
find(/host/log[/var/log/app.log],1h,"like","ERROR")=1

# Multiple errors
count(/host/log[/var/log/app.log],1h,"ERROR")>10

# Specific pattern
regexp(/host/log[/var/log/app.log],,"Exception.*timeout")=1
```

### Availability

```
# Agent unreachable for 5 minutes
nodata(/host/agent.ping,5m)=1

# Host unreachable
last(/host/icmpping)=0

# Multiple failures
count(/host/icmpping,10m,,"eq","0")>3
```

### Time-Based

```
# Only during business hours
last(/host/key)>100 and time()>=090000 and time()<=180000

# Weekday only
last(/host/key)>100 and dayofweek()<6

# Not during maintenance window
last(/host/key)>100 and time()<020000
```

## Recovery Expressions

Set separate recovery condition:

```python
api.trigger.create(
    description="High CPU",
    expression="last(/host/system.cpu.util)>90",
    recovery_mode=1,  # 0=expression, 1=recovery_expression, 2=none
    recovery_expression="last(/host/system.cpu.util)<70"
)
```

## Trigger Dependencies

Prevent alert storms with dependencies:

```python
# Child trigger won't fire if parent is in problem state
api.trigger.adddependencies(
    triggerid="child_trigger_id",
    dependsOnTriggerid="parent_trigger_id"
)
```

## Macros in Expressions

| Macro | Description |
|-------|-------------|
| `{HOST.HOST}` | Technical hostname |
| `{HOST.NAME}` | Visible hostname |
| `{HOST.IP}` | Host IP address |
| `{TRIGGER.VALUE}` | Trigger state (0/1) |
| `{$MACRO}` | User macro |
