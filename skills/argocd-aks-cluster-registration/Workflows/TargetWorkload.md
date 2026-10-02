# TargetWorkload

Point a workload at a registered cluster from the hub Argo CD.

## Step 0: Sufficiency check

First decide what the Application in question is. A registration Application (one that creates
the cluster Secret on the hub) correctly has an in-cluster destination; changing it is a mistake.
A workload Application should target the registered cluster by name.

Then check what cannot be invented: image tags, public hostnames, client ids, vault object names,
which ingress class exists on the target. If any is unknown, write the files with a
`REPLACE_WITH_<WHAT>` placeholder and keep them out of the live path. Never fill one with a guess.

## Ideal state

- The Application's destination is `name: <registered cluster name>`, never a server URL.
- A project on the hub lists that destination and only the kinds the workload renders.
- Values live at the path the delivery pipeline already writes to; that path is a contract.
- Nothing goes live on merge while a placeholder or an unmet prerequisite remains.
- The first sync is manual: `argocd app diff`, then `argocd app sync`.

## Shapes (output-format contracts)

Project, written for the hub. Derive the kind list from a render of the charts
(`helm template … | yq -r .kind | sort -u`), then add the kinds the chart renders once optional
features are enabled.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: <project>
  namespace: <argocd namespace>
spec:
  sourceRepos:
    - <approved repo URL>
  destinations:
    - name: <registered cluster name>
      namespace: <workload namespace>
  clusterResourceWhitelist:
    - { group: "", kind: Namespace }        # only for CreateNamespace=true
  namespaceResourceWhitelist:
    - { group: apps, kind: Deployment }     # one entry per rendered kind
```

Application or ApplicationSet template:

```yaml
spec:
  project: <project>
  destination:
    name: <registered cluster name>
    namespace: <workload namespace>
  syncPolicy:                               # no `automated:` until the first sync is proven
    syncOptions:
      - CreateNamespace=true
```

In an ApplicationSet keep two generator fields apart: the registered cluster name (the
destination) and the directory or naming token (values path, Application name). They are often
different strings, and one field doing both jobs breaks the values path when the cluster is named
after the Azure resource.

## Constraints

- An ApplicationSet written for a cluster's own Argo CD cannot be reused on the hub unchanged:
  its `server: https://kubernetes.default.svc` is the hub there.
- Where the hub's root Application syncs a directory non-recursively, a file at that level is
  live on merge. Park unfinished manifests in a subdirectory the root does not read, and activate
  each with a `git mv` in its own change.
- Project first, then the Application: an Application whose project does not exist sits in an
  error state.
- Project roles grant people access to the target cluster's workloads. Leave them empty until the
  groups are decided; the hub's global admins can still operate.
- Removing a generator element or the ApplicationSet must not delete a production workload:
  set `preserveResourcesOnDeletion: true` and no cascade finalizer.

## Prerequisites on the target, to read before promising a sync

| Need | Probe |
|---|---|
| Images exist in the target's registry | list tags with an account that can reach the registry's data plane; a private registry is unreachable off its network |
| Vault objects exist | list names with stderr redacted; check the signed-in account first |
| The right identity reads the vault | role assignments on the vault, matched to the add-on and kubelet identities |
| An ingress controller exists | the cluster's ingress profile, or the IngressClass list |
| Workload identity subject matches | the federated credential's subject equals `system:serviceaccount:<namespace>:<serviceaccount>` in the values |

Report each as verified, failed, or not readable, with the account used.
