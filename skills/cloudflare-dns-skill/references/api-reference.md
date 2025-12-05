# Cloudflare DNS API Reference

Complete API reference for Cloudflare DNS operations.

## Base URL

```
https://api.cloudflare.com/client/v4
```

## Authentication

All requests require authentication:

```bash
-H "Authorization: Bearer $CF_API_TOKEN"
-H "Content-Type: application/json"
```

## DNS Records Endpoints

### List DNS Records

```
GET /zones/{zone_id}/dns_records
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by record type (A, AAAA, CNAME, etc.) |
| `name` | string | Filter by record name |
| `content` | string | Filter by record content |
| `proxied` | boolean | Filter by proxy status |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Records per page (default: 100, max: 5000) |
| `order` | string | Sort field (type, name, content, ttl, proxied) |
| `direction` | string | Sort direction (asc, desc) |
| `match` | string | Match type: any or all (default: all) |

**Example:**

```bash
# List all A records
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=A&per_page=5000" \
  -H "Authorization: Bearer $CF_API_TOKEN"

# Search by name
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=app.example.com" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

**Response:**

```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": [
    {
      "id": "372e67954025e0ba6aaa6d586b9e0b59",
      "type": "A",
      "name": "app.example.com",
      "content": "20.185.100.50",
      "proxied": true,
      "ttl": 1,
      "locked": false,
      "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
      "zone_name": "example.com",
      "created_on": "2024-01-01T00:00:00.000000Z",
      "modified_on": "2024-01-01T00:00:00.000000Z"
    }
  ],
  "result_info": {
    "page": 1,
    "per_page": 100,
    "total_pages": 1,
    "count": 1,
    "total_count": 1
  }
}
```

### Get DNS Record

```
GET /zones/{zone_id}/dns_records/{record_id}
```

### Create DNS Record

```
POST /zones/{zone_id}/dns_records
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Record type (A, AAAA, CNAME, TXT, MX, etc.) |
| `name` | string | Yes | DNS record name (use @ for root) |
| `content` | string | Yes | Record content (IP, hostname, text) |
| `ttl` | integer | No | TTL in seconds (1 = auto, min 60 for proxied) |
| `proxied` | boolean | No | Whether to proxy through Cloudflare |
| `priority` | integer | No | Priority for MX/SRV records |
| `comment` | string | No | Record comment (visible in dashboard) |
| `tags` | array | No | Record tags (Enterprise only) |

**Examples:**

```bash
# A Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "A",
    "name": "app",
    "content": "20.185.100.50",
    "ttl": 1,
    "proxied": true,
    "comment": "Managed by External-DNS"
  }'

# AAAA Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "AAAA",
    "name": "app",
    "content": "2001:db8::1",
    "ttl": 1,
    "proxied": true
  }'

# CNAME Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "www",
    "content": "app.example.com",
    "ttl": 1,
    "proxied": true
  }'

# TXT Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "TXT",
    "name": "_dmarc",
    "content": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com",
    "ttl": 3600
  }'

# MX Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "MX",
    "name": "@",
    "content": "mail.example.com",
    "priority": 10,
    "ttl": 3600
  }'

# SRV Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SRV",
    "name": "_sip._tcp",
    "data": {
      "priority": 10,
      "weight": 5,
      "port": 5060,
      "target": "sip.example.com"
    },
    "ttl": 3600
  }'

# CAA Record
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CAA",
    "name": "@",
    "data": {
      "flags": 0,
      "tag": "issue",
      "value": "letsencrypt.org"
    },
    "ttl": 3600
  }'
```

### Update DNS Record

```
PUT /zones/{zone_id}/dns_records/{record_id}
```

Full replacement - all fields required:

```bash
curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "A",
    "name": "app",
    "content": "20.185.100.60",
    "ttl": 1,
    "proxied": true
  }'
```

### Patch DNS Record

```
PATCH /zones/{zone_id}/dns_records/{record_id}
```

Partial update - only changed fields:

```bash
# Change content only
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "20.185.100.60"}'

# Toggle proxy
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proxied": false}'
```

### Delete DNS Record

```
DELETE /zones/{zone_id}/dns_records/{record_id}
```

```bash
curl -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

### Export DNS Records

```
GET /zones/{zone_id}/dns_records/export
```

Returns BIND format zone file:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/export" \
  -H "Authorization: Bearer $CF_API_TOKEN" > zone-export.txt
```

### Import DNS Records

```
POST /zones/{zone_id}/dns_records/import
```

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/import" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -F "file=@zone-import.txt"
```

## Zones Endpoints

### List Zones

```
GET /zones
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Zone name |
| `status` | string | Zone status (active, pending, etc.) |
| `account.id` | string | Account ID |
| `page` | integer | Page number |
| `per_page` | integer | Results per page |

```bash
curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[] | {name, id, status}'
```

### Get Zone

```
GET /zones/{zone_id}
```

### Zone Settings

```
GET /zones/{zone_id}/settings
GET /zones/{zone_id}/settings/{setting_id}
PATCH /zones/{zone_id}/settings/{setting_id}
```

**Common Settings:**

| Setting ID | Values | Description |
|------------|--------|-------------|
| `ssl` | off, flexible, full, strict | SSL/TLS mode |
| `always_use_https` | on, off | HTTPS redirect |
| `min_tls_version` | 1.0, 1.1, 1.2, 1.3 | Minimum TLS |
| `tls_1_3` | on, off, zrt | TLS 1.3 support |
| `http2` | on, off | HTTP/2 |
| `http3` | on, off | HTTP/3 |
| `websockets` | on, off | WebSocket support |
| `brotli` | on, off | Brotli compression |

```bash
# Get SSL setting
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
  -H "Authorization: Bearer $CF_API_TOKEN"

# Set SSL to Full (Strict)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "strict"}'
```

## API Tokens Endpoints

### Verify Token

```
GET /user/tokens/verify
```

```bash
curl -s "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

**Response:**

```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": {
    "id": "token-id",
    "status": "active",
    "not_before": "2024-01-01T00:00:00Z",
    "expires_on": "2024-12-31T23:59:59Z"
  }
}
```

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Global | 1,200 requests / 5 min |
| DNS Records (per zone) | 100 requests / 5 min |

**Headers in Response:**

```
X-RateLimit-Limit: 1200
X-RateLimit-Remaining: 1195
X-RateLimit-Reset: 1609459200
```

## Error Codes

| Code | Description |
|------|-------------|
| 1000 | Invalid API key/token |
| 1001 | Invalid zone identifier |
| 1002 | Invalid domain |
| 1003 | Invalid parameter |
| 1004 | Record already exists |
| 1005 | Record not found |
| 1006 | Content required |
| 1007 | Invalid record type |
| 1008 | Invalid TTL |
| 1009 | Invalid priority |
| 9103 | DNS record locked |
| 10000 | Authentication error |
| 81044 | Record already exists |
| 81057 | Record does not exist |

## Response Format

All responses follow this structure:

```json
{
  "success": true|false,
  "errors": [
    {
      "code": 1001,
      "message": "Invalid zone identifier"
    }
  ],
  "messages": [
    {
      "code": 10000,
      "message": "Operation completed"
    }
  ],
  "result": { ... },
  "result_info": {
    "page": 1,
    "per_page": 100,
    "total_pages": 1,
    "count": 1,
    "total_count": 1
  }
}
```

## Pagination

For endpoints returning lists:

```bash
# Page 1
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?page=1&per_page=100"

# Page 2
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?page=2&per_page=100"
```

Check `result_info.total_pages` to determine if more pages exist.
