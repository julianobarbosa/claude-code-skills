# Dependency-Track Troubleshooting Guide

Comprehensive troubleshooting guide for common issues with Dependency-Track deployment, configuration, and operation.

## Table of Contents

1. [Installation & Deployment](#installation--deployment)
2. [Performance Issues](#performance-issues)
3. [Vulnerability Scanning](#vulnerability-scanning)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Issues](#api-issues)
6. [CI/CD Integration](#cicd-integration)
7. [Database Issues](#database-issues)
8. [Kubernetes-Specific Issues](#kubernetes-specific-issues)
9. [Logging & Debugging](#logging--debugging)

---

## Installation & Deployment

### Container crashes immediately after starting

**Symptoms:** Container exits with code 137 or OOM killed message

**Cause:** Insufficient memory allocated

**Solution:**
```bash
# Docker - allocate minimum 4.5GB (8GB+ recommended)
docker run -d -m 8192m -p 8080:8080 dependencytrack/bundled

# Docker Compose - add memory limits
services:
  apiserver:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

### Service stops working after 1-2 weeks

**Symptoms:** API becomes unresponsive, requires restart

**Cause:** OS temp directory cleanup affecting embedded Jetty server

**Solution:**
```yaml
environment:
  JAVA_OPTIONS: >-
    -Djava.io.tmpdir=/data/tmp
    -Xms4g
    -Xmx8g
```

Create persistent tmp directory:
```bash
mkdir -p /data/tmp
chown 1000:1000 /data/tmp
```

### Initial startup takes forever

**Symptoms:** System unresponsive for 30+ minutes on first boot

**Cause:** Mirroring vulnerability databases (NVD, GitHub Advisories)

**Solution:** This is expected behavior. Monitor progress:
```bash
# Docker logs
docker logs -f dependency-track-apiserver

# Look for messages like:
# "Mirroring NVD... 50% complete"
```

Do NOT restart during initial sync.

### Port already in use

**Symptoms:** `Error: bind: address already in use`

**Solution:**
```bash
# Find process using port
lsof -i :8080
netstat -tulpn | grep 8080

# Kill the process or use different port
docker run -p 9080:8080 dependencytrack/apiserver
```

---

## Performance Issues

### Slow API responses

**Causes & Solutions:**

1. **Insufficient heap memory:**
```yaml
environment:
  JAVA_OPTIONS: >-
    -Xms8g
    -Xmx16g
    -XX:+UseG1GC
```

2. **Database connection issues:**
```yaml
# Add connection pool settings
ALPINE_DATABASE_POOL_ENABLED: "true"
ALPINE_DATABASE_POOL_MAX_SIZE: "20"
ALPINE_DATABASE_POOL_MIN_IDLE: "5"
```

3. **Too many components per project:**
   - Break large monorepos into smaller projects
   - Use project hierarchies for organization

### High CPU usage

**Causes:**
- Vulnerability analysis running
- Multiple concurrent BOM uploads
- Full portfolio re-analysis

**Solutions:**
```yaml
# Limit concurrent analysis
ALPINE_VULN_ANALYSIS_CACHE_ENABLED: "true"
ALPINE_VULN_ANALYSIS_CACHE_VALIDITY_PERIOD: "86400"

# Schedule analyzer runs during off-hours
ALPINE_VULN_ANALYSIS_SCHEDULE_ENABLED: "true"
ALPINE_VULN_ANALYSIS_SCHEDULE_CRON: "0 0 3 * * ?"  # 3 AM daily
```

### Memory leak symptoms

**Solution:** JVM tuning for long-running instances:
```yaml
JAVA_OPTIONS: >-
  -Xms8g
  -Xmx16g
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=200
  -XX:+ParallelRefProcEnabled
  -XX:+UseStringDeduplication
  -XX:MaxMetaspaceSize=512m
```

---

## Vulnerability Scanning

### No vulnerabilities found for uploaded SBOM

**Cause 1:** Analyzers not enabled

**Solution:**
1. Go to Administration > Analyzers
2. Enable:
   - Internal Analyzer (always enable)
   - OSS Index Analyzer (requires API token)
   - Snyk Analyzer (optional)
   - Trivy Analyzer (optional)

**Cause 2:** OSS Index requires API token

**Solution:**
1. Register at https://ossindex.sonatype.org/
2. Get API token from account settings
3. Configure in Dependency-Track:
```yaml
ALPINE_OSS_INDEX_ENABLED: "true"
ALPINE_OSS_INDEX_API_USERNAME: "your-email"
ALPINE_OSS_INDEX_API_TOKEN: "your-token"
```

**Cause 3:** Analyzers run on 6-hour schedule

**Solution:** Re-upload SBOM to trigger immediate analysis, or wait for scheduled run.

### NVD shows more CVEs than Dependency-Track

**Cause:** NVD includes "affected configurations" where component is part of vulnerable setup but not directly vulnerable

**Solution:** This is correct behavior. Dependency-Track only flags directly vulnerable components.

### Vulnerabilities not correlating to components

**Cause:** Missing or invalid Package URLs (PURLs) in SBOM

**Solution:**
1. Ensure SBOM generator includes PURLs
2. Verify PURL format: `pkg:type/namespace/name@version`
3. Check component has valid CPE for NVD correlation

```bash
# Verify BOM has PURLs
cat bom.json | jq '.components[].purl'
```

### OSS Index rate limiting

**Symptoms:** 429 Too Many Requests errors in logs

**Solution:**
1. Get paid tier or reduce scan frequency
2. Enable caching:
```yaml
ALPINE_OSS_INDEX_CACHE_VALIDITY_PERIOD: "43200"  # 12 hours
```

---

## Authentication & Authorization

### LDAP synchronization delays

**Cause:** Auto-provisioned accounts sync via async job queue

**Solution:**
- Wait for background sync (can take minutes under load)
- Create accounts manually for immediate sync
- Check LDAP configuration syntax

### LDAP connection failures

**Debug steps:**
```bash
# Test LDAP connectivity
ldapsearch -x -H ldap://ldap.example.com:389 \
  -b "dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" \
  -W "(uid=testuser)"
```

**Common configuration issues:**

```properties
# Active Directory
ALPINE_LDAP_SERVER_URL=ldap://ad.example.com:3268
ALPINE_LDAP_AUTH_USERNAME_FORMAT=%s@example.com

# OpenLDAP
ALPINE_LDAP_SERVER_URL=ldap://ldap.example.com:389
ALPINE_LDAP_AUTH_USERNAME_FORMAT=uid=%s,ou=users,dc=example,dc=com
```

### OIDC login redirects fail

**Cause 1:** Incorrect issuer URL

**Solution:**
```yaml
# Include full path to .well-known/openid-configuration parent
ALPINE_OIDC_ISSUER: "https://auth.example.com/realms/master"
```

**Cause 2:** Client ID mismatch

**Solution:** Ensure frontend and API use same client ID:
```yaml
# API Server
ALPINE_OIDC_CLIENT_ID: "dependency-track"

# Frontend
OIDC_CLIENT_ID: "dependency-track"
```

### OIDC Groups not appearing in UI

**Symptoms:** Configured Azure AD groups don't show in Administration > OpenID Connect Groups

**Cause 1:** No users from those groups have authenticated yet

**Solution:** Groups only appear after a user with that group membership logs in. To verify:
1. Add a test user to the Azure AD group
2. Have them login to Dependency-Track via OIDC
3. Check if group appears in UI after login

**Cause 2:** Groups claim not included in ID token

**Solution:**
```bash
# Verify Azure AD App Registration configuration
az ad app show --id $CLIENT_ID --query '{
  groupMembershipClaims:groupMembershipClaims,
  optionalClaims:optionalClaims.idToken[?name==`groups`]
}'

# Should show:
# groupMembershipClaims: SecurityGroup
# optionalClaims with groups
```

**Cause 3:** User not member of Azure AD group

**Solution:**
```bash
# Check user's group memberships
az ad user get-member-objects --id user@example.com

# Add user to group
az ad group member add \
  --group "G-Usuarios-DependencyTrack-Admin" \
  --member-id <user-object-id>
```

**Cause 4:** Azure AD returns group GUIDs that exceed token size limit

**Solution:** For users in many groups, Azure AD may truncate the groups claim:
1. Use application roles instead of groups
2. Or enable "overage claim" to fetch groups separately via Graph API

### OIDC team mapping not working

**Symptoms:** User logs in but isn't assigned to expected Team

**Debug Steps:**
```bash
# 1. Get user's teams via API
curl -s -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/user/self" | jq '.teams'

# 2. Verify group-to-team mapping exists
curl -s -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/team" | jq '.[] | {name, mappedOidcGroups}'

# 3. Check API server logs for OIDC processing
kubectl logs -n dependency-track deployment/dependency-track-apiserver \
  | grep -i "oidc\|group\|team"
```

**Solution:** Manually create group mapping via API:
```bash
# Azure AD Group Object ID to map
AZURE_GROUP_ID="31d6daa5-5cc2-4e5f-9bf5-75ee8e09198c"

# Get Team UUID
TEAM_UUID=$(curl -s -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/team" | jq -r '.[] | select(.name=="Administrators") | .uuid')

# Step 1: Create OIDC Group first (required before mapping)
curl -X PUT "${DTRACK_URL}/api/v1/oidc/group" \
  -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"uuid\": \"${AZURE_GROUP_ID}\", \"name\": \"${AZURE_GROUP_ID}\"}"

# Step 2: Get the created OIDC Group UUID
OIDC_GROUP_UUID=$(curl -s -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/oidc/group" | jq -r ".[] | select(.name==\"${AZURE_GROUP_ID}\") | .uuid")

# Step 3: Create mapping with UUID strings (NOT objects)
curl -X PUT "${DTRACK_URL}/api/v1/oidc/mapping" \
  -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"team\": \"${TEAM_UUID}\", \"group\": \"${OIDC_GROUP_UUID}\"}"
```

> **Note:** The mapping endpoint expects UUID strings, not objects. Using `{"team": {"uuid": "..."}}` returns HTTP 400.

### API key not working

**Symptoms:** 401 Unauthorized on API calls

**Solutions:**
1. Verify header name: `X-Api-Key` (case-sensitive)
2. Check key hasn't expired
3. Verify team has required permissions
4. Keys are hashed after creation - generate new one if lost

```bash
# Test API key
curl -v -H "X-Api-Key: YOUR_KEY" \
  https://dtrack.example.com/api/v1/version
```

---

## API Issues

### PKIX path building failed

**Cause:** Self-signed or internal CA certificates

**Solution:**
1. Import certificate into Java truststore:
```bash
keytool -import -alias dtrack-cert \
  -keystore /usr/lib/jvm/java-17/lib/security/cacerts \
  -file /path/to/certificate.crt
```

2. Or use environment variable:
```yaml
JAVA_OPTIONS: >-
  -Djavax.net.ssl.trustStore=/data/truststore.jks
  -Djavax.net.ssl.trustStorePassword=changeit
```

### 413 Request Entity Too Large

**Cause:** Nginx/ingress body size limit

**Solution for Kubernetes:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
```

**Solution for nginx proxy:**
```nginx
client_max_body_size 100M;
proxy_read_timeout 600;
proxy_send_timeout 600;
```

### BOM upload returns 400 Bad Request

**Causes:**
1. Invalid JSON/XML format
2. Base64 encoding issues
3. Missing required fields

**Debug:**
```bash
# Validate JSON syntax
cat bom.json | jq .

# Test with minimal payload
curl -X PUT "https://dtrack.example.com/api/v1/bom" \
  -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"projectName\": \"test\",
    \"projectVersion\": \"1.0\",
    \"autoCreate\": true,
    \"bom\": \"$(base64 -w0 bom.json)\"
  }"
```

### API returns empty array when data exists

**Cause:** Pagination - default page size may not return all results

**Solution:**
```bash
# Specify page size
curl -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/project?pageSize=1000&pageNumber=1"
```

---

## CI/CD Integration

### Jenkins plugin timeout errors

**Solution:**
```groovy
dependencyTrackPublisher(
    artifact: 'bom.json',
    projectName: 'my-project',
    synchronous: true,
    // Increase timeout for large projects
    pollingTimeout: 10,  // minutes
    pollingInterval: 5   // seconds
)
```

### GitHub Action fails with connection refused

**Cause:** Firewall rules blocking GitHub runners

**Solution:**
1. Use self-hosted runners inside your network
2. Or expose Dependency-Track via public URL with authentication
3. Check security group / firewall rules

### SBOM upload succeeds but no analysis

**Cause:** Async processing - analysis happens after upload

**Solution:**
```bash
# Wait for processing after upload
TOKEN=$(upload_sbom_and_get_token)

while true; do
  STATUS=$(curl -s -H "X-Api-Key: ${API_KEY}" \
    "${DTRACK_URL}/api/v1/bom/token/${TOKEN}")

  if [ "$(echo $STATUS | jq -r '.processing')" == "false" ]; then
    break
  fi
  sleep 5
done

# Now fetch metrics
```

---

## Database Issues

### H2 database corruption

**Symptoms:** Application won't start, database errors in logs

**Solution:** H2 is not recommended for production
1. Backup `/data` directory
2. Migrate to PostgreSQL
3. Use external database for production

### PostgreSQL connection pool exhausted

**Symptoms:** "Cannot acquire connection from pool" errors

**Solution:**
```yaml
# Increase pool size
ALPINE_DATABASE_POOL_MAX_SIZE: "30"
ALPINE_DATABASE_POOL_MAX_LIFETIME: "600000"
ALPINE_DATABASE_POOL_IDLE_TIMEOUT: "300000"
```

### Database migration failures

**Symptoms:** Application fails on startup with Liquibase errors

**Solution:**
1. Check database connectivity
2. Verify user has DDL permissions
3. Review migration logs:
```bash
docker logs dependency-track-apiserver | grep -i liquibase
```

---

## Kubernetes-Specific Issues

### Pod stuck in CrashLoopBackOff

**Debug:**
```bash
kubectl describe pod -n dtrack dtrack-apiserver-xxx
kubectl logs -n dtrack dtrack-apiserver-xxx --previous
```

**Common causes:**
- Insufficient resources (increase limits)
- Database connection failure (check service/endpoint)
- Secrets not mounted (verify secret exists)

### PVC not binding

**Solution:**
```bash
# Check StorageClass
kubectl get sc
kubectl describe pvc -n dtrack

# Verify storage class supports ReadWriteOnce
```

### Service unreachable from ingress

**Debug:**
```bash
# Check service endpoints
kubectl get endpoints -n dtrack

# Test internal connectivity
kubectl run test --rm -it --image=curlimages/curl -- \
  curl http://dtrack-apiserver:8080/api/version
```

### ConfigMap changes not applied

**Solution:** Restart pods after ConfigMap update:
```bash
kubectl rollout restart deployment -n dtrack dtrack-apiserver
```

---

## Logging & Debugging

### Enable debug logging

```yaml
environment:
  LOGGING_LEVEL: DEBUG
  # Or specific packages
  LOGGING_LEVEL_ORG_DEPENDENCYTRACK: DEBUG
  LOGGING_LEVEL_ALPINE: DEBUG
```

### View detailed API server logs

```bash
# Docker
docker logs -f dependency-track-apiserver 2>&1 | grep -E "(ERROR|WARN|vulnerability|analysis)"

# Kubernetes
kubectl logs -f -n dtrack deployment/dtrack-apiserver
```

### Log file location (container)

```
/data/dependency-track.log
/data/dependency-track.audit.log
```

### Export logs for support

```bash
# Create log bundle
docker exec dependency-track-apiserver \
  tar czf /tmp/logs.tar.gz /data/*.log

docker cp dependency-track-apiserver:/tmp/logs.tar.gz ./dtrack-logs.tar.gz
```

### Health check endpoint

```bash
curl -s https://dtrack.example.com/api/version | jq
```

Expected response:
```json
{
  "version": "4.10.0",
  "timestamp": "2024-01-15T10:00:00Z",
  "uuid": "xxx-xxx-xxx"
}
```

---

## Quick Reference: Environment Variables

### Essential Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ALPINE_DATABASE_MODE` | `embedded` | `embedded` or `external` |
| `ALPINE_DATABASE_URL` | - | JDBC connection URL |
| `ALPINE_DATABASE_DRIVER` | - | JDBC driver class |
| `ALPINE_DATABASE_USERNAME` | - | Database username |
| `ALPINE_DATABASE_PASSWORD` | - | Database password |

### Memory & Performance

| Variable | Default | Description |
|----------|---------|-------------|
| `JAVA_OPTIONS` | - | JVM arguments |
| `SYSTEM_REQUIREMENT_CHECK_ENABLED` | `true` | Check minimum requirements |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `ALPINE_LDAP_ENABLED` | `false` | Enable LDAP auth |
| `ALPINE_OIDC_ENABLED` | `false` | Enable OIDC auth |

### Analyzers

| Variable | Default | Description |
|----------|---------|-------------|
| `ALPINE_OSS_INDEX_ENABLED` | `false` | OSS Index analyzer |
| `ALPINE_SNYK_ENABLED` | `false` | Snyk analyzer |

---

## Getting Help

1. **Documentation:** https://docs.dependencytrack.org/
2. **GitHub Issues:** https://github.com/DependencyTrack/dependency-track/issues
3. **Slack:** OWASP Slack #proj-dependency-track
4. **GitHub Discussions:** https://github.com/DependencyTrack/dependency-track/discussions
