# DefectDojo API v2 Complete Reference

## Authentication

### API Token Generation

Generate your API token at: `<your-instance>/api/key-v2`

### Request Headers

```bash
Authorization: Token <your-api-token>
Content-Type: application/json  # For JSON requests
Accept: application/json
```

### Python Example

```python
import requests

headers = {
    'Authorization': 'Token c8572a5adf107a693aa6c72584da31f4d1f1dcff',
    'Accept': 'application/json'
}

response = requests.get(
    'https://defectdojo.example.com/api/v2/products/',
    headers=headers
)
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DD_API_TOKENS_ENABLED` | Set to `False` to disable all API tokens |
| `DD_API_TOKEN_AUTH_ENDPOINT_ENABLED` | Set to `False` to disable only `/api/v2/api-token-auth/` |

## Products API

### List Products

```bash
curl -X GET "https://defectdojo.example.com/api/v2/products/" \
  -H "Authorization: Token <api-token>"
```

**Query Parameters:**

- `name` - Filter by exact name
- `name__contains` - Filter by partial name match
- `prod_type` - Filter by product type ID
- `offset` - Pagination offset
- `limit` - Number of results per page

### Create Product

```bash
curl -X POST "https://defectdojo.example.com/api/v2/products/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "description": "Description of the application",
    "prod_type": 1
  }'
```

**Required Fields:**

- `name` (string)
- `prod_type` (integer) - Product type ID

**Optional Fields:**

- `description` (string)
- `tags` (array of strings)
- `business_criticality` (string): "very high", "high", "medium", "low", "very low", "none"
- `platform` (string): "web service", "desktop", "iot", "mobile", "web"
- `lifecycle` (string): "construction", "production", "retirement"
- `origin` (string): "third party library", "purchased", "contractor", "internal", "open source", "outsourced"
- `external_audience` (boolean)
- `internet_accessible` (boolean)

### Get Product by ID

```bash
curl -X GET "https://defectdojo.example.com/api/v2/products/1/" \
  -H "Authorization: Token <api-token>"
```

### Update Product

```bash
curl -X PATCH "https://defectdojo.example.com/api/v2/products/1/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description"
  }'
```

## Product Types API

### List Product Types

```bash
curl -X GET "https://defectdojo.example.com/api/v2/product_types/" \
  -H "Authorization: Token <api-token>"
```

### Create Product Type

```bash
curl -X POST "https://defectdojo.example.com/api/v2/product_types/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web Applications",
    "description": "All web-based applications"
  }'
```

## Engagements API

### List Engagements

```bash
curl -X GET "https://defectdojo.example.com/api/v2/engagements/" \
  -H "Authorization: Token <api-token>"
```

**Query Parameters:**

- `product` - Filter by product ID
- `engagement_type` - "Interactive" or "CI/CD"
- `status` - "Not Started", "In Progress", "Completed", "Cancelled"
- `name__contains` - Partial name match

### Create Engagement

```bash
curl -X POST "https://defectdojo.example.com/api/v2/engagements/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2024 Security Review",
    "product": 1,
    "target_start": "2024-01-01",
    "target_end": "2024-03-31",
    "engagement_type": "Interactive",
    "status": "In Progress"
  }'
```

**Required Fields:**

- `name` (string)
- `product` (integer) - Product ID
- `target_start` (date) - YYYY-MM-DD format
- `target_end` (date) - YYYY-MM-DD format

**Optional Fields:**

- `engagement_type` (string): "Interactive" or "CI/CD"
- `status` (string): "Not Started", "In Progress", "Completed", "Cancelled"
- `description` (string)
- `lead` (integer) - User ID
- `build_id` (string) - CI/CD build identifier
- `commit_hash` (string)
- `branch_tag` (string)
- `source_code_management_uri` (string)
- `deduplication_on_engagement` (boolean)

## Tests API

### List Tests

```bash
curl -X GET "https://defectdojo.example.com/api/v2/tests/" \
  -H "Authorization: Token <api-token>"
```

**Query Parameters:**

- `engagement` - Filter by engagement ID
- `test_type` - Filter by test type ID
- `title__contains` - Partial title match

### Create Test

```bash
curl -X POST "https://defectdojo.example.com/api/v2/tests/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "engagement": 1,
    "test_type": 1,
    "target_start": "2024-01-15",
    "target_end": "2024-01-15"
  }'
```

## Findings API

### List Findings

```bash
curl -X GET "https://defectdojo.example.com/api/v2/findings/" \
  -H "Authorization: Token <api-token>"
```

**Query Parameters:**

- `test` - Filter by test ID
- `test__engagement` - Filter by engagement ID
- `test__engagement__product` - Filter by product ID
- `severity` - "Critical", "High", "Medium", "Low", "Info"
- `active` - Boolean
- `verified` - Boolean
- `duplicate` - Boolean
- `false_p` - Boolean (false positive)
- `cwe` - CWE ID
- `title__contains` - Partial title match

### Get Finding by ID

```bash
curl -X GET "https://defectdojo.example.com/api/v2/findings/1/" \
  -H "Authorization: Token <api-token>"
```

### Update Finding

```bash
curl -X PATCH "https://defectdojo.example.com/api/v2/findings/1/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "active": false,
    "verified": true,
    "false_p": false
  }'
```

