# Wiki and Search API Reference

Comprehensive reference for Azure DevOps Wiki and Search REST API operations.

## Table of Contents

- [Wiki Operations](#wiki-operations)
- [Code Search](#code-search)
- [Work Item Search](#work-item-search)
- [Wiki Search](#wiki-search)
- [Search Filters](#search-filters)

---

## Wiki Operations

### Wiki Types

| Type | Description | Storage |
|------|-------------|---------|
| `projectWiki` | Project-scoped wiki | Dedicated Git repo |
| `codeWiki` | Repository-based wiki | Existing Git repo |

### Wiki Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | GUID | Wiki identifier |
| `name` | String | Wiki name |
| `projectId` | GUID | Parent project |
| `repositoryId` | GUID | Backing Git repo |
| `type` | String | projectWiki or codeWiki |
| `mappedPath` | String | Path in repo (codeWiki) |
| `version` | Object | Branch/version info |
| `url` | String | API URL |
| `remoteUrl` | String | Web URL |

### Page Path Format

| Path | Description |
|------|-------------|
| `/` | Root/home page |
| `/Getting-Started` | Top-level page |
| `/Guides/Setup` | Nested page |
| `/API/v1/Users` | Deep nesting |
| `/My%20Page%20Name` | URL-encoded spaces |

### Page Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | Int | Page ID |
| `path` | String | Page path |
| `content` | String | Markdown content |
| `gitItemPath` | String | Git file path |
| `subPages` | Array | Child pages |
| `order` | Int | Sort order |
| `url` | String | API URL |
| `remoteUrl` | String | Web URL |
| `isParentPage` | Boolean | Has children |

### Wiki Markdown Extensions

```markdown
# Standard Markdown
**bold** *italic* `code`

# Azure DevOps Extensions
[[_TOC_]]                    # Table of contents
[[/Page/Path]]               # Wiki page link
[[/Page/Path|Display Text]]  # Named wiki link

# Work Item Links
#1234                        # Work item link
AB#1234                      # Cross-project work item

# Mentions
@<user-guid>                 # User mention
@<group-name>                # Group mention

# Pull Request Links
!123                         # PR link

# Code Snippets
:::code language="csharp" source="path/to/file.cs" range="1-10":::

# Mermaid Diagrams
:::mermaid
graph TD
    A --> B
:::

# Math (LaTeX)
$$E = mc^2$$
$inline math$
```

---

## Code Search

### Search Syntax

| Syntax | Description | Example |
|--------|-------------|---------|
| `keyword` | Simple search | `login` |
| `"exact phrase"` | Exact match | `"public void Login"` |
| `field:value` | Field filter | `repo:MyRepo` |
| `NOT term` | Exclusion | `login NOT test` |
| `term1 AND term2` | Both required | `login AND password` |
| `term1 OR term2` | Either term | `config OR settings` |
| `*` | Wildcard | `log*` matches login, logout |
| `?` | Single char | `te?t` matches test, text |

### Code Search Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `proj:` | Project name | `proj:MyProject` |
| `repo:` | Repository name | `repo:Backend` |
| `path:` | File path | `path:src/api` |
| `file:` | File name | `file:config.json` |
| `ext:` | File extension | `ext:cs` |
| `branch:` | Branch name | `branch:main` |
| `lang:` | Language | `lang:csharp` |

### Code Element Filters

| Filter | Description |
|--------|-------------|
| `class:` | Class definition |
| `struct:` | Struct definition |
| `enum:` | Enum definition |
| `interface:` | Interface definition |
| `method:` | Method/function |
| `property:` | Property definition |
| `field:` | Field definition |
| `comment:` | In comments |
| `string:` | In string literals |

### Example Code Searches

```
# Find class definitions
class:UserService

# Find methods with specific name
method:ValidateCredentials

# Find in specific repo and path
repo:Backend path:src/api login

# Find specific file type
ext:cs "async Task" repo:MyRepo

# Complex query
repo:Backend path:src NOT path:test method:Login
```

---

## Work Item Search

### Work Item Search Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `t:` | Work item type | `t:Bug` |
| `s:` | State | `s:Active` |
| `a:` | Assigned to | `a:@Me` |
| `c:` | Created by | `c:"John Smith"` |
| `project:` | Project | `project:MyProject` |
| `area:` | Area path | `area:"MyProject\Team"` |
| `iteration:` | Iteration | `iteration:@CurrentIteration` |
| `tags:` | Tags | `tags:urgent` |

### Date Filters

| Filter | Description |
|--------|-------------|
| `created:` | Created date |
| `changeddate:` | Last changed |
| `resolveddate:` | Resolved date |
| `closeddate:` | Closed date |

### Date Syntax

```
created:>=2024-01-01
changeddate:<=2024-06-30
created:2024-01-01..2024-03-31
created:@Today-30
```

### Example Work Item Searches

```
# Active bugs assigned to me
t:Bug s:Active a:@Me

# High priority items
t:Task priority:<=2 s:Active

# Recently created in current sprint
created:@Today-7 iteration:@CurrentIteration

# Specific area path
area:"MyProject\Backend Team" t:User Story

# With specific tag
tags:security t:Bug s:Active

# Created by specific user
c:"john.doe@company.com" created:>=2024-01-01
```

---

## Wiki Search

### Wiki Search Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `project:` | Project | `project:MyProject` |
| `wiki:` | Wiki name | `wiki:"Team Wiki"` |
| `path:` | Page path | `path:/Guides` |

### Example Wiki Searches

```
# Search in specific wiki
wiki:"Developer Wiki" API

# Search specific path
path:/Architecture microservices

# Multiple terms
"getting started" installation project:MyProject
```

---

## Search Filters

### Filter Structure (API)

```json
{
  "searchText": "search query",
  "filters": {
    "Project": ["Project1", "Project2"],
    "Repository": ["Repo1"],
    "Path": ["/src"],
    "Branch": ["main", "develop"],
    "CodeElement": ["class", "method"]
  },
  "$skip": 0,
  "$top": 25,
  "$orderBy": [
    {
      "field": "filename",
      "sortOrder": "ASC"
    }
  ]
}
```

### Facets Response

```json
{
  "facets": {
    "Project": [
      {"name": "MyProject", "count": 150},
      {"name": "AnotherProject", "count": 45}
    ],
    "Repository": [
      {"name": "Backend", "count": 100},
      {"name": "Frontend", "count": 50}
    ],
    "CodeElement": [
      {"name": "class", "count": 30},
      {"name": "method", "count": 120}
    ]
  }
}
```

---

## MCP Tool Usage Examples

### List Wikis

```python
# Using mcp__ado__wiki_list_wikis
params = {
    "project": "MyProject"
}
```

### Get Wiki

```python
# Using mcp__ado__wiki_get_wiki
params = {
    "wikiIdentifier": "MyProject.wiki",
    "project": "MyProject"
}
```

### List Wiki Pages

```python
# Using mcp__ado__wiki_list_pages
params = {
    "wikiIdentifier": "MyProject.wiki",
    "project": "MyProject",
    "pageViewsForDays": 7,  # Include view stats
    "top": 50
}
```

### Get Wiki Page Content

```python
# Using mcp__ado__wiki_get_page_content
params = {
    "wikiIdentifier": "MyProject.wiki",
    "project": "MyProject",
    "path": "/Getting-Started/Setup"
}

# Or by URL
params = {
    "url": "https://dev.azure.com/org/project/_wiki/wikis/wiki-name?pagePath=/My%20Page"
}
```

### Create/Update Wiki Page

```python
# Using mcp__ado__wiki_create_or_update_page
params = {
    "wikiIdentifier": "MyProject.wiki",
    "project": "MyProject",
    "path": "/Guides/New-Feature",
    "content": """# New Feature Guide

## Overview
This guide covers the new feature implementation.

## Steps
1. Step one
2. Step two

## Related
- [[/API/Reference]]
- #12345
"""
}
```

### Search Code

```python
# Using mcp__ado__search_code
params = {
    "searchText": "async Task<User> GetUserById",
    "project": ["MyProject"],
    "repository": ["Backend"],
    "path": ["/src"],
    "branch": ["main"],
    "top": 25,
    "includeFacets": True
}
```

### Search Work Items

```python
# Using mcp__ado__search_workitem
params = {
    "searchText": "login authentication",
    "project": ["MyProject"],
    "workItemType": ["Bug", "User Story"],
    "state": ["Active", "New"],
    "assignedTo": ["@Me"],
    "top": 50,
    "includeFacets": True
}
```

### Search Wiki

```python
# Using mcp__ado__search_wiki
params = {
    "searchText": "deployment guide kubernetes",
    "project": ["MyProject"],
    "wiki": ["Team Wiki"],
    "top": 20,
    "includeFacets": True
}
```

---

## Search Response Structure

### Code Search Result

```json
{
  "count": 150,
  "results": [
    {
      "fileName": "UserService.cs",
      "path": "/src/Services/UserService.cs",
      "repository": {
        "name": "Backend",
        "id": "repo-guid"
      },
      "project": {
        "name": "MyProject"
      },
      "versions": [
        {
          "branchName": "main",
          "changeId": "commit-sha"
        }
      ],
      "matches": {
        "content": [
          {
            "charOffset": 100,
            "length": 15
          }
        ]
      },
      "contentId": "blob-sha"
    }
  ],
  "facets": {
    "Project": [...],
    "Repository": [...],
    "CodeElement": [...]
  }
}
```

### Work Item Search Result

```json
{
  "count": 45,
  "results": [
    {
      "project": {
        "name": "MyProject"
      },
      "fields": {
        "system.id": "12345",
        "system.workitemtype": "Bug",
        "system.title": "Login fails with SSO",
        "system.state": "Active",
        "system.assignedto": "user@company.com"
      },
      "hits": [
        {
          "fieldReferenceName": "system.title",
          "highlights": ["Login fails with <highlighttext>SSO</highlighttext>"]
        }
      ],
      "url": "https://dev.azure.com/org/project/_workitems/edit/12345"
    }
  ],
  "facets": {
    "System.WorkItemType": [...],
    "System.State": [...],
    "System.AssignedTo": [...]
  }
}
```

---

## Best Practices

### 1. Use Specific Filters

```
# Bad: Too broad
login

# Good: Specific
repo:Backend path:src/auth class:LoginService method:Validate
```

### 2. Leverage Facets

Use facets to narrow results progressively.

### 3. Quote Exact Phrases

```
"public async Task" vs public async Task
```

### 4. Use Code Element Filters for Code

```
# Find all implementations of interface
class:IUserRepository NOT interface:IUserRepository
```

### 5. Combine Filters

```
t:Bug s:Active a:@Me created:@Today-7 priority:<=2
```
