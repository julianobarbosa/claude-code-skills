---
name: argocd-aks-cluster-registration
version: 1.0.0
description: "Register a private AKS cluster on a hub Argo CD with `argocd cluster add` in exec-provider form (argocd-k8s-auth azure, Entra workload identity, no ServiceAccount token), prove the registration, then point a workload at it by destination name. USE WHEN add a cluster to ArgoCD, register AKS in ArgoCD, argocd cluster add, Settings Clusters only shows in-cluster, hub ArgoCD cannot see a cluster, deploy to another cluster from the hub, argocd-k8s-auth azure, cluster status Unknown. NOT FOR installing Argo CD, authoring the Terraform identity, or opening the PR (use ship)."
argument-hint: [target cluster, and the name it should carry in Argo CD]
---

# ArgocdAksClusterRegistration

Gets a private AKS cluster from "not in Settings → Clusters" to "registered on the hub Argo CD
with a secretless credential", and then to "an Application targets it by name". The hub's own
workload identity is the credential, so nothing long-lived is stored and nothing is installed on
the managed cluster.

## Customization

**Before executing, check for user customizations at:**
`~/.claude/lifeos/USER/CUSTOMIZATIONS/SKILLS/ArgocdAksClusterRegistration/`

If this directory exists, load and apply any PREFERENCES.md or Config found there (cluster and
resource-group names, the Terraform output that carries the ids, the hub hostname, naming
conventions). These override the placeholders in the workflows.

## Voice Notification

**When executing a workflow, do BOTH:**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:31337/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running WORKFLOWNAME in ArgocdAksClusterRegistration"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running **WorkflowName** in **ArgocdAksClusterRegistration**...
   ```

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **RegisterCluster** | "add the cluster to ArgoCD", "argocd cluster add", "only in-cluster is listed", "register AKS on the hub" | `Workflows/RegisterCluster.md` |
| **TargetWorkload** | "deploy this app to the new cluster", "point the Application at it", "destination is in-cluster but should be the other cluster" | `Workflows/TargetWorkload.md` |

## What done looks like

- The cluster is listed by `argocd cluster list` under the agreed name, and its Secret holds an
  `execProviderConfig` and no `bearerToken`.
- Exactly one cluster Secret exists for that API server URL.
- The identity ids never appeared in the transcript, shell history, Git, or a pod spec.
- The report says which claims were read live and which were not, and names the account each
  read ran as.
- For a workload: the Application's destination is `name: <cluster name>`, its project allows
  that destination, and its first sync is a deliberate `diff` then `sync`.

## The three ways to add a cluster

| | CLI, ServiceAccount token | CLI, exec provider | Declarative Secret |
|---|---|---|---|
| Command | `argocd cluster add <ctx>` | `argocd cluster add <ctx> --exec-command …` | a Secret labelled `argocd.argoproj.io/secret-type: cluster` |
| Lands on the managed cluster | ServiceAccount `argocd-manager` with cluster-level privileges | nothing | nothing |
| Stored credential | long-lived bearer token | none; a token is minted per call | none; same as exec provider |
| In Git | no | no | yes, when the Secret is produced from a vault or a manifest |

The CLI decides between the first two by one flag: with `--exec-command` set it skips the
ServiceAccount install entirely (`cmd/argocd/commands/cluster.go`, the `switch` before
`InstallClusterManagerRBAC`). This skill uses the exec-provider form. The token form needs the
principal's explicit decision, because it puts a standing cluster-admin token for the managed
cluster on the hub.

## Safety gates

- Registering a cluster gives the hub the power to change it. Confirm the target cluster and the
  name with the principal before running `argocd cluster add`, and treat a production target as
  an auth change that is called out in whatever records the work.
- One registration path per cluster. Before adding, list existing cluster Secrets and any
  Git-managed registration for the same server; if one exists, stop and ask which path wins.
- Never print the client id or tenant id. Read them into a variable from their source of record
  and pass them by variable. Redact stderr of every vault call (see Gotchas).
- `argocd cluster rm` while Applications target the cluster leaves them unable to reconcile. For
  a pause, annotate the Secret with `argocd.argoproj.io/skip-reconcile=true` instead.

## Examples

**Example 1: the cluster is missing from Settings → Clusters**
```
User: "ArgoCD only shows in-cluster, we need the prd cluster there"
→ Invokes RegisterCluster
→ Preflight: federated credentials, role assignment, token mount, helper binary, DNS from the hub
→ argocd cluster add in exec-provider form, ids passed by variable
→ Reports the cluster list row, the Secret's shape, and what was not verified
```

**Example 2: an Application deploys to the hub instead of the new cluster**
```
User: "this app's destination is in-cluster, it should go to the new cluster"
→ Invokes TargetWorkload
→ Explains whether that Application is the registration itself (in-cluster is right) or a workload
→ Writes the project destination and the Application with destination.name, parked until its
  values have no open placeholders
