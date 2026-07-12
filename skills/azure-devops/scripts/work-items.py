#!/usr/bin/env python3
"""
Azure DevOps Work Items - Python Examples

This script demonstrates common work item operations using the Azure DevOps REST API.
These examples can be used as templates for automation scripts.

Prerequisites:
    pip install requests

Environment Variables:
    AZURE_DEVOPS_ORG: Organization name
    AZURE_DEVOPS_PAT: Personal Access Token
    AZURE_DEVOPS_PROJECT: Project name
"""

import os
import base64
import json
import requests
from typing import Optional, List, Dict, Any

# Configuration
ORG = os.getenv("AZURE_DEVOPS_ORG", "your-org")
PAT = os.getenv("AZURE_DEVOPS_PAT", "your-pat")
PROJECT = os.getenv("AZURE_DEVOPS_PROJECT", "your-project")
API_VERSION = "7.2-preview.3"

# Base URL
BASE_URL = f"https://dev.azure.com/{ORG}"


def get_auth_header() -> Dict[str, str]:
    """Generate authorization header from PAT."""
    auth_string = base64.b64encode(f":{PAT}".encode()).decode()
    return {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json-patch+json"
    }


def get_work_item(work_item_id: int, expand: str = "all") -> Dict[str, Any]:
    """
    Get a single work item by ID.

    Args:
        work_item_id: The work item ID
        expand: Expansion options (all, fields, links, none, relations)

    Returns:
        Work item data
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/{work_item_id}"
    params = {
        "api-version": API_VERSION,
        "$expand": expand
    }

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json()


def get_work_items_batch(ids: List[int], fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get multiple work items by IDs.

    Args:
        ids: List of work item IDs (max 200)
        fields: Optional list of fields to return

    Returns:
        List of work items
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitemsbatch"
    params = {"api-version": API_VERSION}

    body = {"ids": ids[:200]}  # Max 200 per request
    if fields:
        body["fields"] = fields

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    response = requests.post(url, headers=headers, params=params, json=body)
    response.raise_for_status()
    return response.json().get("value", [])


def create_work_item(
    work_item_type: str,
    title: str,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    additional_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new work item.

    Args:
        work_item_type: Type (Bug, Task, User Story, etc.)
        title: Work item title
        description: HTML description
        assigned_to: Email or display name
        area_path: Area path
        iteration_path: Iteration path
        additional_fields: Additional field values

    Returns:
        Created work item
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/${work_item_type}"
    params = {"api-version": API_VERSION}

    # Build JSON Patch document
    operations = [
        {"op": "add", "path": "/fields/System.Title", "value": title}
    ]

    if description:
        operations.append({
            "op": "add",
            "path": "/fields/System.Description",
            "value": description
        })

    if assigned_to:
        operations.append({
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": assigned_to
        })

    if area_path:
        operations.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path
        })

    if iteration_path:
        operations.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path
        })

    if additional_fields:
        for field, value in additional_fields.items():
            operations.append({
                "op": "add",
                "path": f"/fields/{field}",
                "value": value
            })

    response = requests.post(url, headers=get_auth_header(), params=params, json=operations)
    response.raise_for_status()
    return response.json()


def update_work_item(work_item_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a work item's fields.

    Args:
        work_item_id: Work item ID
        updates: Dictionary of field reference names to values

    Returns:
        Updated work item
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/{work_item_id}"
    params = {"api-version": API_VERSION}

    operations = [
        {"op": "add", "path": f"/fields/{field}", "value": value}
        for field, value in updates.items()
    ]

    response = requests.patch(url, headers=get_auth_header(), params=params, json=operations)
    response.raise_for_status()
    return response.json()


def add_work_item_comment(work_item_id: int, comment: str) -> Dict[str, Any]:
    """
    Add a comment to a work item.

    Args:
        work_item_id: Work item ID
        comment: Comment text (supports HTML)

    Returns:
        Created comment
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/{work_item_id}/comments"
    params = {"api-version": "7.2-preview.4"}

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    body = {"text": comment}

    response = requests.post(url, headers=headers, params=params, json=body)
    response.raise_for_status()
    return response.json()


