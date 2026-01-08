#!/usr/bin/env python3
"""
Dependency-Track Python Client

A comprehensive Python client for interacting with the Dependency-Track REST API.
Supports all common operations: projects, SBOMs, vulnerabilities, policies.

Requirements:
    pip install requests python-dotenv

Usage:
    from python_client import DependencyTrackClient

    client = DependencyTrackClient(
        base_url="https://dtrack.example.com",
        api_key="your-api-key"
    )

    # List all projects
    projects = client.get_projects()

    # Upload SBOM
    client.upload_sbom("bom.json", project_name="my-app", project_version="1.0.0")
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class VulnerabilitySummary:
    """Summary of vulnerabilities for a project."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unassigned: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.unassigned

    def exceeds_threshold(
        self,
        max_critical: int = 0,
        max_high: int = 0,
        max_medium: int = 0,
        max_low: int = 0
    ) -> bool:
        """Check if vulnerabilities exceed specified thresholds."""
        return (
            self.critical > max_critical or
            self.high > max_high or
            self.medium > max_medium or
            self.low > max_low
        )


@dataclass
class PolicyViolationSummary:
    """Summary of policy violations for a project."""
    fail: int = 0
    warn: int = 0
    info: int = 0

    @property
    def total(self) -> int:
        return self.fail + self.warn + self.info