```

**Example 3: the cluster reads Unknown after a successful add**
```
User: "it was added but the status is Unknown"
→ RegisterCluster, verification section
→ "Cluster has no applications and is not being monitored" is the resting state; the first
  Application's diff is the real connectivity proof
```

## Gotchas

- **A cluster with no Applications reads `Unknown`.** Right after `cluster add` the row can show a
  version and `Successful` (the API server validated the connection), then it settles to `Unknown`
  with the message "Cluster has no applications and is not being monitored". Neither state is a
  failure.
- **The kubeconfig decides the server URL the hub will use.** The CLI copies `server` and the CA
  from the kubeconfig into the Secret. For a private cluster reached through a hub-side private
  endpoint, fetch credentials WITHOUT `--public-fqdn`: the public name resolves to an address the
  hub cannot route to, and the registration then fails only when the first Application syncs.
- **In exec-provider mode the CLI never contacts the managed cluster.** The operator needs the
  kubeconfig entry, not network access or privileges on that cluster. All real checks happen from
  the hub, so preflight runs there.
- **`--name` is the contract.** Projects and Applications address the cluster by this name.
  Without it the cluster takes the kubeconfig context name. Agree the name first; changing it later
  means editing every project destination.
- **The token mount is the usual missing piece.** `argocd-k8s-auth azure` with
  `AAD_LOGIN_METHOD=workloadidentity` reads a projected ServiceAccount token (audience
  `api://AzureADTokenExchange`). It must be mounted on BOTH `argocd-server` and the application
  controller, and each needs its own federated credential (subjects
  `system:serviceaccount:<ns>:argocd-server` and `…:argocd-application-controller`).
- **Two registrations for one server are a duplicate.** A Git-managed registration Application
  left unsynced beside a CLI registration is a trap: syncing it later creates the second Secret.
- **A CLI registration is not in Git.** A hub rebuild loses it. Say so in the report, and record
  the exact command where the team keeps runbooks.
- **Which `az` account is signed in decides what can be read.** A control-plane Owner often holds
  no vault data-plane role and no rights inside the hub cluster. Check `az account show` before
  concluding a secret or an object is missing; `Forbidden` and "not found" look alike in a filtered
  listing.
- **`az keyvault` RBAC errors print ids.** A `ForbiddenByRbac` message carries the tenant id, the
  subscription id and the caller's object id. Pipe stderr of vault calls through a GUID redaction.
- **Terraform that talks to a private cluster needs its private name to resolve.** A VPN client
  that cannot resolve the `privatelink` name fails a plan with "no such host" while the public name
  answers. One hosts-file line mapping the private name to the address the public name resolves to
  unblocks it.
- **The vault identity for a SecretProviderClass is whichever identity holds the role.** On one
  cluster that is the CSI add-on identity, on another the kubelet identity. Read the role
  assignments on the vault before filling `userAssignedIdentityID`.
- **CLI and server versions can differ.** Check the flags against the server's version, not only
  the local `--help`.