def link_work_items(
    source_id: int,
    target_id: int,
    link_type: str = "System.LinkTypes.Related"
) -> Dict[str, Any]:
    """
    Link two work items together.

    Args:
        source_id: Source work item ID
        target_id: Target work item ID
        link_type: Link type reference name
            - System.LinkTypes.Hierarchy-Forward (parent -> child)
            - System.LinkTypes.Hierarchy-Reverse (child -> parent)
            - System.LinkTypes.Related
            - System.LinkTypes.Dependency-Forward (predecessor -> successor)
            - System.LinkTypes.Dependency-Reverse (successor -> predecessor)

    Returns:
        Updated source work item
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/{source_id}"
    params = {"api-version": API_VERSION}

    target_url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/{target_id}"

    operations = [
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": link_type,
                "url": target_url,
                "attributes": {
                    "comment": "Linked via API"
                }
            }
        }
    ]

    response = requests.patch(url, headers=get_auth_header(), params=params, json=operations)
    response.raise_for_status()
    return response.json()


def run_wiql_query(wiql: str) -> List[Dict[str, Any]]:
    """
    Execute a WIQL query and return work items.

    Args:
        wiql: WIQL query string

    Returns:
        List of work items matching the query
    """
    # Execute query to get IDs
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/wiql"
    params = {"api-version": API_VERSION}

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    body = {"query": wiql}

    response = requests.post(url, headers=headers, params=params, json=body)
    response.raise_for_status()

    result = response.json()

    # Extract IDs and fetch full work items
    if "workItems" in result:
        ids = [wi["id"] for wi in result["workItems"]]
        if ids:
            return get_work_items_batch(ids)

    return []


def add_artifact_link(
    work_item_id: int,
    artifact_uri: str,
    link_type: str = "ArtifactLink",
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add an artifact link to a work item.

    Args:
        work_item_id: Work item ID
        artifact_uri: VSTFS artifact URI
            Examples:
            - Branch: vstfs:///Git/Ref/{projectId}/{repoId}/GB{branchName}
            - Commit: vstfs:///Git/Commit/{projectId}/{repoId}/{commitId}
            - PR: vstfs:///Git/PullRequestId/{projectId}/{prId}
            - Build: vstfs:///Build/Build/{projectId}/{buildId}
        link_type: Link type name
        comment: Optional comment

    Returns:
        Updated work item
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/wit/workitems/{work_item_id}"
    params = {"api-version": API_VERSION}

    link_value = {
        "rel": link_type,
        "url": artifact_uri
    }

    if comment:
        link_value["attributes"] = {"comment": comment}

    operations = [
        {
            "op": "add",
            "path": "/relations/-",
            "value": link_value
        }
    ]

    response = requests.patch(url, headers=get_auth_header(), params=params, json=operations)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    # Example: Get a work item
    print("Getting work item #1...")
    try:
        item = get_work_item(1)
        print(f"Title: {item['fields'].get('System.Title')}")
        print(f"State: {item['fields'].get('System.State')}")
    except Exception as e:
        print(f"Error: {e}")

    # Example: Run WIQL query
    print("\nQuerying active bugs...")
    query = """
    SELECT [System.Id], [System.Title], [System.State]
    FROM workitems
    WHERE [System.TeamProject] = @project
      AND [System.WorkItemType] = 'Bug'
      AND [System.State] = 'Active'
    ORDER BY [System.CreatedDate] DESC
    """
    try:
        bugs = run_wiql_query(query)
        for bug in bugs[:5]:
            print(f"  #{bug['id']}: {bug['fields'].get('System.Title')}")
    except Exception as e:
        print(f"Error: {e}")

    # Example: Create work item
    print("\nCreating new task...")
    try:
        new_task = create_work_item(
            work_item_type="Task",
            title="API Integration Task",
            description="<p>Implement API integration for new feature</p>",
            additional_fields={
                "Microsoft.VSTS.Common.Priority": 2,
                "Microsoft.VSTS.Scheduling.RemainingWork": 8
            }
        )
        print(f"Created: #{new_task['id']}")
    except Exception as e:
        print(f"Error: {e}")
