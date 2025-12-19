#!/usr/bin/env python3
"""
Azure DevOps Pipelines - Python Examples

This script demonstrates common pipeline operations using the Azure DevOps REST API.

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
import time
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


def list_pipelines(
    name_filter: Optional[str] = None,
    top: int = 100
) -> List[Dict[str, Any]]:
    """
    List pipeline definitions.

    Args:
        name_filter: Optional name filter
        top: Maximum results

    Returns:
        List of pipeline definitions
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/pipelines"
    params = {
        "api-version": API_VERSION,
        "$top": top
    }

    if name_filter:
        params["name"] = name_filter

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json().get("value", [])


def get_pipeline(pipeline_id: int) -> Dict[str, Any]:
    """
    Get pipeline definition details.

    Args:
        pipeline_id: Pipeline ID

    Returns:
        Pipeline definition
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/pipelines/{pipeline_id}"
    params = {"api-version": API_VERSION}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json()


def run_pipeline(
    pipeline_id: int,
    branch: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None,
    template_parameters: Optional[Dict[str, str]] = None,
    stages_to_skip: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Trigger a pipeline run.

    Args:
        pipeline_id: Pipeline ID
        branch: Branch to run (refs/heads/main)
        variables: Pipeline variables
        template_parameters: Template parameters
        stages_to_skip: List of stage names to skip

    Returns:
        Pipeline run details
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/pipelines/{pipeline_id}/runs"
    params = {"api-version": API_VERSION}

    body: Dict[str, Any] = {}

    if branch:
        body["resources"] = {
            "repositories": {
                "self": {
                    "refName": branch if branch.startswith("refs/") else f"refs/heads/{branch}"
                }
            }
        }

    if variables:
        body["variables"] = {
            name: {"value": value, "isSecret": False}
            for name, value in variables.items()
        }

    if template_parameters:
        body["templateParameters"] = template_parameters

    if stages_to_skip:
        body["stagesToSkip"] = stages_to_skip

    response = requests.post(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def get_run(pipeline_id: int, run_id: int) -> Dict[str, Any]:
    """
    Get pipeline run details.

    Args:
        pipeline_id: Pipeline ID
        run_id: Run ID

    Returns:
        Run details
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/pipelines/{pipeline_id}/runs/{run_id}"
    params = {"api-version": API_VERSION}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json()


def list_runs(
    pipeline_id: int,
    top: int = 50
) -> List[Dict[str, Any]]:
    """
    List pipeline runs.

    Args:
        pipeline_id: Pipeline ID
        top: Maximum results

    Returns:
        List of runs
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/pipelines/{pipeline_id}/runs"
    params = {
        "api-version": API_VERSION,
        "$top": top
    }

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json().get("value", [])


def get_build(build_id: int) -> Dict[str, Any]:
    """
    Get build details using Build API.

    Args:
        build_id: Build ID

    Returns:
        Build details
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/build/builds/{build_id}"
    params = {"api-version": "7.2-preview.7"}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json()


def list_builds(
    definition_ids: Optional[List[int]] = None,
    branch_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    result_filter: Optional[str] = None,
    top: int = 50
) -> List[Dict[str, Any]]:
    """
    List builds.

    Args:
        definition_ids: Filter by definition IDs
        branch_name: Filter by branch
        status_filter: Filter by status (inProgress, completed, etc.)
        result_filter: Filter by result (succeeded, failed, etc.)
        top: Maximum results

    Returns:
        List of builds
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/build/builds"
    params: Dict[str, Any] = {
        "api-version": "7.2-preview.7",
        "$top": top,
        "queryOrder": "queueTimeDescending"
    }

    if definition_ids:
        params["definitions"] = ",".join(map(str, definition_ids))

    if branch_name:
        params["branchName"] = branch_name

    if status_filter:
        params["statusFilter"] = status_filter

    if result_filter:
        params["resultFilter"] = result_filter

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json().get("value", [])


def get_build_logs(build_id: int) -> List[Dict[str, Any]]:
    """
    Get list of logs for a build.

    Args:
        build_id: Build ID

    Returns:
        List of log references
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/build/builds/{build_id}/logs"
    params = {"api-version": "7.2-preview.2"}

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json().get("value", [])


