# RegisterCluster

Register a private AKS cluster on the hub Argo CD with the exec-provider form of
`argocd cluster add`.

## Step 0: Sufficiency check

Needed before anything runs: the target cluster (name, resource group, subscription), the name it
should carry in Argo CD, where the managed identity's client id and tenant id are recorded, and
which account holds admin on the hub. If the name or the target is a guess, ask. If a Git-managed
registration for the same cluster exists, surface it and ask which path wins.

## Ideal state

- The hub holds one cluster Secret for the target's API server URL, with `execProviderConfig`
  (`argocd-k8s-auth`, args `azure`) and no `bearerToken`.
- Every preflight row below was read from the authority and recorded with its output.
- No id was printed. No ServiceAccount was created on the target.

## Preflight (tool contracts)

Placeholders: `<hub-rg>` `<hub-aks>` `<tgt-rg>` `<tgt-aks>` `<tgt-sub>` `<id-rg>` `<uami>` `<ns>`
(the Argo CD namespace). Redact GUIDs in anything shown:

```bash
R() { sed -E 's/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/<guid>/g'; }
```

| Claim | Probe | Expect |
|---|---|---|
| Right account | `az account show --query user.name -o tsv` | the account with rights on the vault and the hub |
| Two federated credentials | `az identity federated-credential list -g <id-rg> --identity-name <uami> --subscription <tgt-sub> --query '[].{name:name,subject:subject,aud:audiences[0]}' -o tsv` | subjects for `argocd-server` and `argocd-application-controller`, audience `api://AzureADTokenExchange` |
| Issuer is the hub's | compare `sha256sum` of each FIC `issuer` with that of `az aks show -g <hub-rg> -n <hub-aks> --query oidcIssuerProfile.issuerUrl -o tsv \| tr -d '\n'` | equal hashes; never print the URL |
| Role on the target | `az role assignment list --assignee <principalId> --all --query '[].{role:roleDefinitionName,scope:scope}' -o tsv \| R` | one row, scoped to the target cluster |
| Token mounted | `kubectl -n <ns> get deploy/argocd-server sts/argocd-application-controller -o json` and read the projected volume and its mount path | audience `api://AzureADTokenExchange` on both |
| Helper in the image | `kubectl -n <ns> exec sts/argocd-application-controller -- sh -c 'command -v argocd-k8s-auth'` | a path |
| Hub resolves the target | `kubectl -n <ns> exec sts/argocd-application-controller -- getent hosts <target private FQDN>` | the hub-side private endpoint address |
| No existing registration | `kubectl -n <ns> get secret -l argocd.argoproj.io/secret-type=cluster -o name` and `argocd cluster list` | no Secret for this server |

The two `kubectl exec` probes run a command inside a hub pod. Report them as not read-only.

A failing row is a stop, not something to work around: a missing FIC or mount means the
identity work is unfinished, and adding the cluster anyway produces a registration that fails
at the first sync.

## Register

```bash
KC="$HOME/.kube/<tgt-aks>-private"
az aks get-credentials -g <tgt-rg> -n <tgt-aks> --subscription <tgt-sub> \
  --file "$KC" --overwrite-existing                      # no --public-fqdn

# Read the ids from their source of record into a variable. Example: a sensitive Terraform output.
REG=$(<command that prints {"client_id":…, "tenant_id":…} as JSON>)
jq -e '.client_id and .tenant_id' <<<"$REG" >/dev/null || { echo 'ids missing' >&2; exit 1; }

argocd cluster add <kubeconfig context> --kubeconfig "$KC" \
  --name <cluster name in Argo CD> \
  --exec-command argocd-k8s-auth \
  --exec-command-args azure \
  --exec-command-api-version client.authentication.k8s.io/v1beta1 \
  --exec-command-env AAD_ENVIRONMENT_NAME=AzurePublicCloud \
  --exec-command-env AAD_LOGIN_METHOD=workloadidentity \
  --exec-command-env AZURE_CLIENT_ID="$(jq -r .client_id <<<"$REG")" \
  --exec-command-env AZURE_TENANT_ID="$(jq -r .tenant_id <<<"$REG")" \
  --exec-command-env AZURE_FEDERATED_TOKEN_FILE=<mount path>/<token file> \
  --exec-command-env AZURE_AUTHORITY_HOST=https://login.microsoftonline.com/
unset REG
```

`AZURE_FEDERATED_TOKEN_FILE` is the mount path read in preflight plus the projected token's
`path`. Add `--project <project>` only when that project already exists on the hub.

| The principal says | Change |
|---|---|
| "name it X" | `--name X` |
| "scope it to project P" | `--project P` |
| "only these namespaces" | `--namespace a --namespace b` (cluster-level resources are then ignored unless `--cluster-resources`) |
| "replace the existing one" | `--upsert`, after confirming which Secret it replaces |
| "use the token way" | drop the `--exec-command*` flags, only on the principal's explicit decision: it installs `argocd-manager` with cluster-level privileges on the target |

## Verify

```bash
argocd cluster list                                       # the row, twice a few minutes apart
kubectl -n <ns> get secret -l argocd.argoproj.io/secret-type=cluster -o json \
  | jq -r '.items[] | [.metadata.name, (.data|keys|join(",")),
      (.data.config|@base64d|fromjson
        | (if .bearerToken then "bearerToken" else "no-bearerToken" end)
          + " exec=" + (.execProviderConfig.command // "-")
          + " envKeys=" + ((.execProviderConfig.env // {})|keys|join("|")))] | @tsv'
```

The `jq` filter prints key names and shape only. Never print `.data.config` itself.

- A version and `Successful` on the first read is evidence the hub obtained a token and reached
  the target's API. `Unknown` with "Cluster has no applications and is not being monitored"
  afterwards is the resting state.
- `Failed` means the credential or the network path: read the row's message and the application
  controller log.
- The registration is proven to reconcile only by the first Application's `argocd app diff`.

## Report

State: the command that ran (ids elided), its output line, both `cluster list` reads, the Secret
shape, each preflight row with its result, what was not verified and why, the account each read
ran as, and the standing consequences (not in Git; one path per cluster; any Git-managed
registration that must now stay unsynced or be removed).
