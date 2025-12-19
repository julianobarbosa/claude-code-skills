#!/usr/bin/env python3
"""
Azure DevOps Pull Requests - Python Examples

This script demonstrates common PR operations using the Azure DevOps REST API.

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
API_VERSION = "7.2-preview.1"

# Base URL
BASE_URL = f"https://dev.azure.com/{ORG}"


def get_auth_header() -> Dict[str, str]:
    """Generate authorization header from PAT."""
    auth_string = base64.b64encode(f":{PAT}".encode()).decode()
    return {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json"
    }


def list_repositories(name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List repositories in the project.

    Args:
        name_filter: Optional name filter

    Returns:
        List of repositories
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories"
    params = {"api-version": "7.2-preview.1"}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()

    repos = response.json().get("value", [])
    if name_filter:
        repos = [r for r in repos if name_filter.lower() in r["name"].lower()]

    return repos


def get_repository(repo_name_or_id: str) -> Dict[str, Any]:
    """
    Get repository details.

    Args:
        repo_name_or_id: Repository name or ID

    Returns:
        Repository details
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repo_name_or_id}"
    params = {"api-version": "7.2-preview.1"}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json()


def create_branch(
    repository_id: str,
    branch_name: str,
    source_branch: str = "main"
) -> Dict[str, Any]:
    """
    Create a new branch.

    Args:
        repository_id: Repository ID
        branch_name: New branch name
        source_branch: Source branch name

    Returns:
        Created ref
    """
    # First get the source branch commit
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/refs"
    params = {
        "api-version": "7.2-preview.1",
        "filter": f"heads/{source_branch}"
    }

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()

    refs = response.json().get("value", [])
    if not refs:
        raise ValueError(f"Source branch '{source_branch}' not found")

    source_object_id = refs[0]["objectId"]

    # Create the new branch
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/refs"
    params = {"api-version": "7.2-preview.1"}

    body = [
        {
            "name": f"refs/heads/{branch_name}",
            "oldObjectId": "0000000000000000000000000000000000000000",
            "newObjectId": source_object_id
        }
    ]

    response = requests.post(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json().get("value", [{}])[0]


def create_pull_request(
    repository_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: Optional[str] = None,
    reviewers: Optional[List[str]] = None,
    work_item_ids: Optional[List[int]] = None,
    is_draft: bool = False
) -> Dict[str, Any]:
    """
    Create a pull request.

    Args:
        repository_id: Repository ID
        source_branch: Source branch name
        target_branch: Target branch name
        title: PR title
        description: PR description (markdown)
        reviewers: List of reviewer IDs
        work_item_ids: List of work item IDs to link
        is_draft: Create as draft PR

    Returns:
        Created PR
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests"
    params = {"api-version": "7.2-preview.1"}

    # Format branch names
    source_ref = source_branch if source_branch.startswith("refs/") else f"refs/heads/{source_branch}"
    target_ref = target_branch if target_branch.startswith("refs/") else f"refs/heads/{target_branch}"

    body: Dict[str, Any] = {
        "sourceRefName": source_ref,
        "targetRefName": target_ref,
        "title": title,
        "isDraft": is_draft
    }

    if description:
        body["description"] = description

    if reviewers:
        body["reviewers"] = [{"id": r} for r in reviewers]

    if work_item_ids:
        body["workItemRefs"] = [{"id": str(wid)} for wid in work_item_ids]

    response = requests.post(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def list_pull_requests(
    repository_id: str,
    status: str = "active",
    creator_id: Optional[str] = None,
    reviewer_id: Optional[str] = None,
    source_branch: Optional[str] = None,
    target_branch: Optional[str] = None,
    top: int = 50
) -> List[Dict[str, Any]]:
    """
    List pull requests.

    Args:
        repository_id: Repository ID
        status: Filter by status (active, abandoned, completed, all)
        creator_id: Filter by creator
        reviewer_id: Filter by reviewer
        source_branch: Filter by source branch
        target_branch: Filter by target branch
        top: Maximum results

    Returns:
        List of PRs
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests"
    params: Dict[str, Any] = {
        "api-version": "7.2-preview.1",
        "searchCriteria.status": status,
        "$top": top
    }

    if creator_id:
        params["searchCriteria.creatorId"] = creator_id

    if reviewer_id:
        params["searchCriteria.reviewerId"] = reviewer_id

    if source_branch:
        ref = source_branch if source_branch.startswith("refs/") else f"refs/heads/{source_branch}"
        params["searchCriteria.sourceRefName"] = ref

    if target_branch:
        ref = target_branch if target_branch.startswith("refs/") else f"refs/heads/{target_branch}"
        params["searchCriteria.targetRefName"] = ref

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json().get("value", [])


def get_pull_request(repository_id: str, pr_id: int) -> Dict[str, Any]:
    """
    Get pull request details.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID

    Returns:
        PR details
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}"
    params = {"api-version": "7.2-preview.1"}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json()


def update_pull_request(
    repository_id: str,
    pr_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    target_branch: Optional[str] = None,
    auto_complete: Optional[bool] = None,
    merge_strategy: Optional[str] = None,
    delete_source_branch: bool = True
) -> Dict[str, Any]:
    """
    Update a pull request.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID
        title: New title
        description: New description
        status: New status (active, abandoned)
        target_branch: New target branch
        auto_complete: Enable auto-complete
        merge_strategy: noFastForward, squash, rebase, rebaseMerge
        delete_source_branch: Delete source branch on merge

    Returns:
        Updated PR
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}"
    params = {"api-version": "7.2-preview.1"}

    body: Dict[str, Any] = {}

    if title:
        body["title"] = title

    if description:
        body["description"] = description

    if status:
        body["status"] = status

    if target_branch:
        ref = target_branch if target_branch.startswith("refs/") else f"refs/heads/{target_branch}"
        body["targetRefName"] = ref

    if auto_complete is not None:
        if auto_complete:
            # Get current user ID
            me_url = f"https://dev.azure.com/{ORG}/_apis/connectionData"
            me_response = requests.get(me_url, headers=get_auth_header())
            me_response.raise_for_status()
            user_id = me_response.json().get("authenticatedUser", {}).get("id")

            body["autoCompleteSetBy"] = {"id": user_id}
            body["completionOptions"] = {
                "mergeStrategy": merge_strategy or "squash",
                "deleteSourceBranch": delete_source_branch,
                "transitionWorkItems": True
            }
        else:
            body["autoCompleteSetBy"] = None

    response = requests.patch(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def add_reviewers(
    repository_id: str,
    pr_id: int,
    reviewer_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Add reviewers to a PR.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID
        reviewer_ids: List of reviewer identity IDs

    Returns:
        List of added reviewers
    """
    results = []

    for reviewer_id in reviewer_ids:
        url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}/reviewers/{reviewer_id}"
        params = {"api-version": "7.2-preview.1"}

        body = {"vote": 0}  # No vote initially

        response = requests.put(url, headers=get_auth_header(), params=params, json=body)
        response.raise_for_status()
        results.append(response.json())

    return results


def set_vote(
    repository_id: str,
    pr_id: int,
    reviewer_id: str,
    vote: int
) -> Dict[str, Any]:
    """
    Set reviewer vote.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID
        reviewer_id: Reviewer identity ID
        vote: Vote value
            10: Approved
            5: Approved with suggestions
            0: No vote
            -5: Waiting for author
            -10: Rejected

    Returns:
        Updated reviewer
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}/reviewers/{reviewer_id}"
    params = {"api-version": "7.2-preview.1"}

    body = {"vote": vote}

    response = requests.put(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def create_comment_thread(
    repository_id: str,
    pr_id: int,
    content: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    status: str = "active"
) -> Dict[str, Any]:
    """
    Create a comment thread on a PR.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID
        content: Comment content
        file_path: Optional file path for inline comment
        line_number: Optional line number for inline comment
        status: Thread status (active, fixed, wontFix, closed, pending)

    Returns:
        Created thread
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}/threads"
    params = {"api-version": "7.2-preview.1"}

    body: Dict[str, Any] = {
        "comments": [
            {
                "parentCommentId": 0,
                "content": content,
                "commentType": "text"
            }
        ],
        "status": status
    }

    if file_path and line_number:
        body["threadContext"] = {
            "filePath": file_path,
            "rightFileStart": {
                "line": line_number,
                "offset": 1
            },
            "rightFileEnd": {
                "line": line_number,
                "offset": 1
            }
        }

    response = requests.post(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def reply_to_thread(
    repository_id: str,
    pr_id: int,
    thread_id: int,
    content: str
) -> Dict[str, Any]:
    """
    Reply to a comment thread.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID
        thread_id: Thread ID
        content: Reply content

    Returns:
        Created comment
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}/threads/{thread_id}/comments"
    params = {"api-version": "7.2-preview.1"}

    body = {
        "content": content,
        "commentType": "text"
    }

    response = requests.post(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def resolve_thread(
    repository_id: str,
    pr_id: int,
    thread_id: int,
    status: str = "fixed"
) -> Dict[str, Any]:
    """
    Resolve a comment thread.

    Args:
        repository_id: Repository ID
        pr_id: Pull request ID
        thread_id: Thread ID
        status: Resolution status (fixed, wontFix, closed)

    Returns:
        Updated thread
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}/threads/{thread_id}"
    params = {"api-version": "7.2-preview.1"}

    body = {"status": status}

    response = requests.patch(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    # List repositories
    print("Listing repositories...")
    try:
        repos = list_repositories()
        for repo in repos[:5]:
            print(f"  {repo['name']} ({repo['id']})")
    except Exception as e:
        print(f"Error: {e}")

    # List active PRs
    print("\nActive pull requests...")
    try:
        if repos:
            prs = list_pull_requests(repos[0]["id"], status="active", top=5)
            for pr in prs:
                print(f"  #{pr['pullRequestId']}: {pr['title']}")
                print(f"    {pr['sourceRefName']} -> {pr['targetRefName']}")
    except Exception as e:
        print(f"Error: {e}")

    # Create a PR (example)
    print("\nCreating PR...")
    try:
        repo_id = repos[0]["id"] if repos else "your-repo-id"
        new_pr = create_pull_request(
            repository_id=repo_id,
            source_branch="feature/my-feature",
            target_branch="main",
            title="Add new feature",
            description="""## Summary
This PR adds a new feature.

## Changes
- Added feature X
- Updated tests

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
""",
            is_draft=True
        )
        print(f"Created PR #{new_pr['pullRequestId']}")
    except Exception as e:
        print(f"Error (expected if branch doesn't exist): {e}")
