# Microsoft / Azure sources

## The three-tool pattern

The Microsoft Learn MCP server exposes three tools with genuinely different jobs. Using them in the wrong order wastes calls and produces shallow docs.

| Tool | Returns | Use it for |
|---|---|---|
| `microsoft_docs_search` | up to 10 chunks, ~500 tokens each, with titles + URLs | finding *which* pages matter |
| `microsoft_docs_fetch` | a full page as markdown, tables and code blocks preserved | everything you'll actually write from |
| `microsoft_code_sample_search` | up to 20 code samples, optional `language` filter | exact SDK call shapes |

**Search gives breadth. Fetch gives depth. Write from fetch.**

Search results are the map, not the territory. They routinely truncate exactly the content a local doc needs: billing tables, metric-name tables, minimum-version matrices, "known issues and considerations" lists. Identify the two or three pages that matter from search, then fetch each one in full.

## Where Azure feature facts live

An Azure feature's facts are spread across predictable page types. Fetching the right two beats fetching six.

- **The feature's own reference page** (`/azure/<service>/<feature>`) — mechanics, prerequisites, per-tool enablement tabs (Portal / PowerShell / CLI), billing details, monitoring metrics, minimum SDK versions. This is the primary source and it outranks the others on conflicts.
- **The comparison / "cost optimization services" page** — how the feature relates to the alternatives it competes with, plus a decision table. This is where "when should I use this instead of X" comes from.
- **The overview page for the family** (e.g. access tiers overview) — the surrounding concepts a reader needs to place the feature.
- **The `azure.microsoft.com/blog` announcement** — GA date, preview history, customer results, regional rollout. Good for the lead paragraph and the timeline. Weak on mechanics.
- **The pricing page** — region-specific and usually rendered client-side, so a plain fetch often returns nothing usable. Link it and say the rates are region-specific rather than inventing a number. The Azure pricing MCP tool (`pricing` under the Azure MCP server) can retrieve retail rates if a real number is needed.

Cloud-availability caveats hide in the reference page's "Known issues and considerations" section: a feature can be GA in commercial Azure while still preview in Azure Government and Azure operated by 21Vianet, and preview clouds often require registering a feature flag. Sovereign-cloud status is exactly the kind of thing a local doc should state and an announcement won't.

## Verifying Terraform / SDK support at a pinned version

Microsoft docs describe the current API. The AzureRM provider carries a vendored copy of the Azure SDK, and whether a value is accepted depends on which SDK version is vendored into the provider version **this repo pins** — not on what the docs or the provider's `main` branch say.

Find the pin, then check the released artifact at that tag:

```bash
# 1. What does this repo pin?
grep -rn "version" iac/**/versions.tf

# 2. Does the enum exist in the vendored SDK at that tag?
curl -s "https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/v4.73.0/vendor/github.com/hashicorp/go-azure-sdk/resource-manager/storage/<api-version>/<package>/constants.go" | grep -c "<ConstantName>"

# 3. Does the resource schema validate against that enum?
curl -s "https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/v4.73.0/internal/services/storage/storage_account_resource.go" | grep -A5 '"<argument_name>": {'
```

Step 3 matters on its own: a constant existing in the vendored SDK only helps if the resource schema validates against `PossibleValuesFor<X>()` rather than a hand-written allowlist. Both checks together are what let you write "supported on the pinned provider" as a fact.

Note that a provider's `CHANGELOG.md` is a poor instrument here — it's enormous, and summarizing it can return a false "no entries found" for a change that's really there. The raw file at the tag is the reliable check.

## Equivalent checks for other Microsoft ecosystems

- **Azure CLI** — the reference page's client-tooling table usually states a minimum `az` version. Confirm locally with `az version`.
- **.NET / Python / JS SDKs** — the same minimum-version table; confirm against the package registry's release list for that major.
- **REST API** — the api-version string is load-bearing. Quote the exact one from the docs in every example command, because features frequently only exist on the newest api-version.
