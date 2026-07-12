# Git Repositories API Reference

Comprehensive reference for Azure DevOps Git REST API operations.

## Table of Contents

- [Repository Concepts](#repository-concepts)
- [Pull Request Operations](#pull-request-operations)
- [Branch Policies](#branch-policies)
- [Git Refs and Commits](#git-refs-and-commits)
- [Code Review](#code-review)

---

## Repository Concepts

### Repository Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | GUID | Unique repository identifier |
| `name` | String | Repository name |
| `url` | String | API URL |
| `project` | Object | Parent project |
| `defaultBranch` | String | Default branch (refs/heads/main) |
| `size` | Long | Repository size in bytes |
| `remoteUrl` | String | Clone URL |
| `sshUrl` | String | SSH clone URL |
| `webUrl` | String | Web portal URL |
| `isDisabled` | Boolean | Whether repo is disabled |
| `isFork` | Boolean | Whether repo is a fork |

### Ref Format

```
refs/heads/main          # Branch
refs/heads/feature/test  # Feature branch
refs/tags/v1.0.0         # Tag
refs/pull/123/merge      # PR merge ref
```

---

## Pull Request Operations

### PR Status Values

| Status | Description |
|--------|-------------|
| `active` | Open for review |
| `abandoned` | Closed without merge |
| `completed` | Merged |
| `all` | All statuses |

### Merge Strategies

| Strategy | Description |
|----------|-------------|
| `noFastForward` | Create merge commit (default) |
| `squash` | Squash all commits into one |
| `rebase` | Rebase source onto target |
| `rebaseMerge` | Rebase with merge commit |

### PR Vote Values

| Vote | Value | Description |
|------|-------|-------------|
| Approved | `10` | Approved |
| Approved with suggestions | `5` | Approved with comments |
| No vote | `0` | No vote (reset) |
| Waiting for author | `-5` | Needs work |
| Rejected | `-10` | Rejected |

### PR Completion Options

```json
{
  "autoCompleteSetBy": {
    "id": "user-guid"
  },
  "completionOptions": {
    "deleteSourceBranch": true,
    "mergeCommitMessage": "Merged PR #123: Feature description",
    "mergeStrategy": "squash",
    "bypassPolicy": false,
    "bypassReason": "",
    "transitionWorkItems": true,
    "squashMerge": true
  }
}
```

---

## Branch Policies

### Policy Types

| Type ID | Name | Description |
|---------|------|-------------|
| `fa4e907d-c16b-4a4c-9dfa-4916e5d171ab` | Minimum reviewers | Required approvals |
| `c6a1889d-b943-4856-b76f-9e46bb6b0df2` | Work item linking | Require linked work items |
| `0609b952-1397-4640-95ec-e00a01b2c241` | Comment requirements | Resolve all comments |
| `40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e` | Merge strategy | Allowed merge types |
| `7ed39669-655c-494e-b4a0-a08b4da0fcce` | Build validation | Required build to pass |
| `cbdc66da-9728-4af8-aada-9a5a32e4a226` | Status | Required external status |
| `ca93de9d-e26b-4dc5-9e97-4f76a0ff1ae5` | Required reviewers | Auto-add reviewers |
| `fd2167ab-b0be-447a-8ec8-39368250530e` | File size | Max file size restriction |
| `001bf6b8-c251-4a78-b09e-c9b6b3f8b75a` | File path | Path-based restrictions |

### Policy Configuration Example

```json
{
  "isEnabled": true,
  "isBlocking": true,
  "type": {
    "id": "fa4e907d-c16b-4a4c-9dfa-4916e5d171ab"
  },
  "settings": {
    "minimumApproverCount": 2,
    "creatorVoteCounts": false,
    "allowDownvotes": false,
    "resetOnSourcePush": true,
    "scope": [
      {
        "refName": "refs/heads/main",
        "matchKind": "exact",
        "repositoryId": "repo-guid"
      }
    ]
  }
}
```

---

## Git Refs and Commits

### Ref Update Operation

| Operation | Old Object ID | New Object ID |
|-----------|---------------|---------------|
| Create | 0000000...000 | New commit SHA |
| Update | Current SHA | New SHA |
| Delete | Current SHA | 0000000...000 |

### Commit Properties

| Property | Type | Description |
|----------|------|-------------|
| `commitId` | String | Full SHA |
| `author` | GitUserDate | Author info |
| `committer` | GitUserDate | Committer info |
| `comment` | String | Commit message |
| `commentTruncated` | Boolean | Message truncated |
| `changeCounts` | Object | Add/Edit/Delete counts |
| `url` | String | API URL |
| `remoteUrl` | String | Web URL |
| `parents` | Array | Parent commit SHAs |
| `push` | Object | Push details |
| `statuses` | Array | Commit statuses |

### Change Types

| Type | Description |
|------|-------------|
| `add` | New file added |
| `edit` | Existing file modified |
| `delete` | File deleted |
| `rename` | File renamed |
| `sourceRename` | Source of rename |
| `targetRename` | Target of rename |

---

## Code Review

### Thread Status

| Status | Description |
|--------|-------------|
| `Unknown` | Unknown status |
| `Active` | Open thread |
| `Fixed` | Marked as fixed |
| `WontFix` | Won't fix |
| `Closed` | Closed |
| `ByDesign` | By design |
| `Pending` | Pending review |

### Comment Types

| Type | Description |
|------|-------------|
| `Unknown` | Unknown type |
| `Text` | Regular comment |
| `CodeChange` | Code suggestion |
| `System` | System-generated |

### Thread Context

```json
{
  "filePath": "/src/main.cs",
  "rightFileStart": {
    "line": 10,
    "offset": 1
  },
  "rightFileEnd": {
    "line": 15,
    "offset": 50
  },
  "leftFileStart": null,
  "leftFileEnd": null
}
```

---

## MCP Tool Usage Examples

### List Repositories

```python
# Using mcp__ado__repo_list_repos_by_project
params = {
    "project": "MyProject",
    "repoNameFilter": "api",  # Optional filter
    "top": 100
}
```

### Get Repository

```python
# Using mcp__ado__repo_get_repo_by_name_or_id
params = {
    "project": "MyProject",
    "repositoryNameOrId": "my-repo"
}
```

### Create Branch

```python
# Using mcp__ado__repo_create_branch
params = {
    "repositoryId": "repo-guid",
    "branchName": "feature/new-feature",
    "sourceBranchName": "main"
}
```

### List Branches

```python
# Using mcp__ado__repo_list_branches_by_repo
params = {
    "repositoryId": "repo-guid",
    "filterContains": "feature",
    "top": 50
}
```

### Search Commits

```python
# Using mcp__ado__repo_search_commits
params = {
    "project": "MyProject",
    "repository": "my-repo",
    "searchText": "fix bug",
    "author": "developer@company.com",
    "fromDate": "2024-01-01T00:00:00Z",
    "toDate": "2024-12-31T23:59:59Z",
    "includeWorkItems": True,
    "top": 20
}
```

### Create Pull Request

```python
# Using mcp__ado__repo_create_pull_request
params = {
    "repositoryId": "repo-guid",
    "sourceRefName": "refs/heads/feature/new-feature",
    "targetRefName": "refs/heads/main",
    "title": "Add new feature",
    "description": "## Summary\nThis PR adds...\n\n## Testing\n- [ ] Unit tests\n- [ ] Integration tests",
    "isDraft": False,
    "workItems": "12345 12346"  # Space-separated IDs
}
```

### Update Pull Request

```python
# Using mcp__ado__repo_update_pull_request
params = {
    "repositoryId": "repo-guid",
    "pullRequestId": 123,
    "title": "Updated title",
    "description": "Updated description",
    "autoComplete": True,
    "mergeStrategy": "Squash",
    "deleteSourceBranch": True,
    "transitionWorkItems": True
}
```

### Add/Remove Reviewers

```python
# Using mcp__ado__repo_update_pull_request_reviewers
params = {
    "repositoryId": "repo-guid",
    "pullRequestId": 123,
    "reviewerIds": ["user-guid-1", "user-guid-2"],
    "action": "add"  # or "remove"
}
```

### List PR Threads

```python
# Using mcp__ado__repo_list_pull_request_threads
params = {
    "repositoryId": "repo-guid",
    "pullRequestId": 123,
    "top": 100
}
```

### Create Comment Thread

```python
# Using mcp__ado__repo_create_pull_request_thread
params = {
    "repositoryId": "repo-guid",
    "pullRequestId": 123,
    "content": "Please review this logic",
    "filePath": "/src/main.cs",
    "rightFileStartLine": 10,
    "rightFileEndLine": 15,
    "status": "Active"
}
```

### Reply to Comment

```python
# Using mcp__ado__repo_reply_to_comment
params = {
    "repositoryId": "repo-guid",
    "pullRequestId": 123,
    "threadId": 456,
    "content": "Good catch, I'll fix this."
}
```

### Resolve Thread

```python
# Using mcp__ado__repo_resolve_comment
params = {
    "repositoryId": "repo-guid",
    "pullRequestId": 123,
    "threadId": 456
}
```

### Find PRs by Commit

```python
# Using mcp__ado__repo_list_pull_requests_by_commits
params = {
    "project": "MyProject",
    "repository": "my-repo",
    "commits": ["abc123def456", "789ghi012jkl"],
    "queryType": "LastMergeCommit"
}
```

---

## Git URL Patterns

### Clone URLs

```bash
# HTTPS
https://dev.azure.com/{org}/{project}/_git/{repo}

# SSH
git@ssh.dev.azure.com:v3/{org}/{project}/{repo}

# With PAT
https://{pat}@dev.azure.com/{org}/{project}/_git/{repo}
```

### Web URLs

```bash
# Repository home
https://dev.azure.com/{org}/{project}/_git/{repo}

# Specific branch
https://dev.azure.com/{org}/{project}/_git/{repo}?version=GB{branch}

# Specific file
https://dev.azure.com/{org}/{project}/_git/{repo}?path=/path/to/file&version=GB{branch}

# Commit
https://dev.azure.com/{org}/{project}/_git/{repo}/commit/{commitId}

# Pull request
https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{prId}

# Compare
https://dev.azure.com/{org}/{project}/_git/{repo}/branchCompare?baseVersion=GB{base}&targetVersion=GB{target}
```
