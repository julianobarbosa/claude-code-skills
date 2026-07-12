---
name: using-cloud-cli
description: Cloud CLI patterns for GCP and AWS. Use when running bq queries, gcloud commands, aws commands, or making decisions about cloud services. Covers BigQuery cost optimization and operational best practices.
allowed-tools: Read, Bash, Grep, Glob
---

# Cloud CLI Patterns

Credentials are pre-configured. Use `--help` or Context7 for syntax.

## BigQuery

```bash
# Always estimate cost first
bq query --dry_run --use_legacy_sql=false 'SELECT ...'

# Run query
bq query --use_legacy_sql=false --format=json 'SELECT ...'

# List tables
bq ls project:dataset

# Get table schema
bq show --schema --format=json project:dataset.table
```

**Cost awareness**: Charged per bytes scanned. Use `--dry_run`, partition tables, specify columns.

## GCP (gcloud)

```bash
# List resources
gcloud compute instances list --format=json

# Describe resource
gcloud compute instances describe INSTANCE --zone=ZONE --format=json

# Create with explicit project
gcloud compute instances create NAME --project=PROJECT --zone=ZONE

# Use --quiet for automation
gcloud compute instances delete NAME --quiet
```

## AWS

```bash
# List resources
aws ec2 describe-instances --output json

# With JMESPath filtering
aws ec2 describe-instances --query 'Reservations[].Instances[].InstanceId' --output text

# Explicit region
aws s3 ls s3://bucket --region us-west-2

# Dry run where available
aws ec2 run-instances --dry-run ...
```

## References

- [GCP.md](GCP.md) - GCP service patterns and common commands
- [AWS.md](AWS.md) - AWS service patterns and common commands
- [scripts/](scripts/) - Helper scripts for common operations

---

## Gotchas

- **`gcloud auth login` and `gcloud auth application-default login` are DIFFERENT credentials** — a script working for the user can 401 in CI because CI only has the latter.
- **AWS CLI v1 vs v2 have different config formats** — both may be installed; `aws --version` reveals which is the default `aws` binary.
- **BigQuery cost estimation requires `--dry_run`** — without it, you can run a $100 query thinking it's free. Always estimate first.
- **Precedence**: `AWS_PROFILE` vs `--profile` flag vs `AWS_ACCESS_KEY_ID` direct env — three-way precedence is order-dependent and rarely documented.
- **gcloud impersonation chains via `--impersonate-service-account` need IAM token-creator on EACH hop** — missing one hop returns 403 with vague "permission denied".
- **`aws sts get-caller-identity` is the cheapest way to verify which credential you're actually using** — always check first.