### Create Finding Manually

```bash
curl -X POST "https://defectdojo.example.com/api/v2/findings/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SQL Injection in Login",
    "description": "Detailed description of the vulnerability",
    "severity": "High",
    "test": 1,
    "active": true,
    "verified": true,
    "cwe": 89,
    "mitigation": "Use parameterized queries"
  }'
```

**Required Fields:**

- `title` (string)
- `severity` (string): "Critical", "High", "Medium", "Low", "Info"
- `test` (integer) - Test ID

## Import Scan API

### Import Scan (First Import)

```bash
curl -X POST "https://defectdojo.example.com/api/v2/import-scan/" \
  -H "Authorization: Token <api-token>" \
  -F "scan_type=Trivy Scan" \
  -F "file=@trivy-results.json" \
  -F "engagement=1" \
  -F "minimum_severity=Info" \
  -F "active=true" \
  -F "verified=false"
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_type` | string | Yes | Scanner identifier (see Supported Parsers) |
| `file` | file | Yes | Scan results file |
| `engagement` | integer | Conditional | Engagement ID (required if not using auto_create) |
| `product_type_name` | string | No | For auto_create_context |
| `product_name` | string | No | For auto_create_context |
| `engagement_name` | string | No | For auto_create_context |
| `test_title` | string | No | Custom test name |
| `minimum_severity` | string | No | "Info", "Low", "Medium", "High", "Critical" |
| `active` | boolean | No | Mark findings as active |
| `verified` | boolean | No | Mark findings as verified |
| `scan_date` | date | No | Override scan completion date |
| `auto_create_context` | boolean | No | Auto-create Product/Engagement |
| `close_old_findings` | boolean | No | Close findings not in scan |
| `push_to_jira` | boolean | No | Push findings to JIRA |
| `tags` | array | No | Tags to apply to test |

### Reimport Scan (Subsequent Imports)

```bash
curl -X POST "https://defectdojo.example.com/api/v2/reimport-scan/" \
  -H "Authorization: Token <api-token>" \
  -F "scan_type=Trivy Scan" \
  -F "file=@trivy-results.json" \
  -F "test=1" \
  -F "do_not_reactivate=true"
```

**Additional Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `test` | integer | Existing test ID to reimport into |
| `do_not_reactivate` | boolean | Prevent reopening previously closed findings |

**Reimport Behavior:**

- New findings are created
- Existing findings are updated
- Findings not in new scan are closed (unless `close_old_findings=false`)
- Can also auto-create context like `/import-scan/`

## Endpoints API

### List Endpoints

```bash
curl -X GET "https://defectdojo.example.com/api/v2/endpoints/" \
  -H "Authorization: Token <api-token>"
```

**Query Parameters:**

- `product` - Filter by product ID
- `host` - Filter by hostname
- `protocol` - "http", "https", etc.

### Create Endpoint

```bash
curl -X POST "https://defectdojo.example.com/api/v2/endpoints/" \
  -H "Authorization: Token <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "api.example.com",
    "protocol": "https",
    "port": 443,
    "path": "/api/v1",
    "product": 1
  }'
```

## Test Types API

### List Test Types (Scanner Types)

```bash
curl -X GET "https://defectdojo.example.com/api/v2/test_types/" \
  -H "Authorization: Token <api-token>"
```

This returns all available scanner types that can be used in `scan_type` parameter.

## Users API

### List Users

```bash
curl -X GET "https://defectdojo.example.com/api/v2/users/" \
  -H "Authorization: Token <api-token>"
```

**Query Parameters:**

- `username__contains` - Partial username match
- `email__contains` - Partial email match
- `is_active` - Boolean

## Common Scan Types

| Scan Type | File Format |
|-----------|-------------|
| `Trivy Scan` | JSON |
| `Semgrep JSON Report` | JSON |
| `Bandit Scan` | JSON |
| `OWASP Dependency-Check` | XML |
| `Snyk Code Scan` | JSON |
| `SonarQube Scan` | JSON |
| `Checkmarx Scan` | XML |
| `Burp REST API` | JSON |
| `OWASP ZAP` | XML |
| `Nessus` | CSV/XML |
| `Qualys Scan` | XML |
| `Gitleaks Scan` | JSON |
| `Trufflehog Scan` | JSON |
| `Checkov` | JSON |
| `kube-bench Scan` | JSON |
| `AWS Security Hub` | JSON |
| `Azure Security Center` | JSON |

## Pagination

All list endpoints support pagination:

```bash
curl "https://defectdojo.example.com/api/v2/findings/?limit=100&offset=0"
```

**Response Format:**

```json
{
  "count": 1234,
  "next": "https://defectdojo.example.com/api/v2/findings/?limit=100&offset=100",
  "previous": null,
  "results": [...]
}
```

## Error Handling

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

Or for validation errors:

```json
{
  "field_name": ["Error message for this field"]
}
```

## Rate Limiting

DefectDojo doesn't have built-in rate limiting, but consider:

- Implementing client-side delays for bulk operations
- Using batch operations where available
- Monitoring API response times

## Interactive Documentation

Access Swagger UI at: `<your-instance>/api/v2/oa3/swagger-ui/`

This provides:

- Interactive API testing
- Complete schema documentation
- Request/response examples