def get_build_log_content(
    build_id: int,
    log_id: int,
    start_line: int = 0,
    end_line: Optional[int] = None
) -> str:
    """
    Get log content.

    Args:
        build_id: Build ID
        log_id: Log ID
        start_line: Start line (0-based)
        end_line: End line

    Returns:
        Log content as text
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/build/builds/{build_id}/logs/{log_id}"
    params: Dict[str, Any] = {
        "api-version": "7.2-preview.2",
        "startLine": start_line
    }

    if end_line:
        params["endLine"] = end_line

    headers = get_auth_header()
    headers["Accept"] = "text/plain"

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.text


def retry_build_stage(
    build_id: int,
    stage_name: str,
    force_retry_all_jobs: bool = False
) -> Dict[str, Any]:
    """
    Retry a failed stage.

    Args:
        build_id: Build ID
        stage_name: Stage name to retry
        force_retry_all_jobs: Retry all jobs in stage

    Returns:
        Updated build timeline
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/build/builds/{build_id}/stages/{stage_name}"
    params = {"api-version": "7.2-preview.1"}

    body = {
        "forceRetryAllJobs": force_retry_all_jobs,
        "state": "retry"
    }

    response = requests.patch(url, headers=get_auth_header(), params=params, json=body)
    response.raise_for_status()
    return response.json()


def wait_for_build(
    build_id: int,
    poll_interval: int = 30,
    timeout: int = 3600
) -> Dict[str, Any]:
    """
    Wait for a build to complete.

    Args:
        build_id: Build ID
        poll_interval: Seconds between polls
        timeout: Maximum wait time in seconds

    Returns:
        Final build state

    Raises:
        TimeoutError: If build doesn't complete within timeout
    """
    start_time = time.time()

    while True:
        build = get_build(build_id)
        status = build.get("status")

        if status == "completed":
            return build

        elapsed = time.time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(f"Build {build_id} did not complete within {timeout} seconds")

        print(f"Build {build_id} status: {status}, elapsed: {int(elapsed)}s")
        time.sleep(poll_interval)


def get_build_changes(build_id: int, top: int = 100) -> List[Dict[str, Any]]:
    """
    Get commits associated with a build.

    Args:
        build_id: Build ID
        top: Maximum results

    Returns:
        List of associated changes
    """
    url = f"{BASE_URL}/{PROJECT}/_apis/build/builds/{build_id}/changes"
    params = {
        "api-version": "7.2-preview.2",
        "$top": top
    }

    response = requests.get(url, headers=get_auth_header(), params=params)
    response.raise_for_status()
    return response.json().get("value", [])


# Example usage
if __name__ == "__main__":
    # List pipelines
    print("Listing pipelines...")
    try:
        pipelines = list_pipelines(top=10)
        for p in pipelines:
            print(f"  {p['id']}: {p['name']}")
    except Exception as e:
        print(f"Error: {e}")

    # Get recent builds
    print("\nRecent builds...")
    try:
        builds = list_builds(top=5)
        for b in builds:
            print(f"  #{b['id']}: {b['definition']['name']} - {b.get('status')} / {b.get('result', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")

    # Run a pipeline
    print("\nRunning pipeline...")
    try:
        pipeline_id = 1  # Replace with actual ID
        run = run_pipeline(
            pipeline_id=pipeline_id,
            branch="main",
            variables={"environment": "dev"},
            template_parameters={"runTests": "true"}
        )
        print(f"Started run #{run['id']}, state: {run['state']}")

        # Optionally wait for completion
        # result = wait_for_build(run['id'], poll_interval=30, timeout=1800)
        # print(f"Final result: {result.get('result')}")
    except Exception as e:
        print(f"Error: {e}")

    # Get build logs
    print("\nBuild logs...")
    try:
        build_id = 1  # Replace with actual ID
        logs = get_build_logs(build_id)
        print(f"Found {len(logs)} log files")

        # Get content of first log
        if logs:
            content = get_build_log_content(build_id, logs[0]['id'], end_line=20)
            print(f"First 20 lines of log {logs[0]['id']}:\n{content}")
    except Exception as e:
        print(f"Error: {e}")
