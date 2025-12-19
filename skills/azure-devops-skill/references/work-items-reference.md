# Work Item Tracking API Reference

Comprehensive reference for Azure DevOps Work Item Tracking REST API operations.

## Table of Contents

- [Work Item Fields](#work-item-fields)
- [Work Item Types](#work-item-types)
- [WIQL Reference](#wiql-reference)
- [Link Types](#link-types)
- [State Transitions](#state-transitions)

---

## Work Item Fields

### System Fields

| Field | Reference Name | Type | Description |
|-------|----------------|------|-------------|
| ID | `System.Id` | Integer | Unique work item identifier |
| Title | `System.Title` | String | Work item title (required) |
| State | `System.State` | String | Current state |
| Reason | `System.Reason` | String | Reason for state change |
| Assigned To | `System.AssignedTo` | Identity | Assigned user |
| Area Path | `System.AreaPath` | TreePath | Area classification |
| Iteration Path | `System.IterationPath` | TreePath | Sprint/iteration |
| Work Item Type | `System.WorkItemType` | String | Type (Bug, Task, etc.) |
| Created Date | `System.CreatedDate` | DateTime | Creation timestamp |
| Created By | `System.CreatedBy` | Identity | Creator |
| Changed Date | `System.ChangedDate` | DateTime | Last modified timestamp |
| Changed By | `System.ChangedBy` | Identity | Last modifier |
| Tags | `System.Tags` | String | Semicolon-separated tags |
| Description | `System.Description` | HTML | Detailed description |
| History | `System.History` | History | Discussion/comments |
| Rev | `System.Rev` | Integer | Revision number |
| Team Project | `System.TeamProject` | String | Project name |
| Board Column | `System.BoardColumn` | String | Kanban board column |
| Board Lane | `System.BoardLane` | String | Kanban board lane |

### Scheduling Fields

| Field | Reference Name | Type | Description |
|-------|----------------|------|-------------|
| Story Points | `Microsoft.VSTS.Scheduling.StoryPoints` | Double | Agile story points |
| Effort | `Microsoft.VSTS.Scheduling.Effort` | Double | Effort estimate |
| Remaining Work | `Microsoft.VSTS.Scheduling.RemainingWork` | Double | Hours remaining |
| Original Estimate | `Microsoft.VSTS.Scheduling.OriginalEstimate` | Double | Initial estimate |
| Completed Work | `Microsoft.VSTS.Scheduling.CompletedWork` | Double | Hours completed |
| Start Date | `Microsoft.VSTS.Scheduling.StartDate` | DateTime | Planned start |
| Finish Date | `Microsoft.VSTS.Scheduling.FinishDate` | DateTime | Planned finish |
| Target Date | `Microsoft.VSTS.Scheduling.TargetDate` | DateTime | Target completion |

### Bug-Specific Fields

| Field | Reference Name | Type | Description |
|-------|----------------|------|-------------|
| Repro Steps | `Microsoft.VSTS.TCM.ReproSteps` | HTML | Steps to reproduce |
| System Info | `Microsoft.VSTS.TCM.SystemInfo` | HTML | System information |
| Found In | `Microsoft.VSTS.Build.FoundIn` | String | Build where found |
| Integration Build | `Microsoft.VSTS.Build.IntegrationBuild` | String | Fix build |
| Severity | `Microsoft.VSTS.Common.Severity` | String | Bug severity |
| Priority | `Microsoft.VSTS.Common.Priority` | Integer | Priority (1-4) |

### Custom Field Pattern

Custom fields follow the pattern: `Custom.{FieldName}`

---

## Work Item Types

### Agile Process Template

| Type | Purpose | Parent Type |
|------|---------|-------------|
| Epic | Large initiative | - |
| Feature | Product capability | Epic |
| User Story | User requirement | Feature |
| Task | Implementation work | User Story |
| Bug | Defect | User Story/Feature |
| Issue | Impediment | - |
| Test Case | Test scenario | - |

### Scrum Process Template

| Type | Purpose | Parent Type |
|------|---------|-------------|
| Epic | Large initiative | - |
| Feature | Product capability | Epic |
| Product Backlog Item | Backlog item | Feature |
| Task | Sprint task | Product Backlog Item |
| Bug | Defect | Product Backlog Item |
| Impediment | Blocker | - |
| Test Case | Test scenario | - |

### CMMI Process Template

| Type | Purpose | Parent Type |
|------|---------|-------------|
| Epic | Large initiative | - |
| Feature | Product capability | Epic |
| Requirement | Formal requirement | Feature |
| Task | Implementation task | Requirement |
| Bug | Defect | Requirement |
| Change Request | Change proposal | - |
| Issue | Problem | - |
| Review | Review item | - |
| Risk | Risk item | - |
| Test Case | Test scenario | - |

---

## WIQL Reference

### Query Syntax

```sql
SELECT [Field1], [Field2], ...
FROM workitems | workitemLinks
WHERE [Conditions]
ORDER BY [Field] [ASC|DESC]
ASOF [DateTime]
MODE [Options]
```

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `[System.State] = 'Active'` |
| `<>` | Not equals | `[System.State] <> 'Closed'` |
| `>` | Greater than | `[System.Priority] > 2` |
| `<` | Less than | `[Microsoft.VSTS.Scheduling.RemainingWork] < 8` |
| `>=` | Greater or equal | `[System.CreatedDate] >= @Today - 7` |
| `<=` | Less or equal | `[System.ChangedDate] <= @Today` |
| `IN` | In list | `[System.State] IN ('Active', 'New')` |
| `NOT IN` | Not in list | `[System.WorkItemType] NOT IN ('Task')` |
| `CONTAINS` | Contains text | `[System.Title] CONTAINS 'API'` |
| `NOT CONTAINS` | Not contains | `[System.Description] NOT CONTAINS 'deprecated'` |
| `UNDER` | Under tree path | `[System.AreaPath] UNDER 'Project\Team'` |
| `NOT UNDER` | Not under path | `[System.IterationPath] NOT UNDER 'Project\Archive'` |
| `IN GROUP` | In group | `[System.AssignedTo] IN GROUP '[Team]'` |
| `WAS EVER` | Was ever value | `[System.AssignedTo] WAS EVER @Me` |

### Macros

| Macro | Description |
|-------|-------------|
| `@Me` | Current authenticated user |
| `@Today` | Today's date (midnight) |
| `@Today - N` | N days before today |
| `@Today + N` | N days after today |
| `@Project` | Current project |
| `@CurrentIteration` | Current team iteration |
| `@CurrentIteration + N` | N iterations ahead |
| `@CurrentIteration - N` | N iterations behind |
| `@TeamAreas` | Team's area paths |
| `@StartOfDay` | Start of today |
| `@StartOfWeek` | Start of current week |
| `@StartOfMonth` | Start of current month |
| `@StartOfYear` | Start of current year |
| `@RecentProjectActivity` | Recent activity filter |
| `@follows` | Items user follows |
| `@MyRecentActivity` | User's recent activity |
| `@RecentMentions` | Recent @mentions |

### Link Query Modes

| Mode | Description |
|------|-------------|
| `MustContain` | Links must contain specified items |
| `MayContain` | Links may contain specified items |
| `DoesNotContain` | Links must not contain specified items |
| `Recursive` | Follow links recursively |
| `ReturnMatchingChildren` | Return only matching children |

### Example Queries

```sql
-- Active bugs assigned to me, high priority
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Severity]
FROM workitems
WHERE [System.TeamProject] = @Project
  AND [System.WorkItemType] = 'Bug'
  AND [System.State] = 'Active'
  AND [System.AssignedTo] = @Me
  AND [Microsoft.VSTS.Common.Priority] <= 2
ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.CreatedDate] DESC

-- Items changed in last week
SELECT [System.Id], [System.Title], [System.ChangedDate], [System.ChangedBy]
FROM workitems
WHERE [System.TeamProject] = @Project
  AND [System.ChangedDate] >= @Today - 7
ORDER BY [System.ChangedDate] DESC

-- Current sprint work items
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM workitems
WHERE [System.TeamProject] = @Project
  AND [System.IterationPath] = @CurrentIteration
  AND [System.WorkItemType] IN ('User Story', 'Task', 'Bug')
ORDER BY [System.State], [System.AssignedTo]

-- Parent-child hierarchy
SELECT [Source].[System.Id], [Source].[System.Title],
       [Target].[System.Id], [Target].[System.Title]
FROM workitemLinks
WHERE [Source].[System.TeamProject] = @Project
  AND [Source].[System.WorkItemType] = 'User Story'
  AND [System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward'
  AND [Target].[System.WorkItemType] = 'Task'
MODE (MustContain)
```

---

## Link Types

### Standard Link Types

| Display Name | Forward Ref | Reverse Ref |
|-------------|-------------|-------------|
| Parent/Child | `System.LinkTypes.Hierarchy-Forward` | `System.LinkTypes.Hierarchy-Reverse` |
| Related | `System.LinkTypes.Related` | `System.LinkTypes.Related` |
| Predecessor/Successor | `System.LinkTypes.Dependency-Forward` | `System.LinkTypes.Dependency-Reverse` |
| Duplicate/Duplicate Of | `System.LinkTypes.Duplicate-Forward` | `System.LinkTypes.Duplicate-Reverse` |
| Tested By/Tests | `Microsoft.VSTS.Common.TestedBy-Forward` | `Microsoft.VSTS.Common.TestedBy-Reverse` |
| Test Case/Shared Steps | `Microsoft.VSTS.TestCase.SharedStepReferencedBy` | `Microsoft.VSTS.TestCase.SharedStepReferencedBy-Reverse` |
| Affects/Affected By | `Microsoft.VSTS.Common.Affects-Forward` | `Microsoft.VSTS.Common.Affects-Reverse` |

### External Link Types

| Link Type | Description |
|-----------|-------------|
| `ArtifactLink` | Link to build, release, or other artifact |
| `Hyperlink` | Link to external URL |
| `Storyboard` | Link to storyboard |
| `Remote Work Item Link` | Cross-organization link |
| `GitHub Commit` | GitHub commit link |
| `GitHub Pull Request` | GitHub PR link |

### VSTFS Link URIs

```
# Branch
vstfs:///Git/Ref/{projectId}/{repositoryId}/GB{branchName}

# Commit
vstfs:///Git/Commit/{projectId}/{repositoryId}/{commitId}

# Pull Request
vstfs:///Git/PullRequestId/{projectId}/{pullRequestId}

# Build
vstfs:///Build/Build/{projectId}/{buildId}

# Release
vstfs:///ReleaseManagement/ReleaseEnvironment/{projectId}/{releaseId}:{environmentId}
```

---

## State Transitions

### Agile Bug States

```
New → Active → Resolved → Closed
         ↓         ↓
      Removed   Removed
```

### Agile User Story States

```
New → Active → Resolved → Closed
         ↓
      Removed
```

### Agile Task States

```
New → Active → Closed
         ↓
      Removed
```

### State Reasons

| From State | To State | Reason |
|------------|----------|--------|
| New | Active | Approved, Investigation |
| Active | Resolved | Fixed, As Designed, Deferred |
| Resolved | Active | Not Fixed, Test Failed |
| Resolved | Closed | Verified |
| Active | Closed | Cut, Completed |
| Any | Removed | Removed from backlog |

---

## MCP Tool Usage Examples

### Get Work Item

```python
# Using mcp__ado__wit_get_work_item
params = {
    "project": "MyProject",
    "id": 12345,
    "expand": "relations",  # Include links
    "fields": ["System.Id", "System.Title", "System.State"]
}
```

### Create Work Item

```python
# Using mcp__ado__wit_create_work_item
params = {
    "project": "MyProject",
    "workItemType": "Bug",
    "fields": [
        {"name": "System.Title", "value": "Login button not working"},
        {"name": "System.Description", "value": "Users cannot click the login button"},
        {"name": "Microsoft.VSTS.Common.Severity", "value": "2 - High"},
        {"name": "System.AssignedTo", "value": "user@company.com"}
    ]
}
```

### Update Work Item

```python
# Using mcp__ado__wit_update_work_item
params = {
    "id": 12345,
    "updates": [
        {"op": "add", "path": "/fields/System.State", "value": "Active"},
        {"op": "add", "path": "/fields/System.AssignedTo", "value": "dev@company.com"}
    ]
}
```

### Link Work Items

```python
# Using mcp__ado__wit_work_items_link
params = {
    "project": "MyProject",
    "updates": [
        {"id": 12345, "linkToId": 12346, "type": "child"},
        {"id": 12345, "linkToId": 12347, "type": "related"}
    ]
}
```

### Add Artifact Link

```python
# Using mcp__ado__wit_add_artifact_link
params = {
    "workItemId": 12345,
    "project": "MyProject",
    "linkType": "Branch",
    "projectId": "project-guid",
    "repositoryId": "repo-guid",
    "branchName": "feature/new-feature"
}
```