class DependencyTrackClient:
    """Client for Dependency-Track REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize the Dependency-Track client.

        Args:
            base_url: Base URL of Dependency-Track instance (or DTRACK_URL env var)
            api_key: API key for authentication (or DTRACK_API_KEY env var)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = (base_url or os.getenv("DTRACK_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("DTRACK_API_KEY", "")

        if not self.base_url:
            raise ValueError("base_url or DTRACK_URL environment variable required")
        if not self.api_key:
            raise ValueError("api_key or DTRACK_API_KEY environment variable required")

        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """Make an API request."""
        url = f"{self.base_url}/api/v1{endpoint}"
        response = self.session.request(
            method,
            url,
            timeout=self.timeout,
            verify=self.verify_ssl,
            **kwargs
        )
        response.raise_for_status()
        return response

    def _get(self, endpoint: str, **kwargs) -> Any:
        """Make a GET request and return JSON."""
        return self._request("GET", endpoint, **kwargs).json()

    def _put(self, endpoint: str, **kwargs) -> Any:
        """Make a PUT request and return JSON."""
        return self._request("PUT", endpoint, **kwargs).json()

    def _post(self, endpoint: str, **kwargs) -> Any:
        """Make a POST request and return JSON."""
        return self._request("POST", endpoint, **kwargs).json()

    def _delete(self, endpoint: str, **kwargs) -> None:
        """Make a DELETE request."""
        self._request("DELETE", endpoint, **kwargs)

    # =========================================================================
    # Version / Health
    # =========================================================================
    def get_version(self) -> Dict[str, str]:
        """Get Dependency-Track version information."""
        return self._get("/version")

    def health_check(self) -> bool:
        """Check if Dependency-Track is healthy."""
        try:
            self.get_version()
            return True
        except Exception:
            return False

    # =========================================================================
    # Projects
    # =========================================================================
    def get_projects(
        self,
        name: Optional[str] = None,
        exclude_inactive: bool = False,
        only_root: bool = False,
        page_size: int = 100,
        page_number: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get all projects or filter by name.

        Args:
            name: Filter projects by name
            exclude_inactive: Exclude inactive projects
            only_root: Only return root projects (no children)
            page_size: Number of results per page
            page_number: Page number (1-indexed)
        """
        params = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "excludeInactive": exclude_inactive,
            "onlyRoot": only_root
        }
        if name:
            params["name"] = name

        return self._get("/project", params=params)

    def get_project(self, uuid: str) -> Dict[str, Any]:
        """Get a project by UUID."""
        return self._get(f"/project/{uuid}")

    def get_project_by_name_version(
        self,
        name: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """Look up a project by name and version."""
        try:
            return self._get("/project/lookup", params={"name": name, "version": version})
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def create_project(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parent_uuid: Optional[str] = None,
        active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name
            version: Project version
            description: Project description
            tags: List of tag names
            parent_uuid: UUID of parent project
            active: Whether project is active
        """
        data = {
            "name": name,
            "version": version,
            "active": active
        }

        if description:
            data["description"] = description
        if tags:
            data["tags"] = [{"name": tag} for tag in tags]
        if parent_uuid:
            data["parent"] = {"uuid": parent_uuid}

        return self._put("/project", json=data)

    def delete_project(self, uuid: str) -> None:
        """Delete a project by UUID."""
        self._delete(f"/project/{uuid}")

    def get_project_children(self, uuid: str) -> List[Dict[str, Any]]:
        """Get child projects of a parent project."""
        return self._get(f"/project/{uuid}/children")

    # =========================================================================
    # SBOM / BOM
    # =========================================================================
    def upload_sbom(
        self,
        bom_path: str,
        project_uuid: Optional[str] = None,
        project_name: Optional[str] = None,
        project_version: Optional[str] = None,
        auto_create: bool = True,
        parent_uuid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a CycloneDX SBOM to Dependency-Track.

        Args:
            bom_path: Path to BOM file (JSON or XML)
            project_uuid: UUID of existing project (if known)
            project_name: Project name (required if no UUID)
            project_version: Project version (required if no UUID)
            auto_create: Create project if it doesn't exist
            parent_uuid: UUID of parent project for auto-created projects

        Returns:
            Upload response containing token for tracking
        """
        bom_path = Path(bom_path)
        if not bom_path.exists():
            raise FileNotFoundError(f"BOM file not found: {bom_path}")

        with open(bom_path, "rb") as f:
            bom_content = base64.b64encode(f.read()).decode("utf-8")

        data = {
            "bom": bom_content,
            "autoCreate": auto_create
        }

        if project_uuid:
            data["project"] = project_uuid
        else:
            if not project_name or not project_version:
                raise ValueError("project_name and project_version required when project_uuid not provided")
            data["projectName"] = project_name
            data["projectVersion"] = project_version

        if parent_uuid:
            data["parentUUID"] = parent_uuid

        return self._put("/bom", json=data)

    def upload_sbom_multipart(
        self,
        bom_path: str,
        project_name: str,
        project_version: str,
        auto_create: bool = True
    ) -> Dict[str, Any]:
        """
        Upload SBOM using multipart form data (no base64 encoding needed).
        Useful for very large SBOMs.
        """
        bom_path = Path(bom_path)
        if not bom_path.exists():
            raise FileNotFoundError(f"BOM file not found: {bom_path}")

        # Remove Content-Type header for multipart
        headers = {"X-Api-Key": self.api_key}

        with open(bom_path, "rb") as f:
            files = {"bom": (bom_path.name, f)}
            data = {
                "projectName": project_name,
                "projectVersion": project_version,
                "autoCreate": str(auto_create).lower()
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/bom",
                headers=headers,
                files=files,
                data=data,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()

    def is_bom_processing_complete(self, token: str) -> bool:
        """Check if BOM processing is complete."""
        result = self._get(f"/bom/token/{token}")
        return result.get("processing", True) is False

    def wait_for_bom_processing(
        self,
        token: str,
        timeout_seconds: int = 300,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for BOM processing to complete.

        Args:
            token: Upload token from upload_sbom response
            timeout_seconds: Maximum time to wait
            poll_interval: Seconds between status checks

        Returns:
            True if processing completed, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if self.is_bom_processing_complete(token):
                return True
            time.sleep(poll_interval)
        return False

    def export_sbom(
        self,
        project_uuid: str,
        format: str = "json",
        variant: str = "inventory"
    ) -> str:
        """
        Export a project's SBOM.

        Args:
            project_uuid: Project UUID
            format: Export format (json or xml)
            variant: BOM variant (inventory, withVulnerabilities, vdr, vex)

        Returns:
            SBOM content as string
        """
        params = {"format": format, "variant": variant}
        response = self._request("GET", f"/bom/cyclonedx/project/{project_uuid}", params=params)
        return response.text

    # =========================================================================
    # Vulnerabilities
    # =========================================================================
    def get_project_vulnerabilities(
        self,
        project_uuid: str,
        suppressed: bool = False
    ) -> List[Dict[str, Any]]:
        """Get vulnerabilities for a project."""
        params = {"suppressed": suppressed}
        return self._get(f"/vulnerability/project/{project_uuid}", params=params)

    def get_vulnerability(
        self,
        source: str,
        vuln_id: str
    ) -> Dict[str, Any]:
        """Get vulnerability details by source and ID."""
        return self._get(f"/vulnerability/source/{source}/vuln/{vuln_id}")

    def get_project_metrics(self, project_uuid: str) -> Dict[str, Any]:
        """Get current vulnerability metrics for a project."""
        return self._get(f"/metrics/project/{project_uuid}/current")

    def get_vulnerability_summary(self, project_uuid: str) -> VulnerabilitySummary:
        """Get vulnerability summary for a project."""
        metrics = self.get_project_metrics(project_uuid)
        return VulnerabilitySummary(
            critical=metrics.get("critical", 0),
            high=metrics.get("high", 0),
            medium=metrics.get("medium", 0),
            low=metrics.get("low", 0),
            unassigned=metrics.get("unassigned", 0)
        )

    # =========================================================================
    # Components
    # =========================================================================
    def get_project_components(
        self,
        project_uuid: str,
        page_size: int = 100,
        page_number: int = 1
    ) -> List[Dict[str, Any]]:
        """Get components for a project."""
        params = {"pageSize": page_size, "pageNumber": page_number}
        return self._get(f"/component/project/{project_uuid}", params=params)

    def get_component(self, uuid: str) -> Dict[str, Any]:
        """Get component details by UUID."""
        return self._get(f"/component/{uuid}")

    # =========================================================================
    # Policies
    # =========================================================================
    def get_policies(self) -> List[Dict[str, Any]]:
        """Get all policies."""
        return self._get("/policy")

    def get_policy(self, uuid: str) -> Dict[str, Any]:
        """Get a policy by UUID."""
        return self._get(f"/policy/{uuid}")

    def create_policy(
        self,
        name: str,
        operator: str = "ANY",
        violation_state: str = "FAIL",
        conditions: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new policy.

        Args:
            name: Policy name
            operator: ALL or ANY
            violation_state: FAIL, WARN, or INFO
            conditions: List of policy conditions
        """
        data = {
            "name": name,
            "operator": operator,
            "violationState": violation_state
        }

        if conditions:
            data["policyConditions"] = conditions

        return self._put("/policy", json=data)

    def delete_policy(self, uuid: str) -> None:
        """Delete a policy by UUID."""
        self._delete(f"/policy/{uuid}")

    # =========================================================================
    # Policy Violations
    # =========================================================================
    def get_project_policy_violations(
        self,
        project_uuid: str,
        suppressed: bool = False
    ) -> List[Dict[str, Any]]:
        """Get policy violations for a project."""
        params = {"suppressed": suppressed}
        return self._get(f"/violation/project/{project_uuid}", params=params)

    def get_policy_violation_summary(
        self,
        project_uuid: str
    ) -> PolicyViolationSummary:
        """Get policy violation summary for a project."""
        violations = self.get_project_policy_violations(project_uuid)

        summary = PolicyViolationSummary()
        for v in violations:
            state = v.get("policyViolation", {}).get("violationState", "")
            if state == "FAIL":
                summary.fail += 1
            elif state == "WARN":
                summary.warn += 1
            elif state == "INFO":
                summary.info += 1

        return summary

    # =========================================================================
    # Findings (Analysis/Audit)
    # =========================================================================
    def get_project_findings(
        self,
        project_uuid: str,
        suppressed: bool = False
    ) -> List[Dict[str, Any]]:
        """Get findings (vulnerabilities with audit info) for a project."""
        params = {"suppressed": suppressed}
        return self._get(f"/finding/project/{project_uuid}", params=params)

    def update_analysis(
        self,
        project_uuid: str,
        component_uuid: str,
        vulnerability_uuid: str,
        state: str,
        comment: Optional[str] = None,
        suppressed: bool = False
    ) -> Dict[str, Any]:
        """
        Update vulnerability analysis/audit state.

        Args:
            project_uuid: Project UUID
            component_uuid: Component UUID
            vulnerability_uuid: Vulnerability UUID
            state: Analysis state (NOT_SET, EXPLOITABLE, IN_TRIAGE, FALSE_POSITIVE,
                   NOT_AFFECTED, RESOLVED)
            comment: Optional analysis comment
            suppressed: Whether to suppress the finding
        """
        data = {
            "project": project_uuid,
            "component": component_uuid,
            "vulnerability": vulnerability_uuid,
            "analysisState": state,
            "suppressed": suppressed
        }

        if comment:
            data["comment"] = comment

        return self._put("/analysis", json=data)

    # =========================================================================
    # License
    # =========================================================================
    def get_licenses(self) -> List[Dict[str, Any]]:
        """Get all licenses."""
        return self._get("/license")

    def get_license_groups(self) -> List[Dict[str, Any]]:
        """Get all license groups."""
        return self._get("/licenseGroup")


# =========================================================================
# CLI Interface
# =========================================================================
def main():
    """CLI interface for common operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Dependency-Track CLI")
    parser.add_argument("--url", help="Dependency-Track URL", default=os.getenv("DTRACK_URL"))
    parser.add_argument("--api-key", help="API Key", default=os.getenv("DTRACK_API_KEY"))

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload SBOM")
    upload_parser.add_argument("bom", help="Path to BOM file")
    upload_parser.add_argument("--project", help="Project name")
    upload_parser.add_argument("--version", help="Project version")
    upload_parser.add_argument("--wait", action="store_true", help="Wait for processing")

    # List projects command
    subparsers.add_parser("projects", help="List projects")

    # Get metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Get project metrics")
    metrics_parser.add_argument("project", help="Project name")
    metrics_parser.add_argument("version", help="Project version")

    # Security gate command
    gate_parser = subparsers.add_parser("gate", help="Security gate check")
    gate_parser.add_argument("project", help="Project name")
    gate_parser.add_argument("version", help="Project version")
    gate_parser.add_argument("--max-critical", type=int, default=0)
    gate_parser.add_argument("--max-high", type=int, default=0)

    args = parser.parse_args()

    if not args.url or not args.api_key:
        parser.error("--url and --api-key required (or set DTRACK_URL and DTRACK_API_KEY)")

    client = DependencyTrackClient(base_url=args.url, api_key=args.api_key)

    if args.command == "upload":
        result = client.upload_sbom(
            args.bom,
            project_name=args.project,
            project_version=args.version
        )
        print(f"Upload initiated. Token: {result.get('token')}")

        if args.wait:
            print("Waiting for processing...")
            if client.wait_for_bom_processing(result["token"]):
                print("Processing complete!")
            else:
                print("Processing timeout!")
                exit(1)

    elif args.command == "projects":
        projects = client.get_projects()
        for p in projects:
            print(f"{p['name']}:{p['version']} ({p['uuid']})")

    elif args.command == "metrics":
        project = client.get_project_by_name_version(args.project, args.version)
        if not project:
            print(f"Project not found: {args.project}:{args.version}")
            exit(1)

        summary = client.get_vulnerability_summary(project["uuid"])
        print(f"Vulnerabilities for {args.project}:{args.version}")
        print(f"  Critical: {summary.critical}")
        print(f"  High:     {summary.high}")
        print(f"  Medium:   {summary.medium}")
        print(f"  Low:      {summary.low}")
        print(f"  Total:    {summary.total}")

    elif args.command == "gate":
        project = client.get_project_by_name_version(args.project, args.version)
        if not project:
            print(f"Project not found: {args.project}:{args.version}")
            exit(1)

        summary = client.get_vulnerability_summary(project["uuid"])

        if summary.exceeds_threshold(
            max_critical=args.max_critical,
            max_high=args.max_high
        ):
            print(f"FAILED: Vulnerabilities exceed threshold")
            print(f"  Critical: {summary.critical} (max: {args.max_critical})")
            print(f"  High: {summary.high} (max: {args.max_high})")
            exit(1)
        else:
            print("PASSED: Security gate check")


if __name__ == "__main__":
    main()
