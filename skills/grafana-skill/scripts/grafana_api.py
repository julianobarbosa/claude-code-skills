#!/usr/bin/env python3
"""
Grafana HTTP API Python Client

A reusable Python library for interacting with Grafana's HTTP API.
Supports dashboards, data sources, alerting, folders, annotations, and more.

Usage:
    from grafana_api import GrafanaAPI

    grafana = GrafanaAPI(
        base_url="https://your-grafana.com",
        token="your-service-account-token"
    )

    # Search dashboards
    dashboards = grafana.search_dashboards(query="production")

    # Get dashboard
    dashboard = grafana.get_dashboard_by_uid("abc123")
"""

import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlencode

try:
    import requests
except ImportError:
    raise ImportError("requests library required: pip install requests")


class GrafanaAPIError(Exception):
    """Exception raised for Grafana API errors."""

    def __init__(self, message: str, status_code: int, response: Dict[str, Any]):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(f"[{status_code}] {message}")


class GrafanaAPI:
    """
    Grafana HTTP API Client.

    Args:
        base_url: Grafana instance URL (e.g., "https://grafana.example.com")
        token: Service account token or API key
        org_id: Optional organization ID for multi-org setups
        timeout: Request timeout in seconds (default: 30)
        verify_ssl: Verify SSL certificates (default: True)
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        org_id: Optional[int] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        if org_id:
            self.session.headers['X-Grafana-Org-Id'] = str(org_id)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> Union[Dict, List]:
        """Make HTTP request to Grafana API."""
        url = f"{self.base_url}{endpoint}"

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=self.timeout,
            verify=self.verify_ssl,
            **kwargs
        )

        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {'message': response.text or 'No response body'}

        # Raise on error status codes
        if not response.ok:
            raise GrafanaAPIError(
                message=data.get('message', 'Unknown error'),
                status_code=response.status_code,
                response=data
            )

        return data

    # =========================================================================
    # Health & Info
    # =========================================================================

    def health(self) -> Dict:
        """Check Grafana health status."""
        return self._request('GET', '/api/health')

    def get_frontend_settings(self) -> Dict:
        """Get Grafana frontend settings."""
        return self._request('GET', '/api/frontend/settings')

    # =========================================================================
    # Dashboards
    # =========================================================================

    def search_dashboards(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        folder_uid: Optional[str] = None,
        starred: Optional[bool] = None,
        limit: int = 100,
        page: int = 1
    ) -> List[Dict]:
        """
        Search dashboards.

        Args:
            query: Search by title
            tag: Filter by tag
            folder_uid: Filter by folder UID
            starred: Filter by starred status
            limit: Max results (default: 100)
            page: Page number
        """
        params = {
            'type': 'dash-db',
            'limit': limit,
            'page': page
        }
        if query:
            params['query'] = query
        if tag:
            params['tag'] = tag
        if folder_uid:
            params['folderUIDs'] = folder_uid
        if starred is not None:
            params['starred'] = str(starred).lower()

        return self._request('GET', '/api/search', params=params)

    def get_dashboard_by_uid(self, uid: str) -> Dict:
        """Get dashboard by UID."""
        return self._request('GET', f'/api/dashboards/uid/{uid}')

    def create_or_update_dashboard(
        self,
        dashboard: Dict,
        folder_uid: Optional[str] = None,
        message: Optional[str] = None,
        overwrite: bool = False
    ) -> Dict:
        """
        Create or update a dashboard.

        Args:
            dashboard: Dashboard JSON model
            folder_uid: Target folder UID
            message: Commit message
            overwrite: Force overwrite existing dashboard
        """
        payload = {
            'dashboard': dashboard,
            'overwrite': overwrite
        }
        if folder_uid:
            payload['folderUid'] = folder_uid
        if message:
            payload['message'] = message

        return self._request('POST', '/api/dashboards/db', json_data=payload)

    def delete_dashboard(self, uid: str) -> Dict:
        """Delete dashboard by UID."""
        return self._request('DELETE', f'/api/dashboards/uid/{uid}')

    def get_dashboard_versions(self, uid: str, limit: int = 0) -> List[Dict]:
        """Get dashboard version history."""
        params = {'limit': limit} if limit > 0 else {}
        return self._request('GET', f'/api/dashboards/uid/{uid}/versions', params=params)

    def restore_dashboard_version(self, uid: str, version: int) -> Dict:
        """Restore dashboard to a specific version."""
        return self._request('POST', f'/api/dashboards/uid/{uid}/restore', json_data={'version': version})

    # =========================================================================
    # Data Sources
    # =========================================================================

    def list_datasources(self) -> List[Dict]:
        """List all data sources."""
        return self._request('GET', '/api/datasources')

    def get_datasource_by_uid(self, uid: str) -> Dict:
        """Get data source by UID."""
        return self._request('GET', f'/api/datasources/uid/{uid}')

    def get_datasource_by_name(self, name: str) -> Dict:
        """Get data source by name."""
        return self._request('GET', f'/api/datasources/name/{name}')

    def create_datasource(self, datasource: Dict) -> Dict:
        """Create a new data source."""
        return self._request('POST', '/api/datasources', json_data=datasource)

    def update_datasource(self, uid: str, datasource: Dict) -> Dict:
        """Update data source by UID."""
        return self._request('PUT', f'/api/datasources/uid/{uid}', json_data=datasource)

    def delete_datasource(self, uid: str) -> Dict:
        """Delete data source by UID."""
        return self._request('DELETE', f'/api/datasources/uid/{uid}')

    def health_check_datasource(self, uid: str) -> Dict:
        """Check data source health."""
        return self._request('GET', f'/api/datasources/uid/{uid}/health')

    def query_datasource(
        self,
        queries: List[Dict],
        from_time: str = 'now-1h',
        to_time: str = 'now'
    ) -> Dict:
        """
        Execute query against data sources.

        Args:
            queries: List of query objects with refId, datasource, and query model
            from_time: Start time (e.g., 'now-1h', epoch ms)
            to_time: End time (e.g., 'now', epoch ms)
        """
        payload = {
            'queries': queries,
            'from': from_time,
            'to': to_time
        }
        return self._request('POST', '/api/ds/query', json_data=payload)

    # =========================================================================
    # Folders
    # =========================================================================

    def list_folders(self, limit: int = 1000) -> List[Dict]:
        """List all folders."""
        return self._request('GET', '/api/folders', params={'limit': limit})

    def get_folder(self, uid: str) -> Dict:
        """Get folder by UID."""
        return self._request('GET', f'/api/folders/{uid}')

    def create_folder(self, title: str, uid: Optional[str] = None, parent_uid: Optional[str] = None) -> Dict:
        """
        Create a new folder.

        Args:
            title: Folder title
            uid: Optional custom UID
            parent_uid: Parent folder UID (for nested folders)
        """
        payload = {'title': title}
        if uid:
            payload['uid'] = uid
        if parent_uid:
            payload['parentUid'] = parent_uid
        return self._request('POST', '/api/folders', json_data=payload)

    def update_folder(self, uid: str, title: str, version: int, overwrite: bool = False) -> Dict:
        """Update folder."""
        payload = {
            'title': title,
            'version': version,
            'overwrite': overwrite
        }
        return self._request('PUT', f'/api/folders/{uid}', json_data=payload)

    def delete_folder(self, uid: str, force_delete_rules: bool = False) -> Dict:
        """Delete folder and all its dashboards."""
        params = {'forceDeleteRules': str(force_delete_rules).lower()}
        return self._request('DELETE', f'/api/folders/{uid}', params=params)

    # =========================================================================
    # Annotations
    # =========================================================================

    def query_annotations(
        self,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        dashboard_uid: Optional[str] = None,
        panel_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query annotations.

        Args:
            from_time: Start time in epoch milliseconds
            to_time: End time in epoch milliseconds
            dashboard_uid: Filter by dashboard UID
            panel_id: Filter by panel ID
            tags: Filter by tags
            limit: Max results
        """
        params = {'limit': limit}
        if from_time:
            params['from'] = from_time
        if to_time:
            params['to'] = to_time
        if dashboard_uid:
            params['dashboardUID'] = dashboard_uid
        if panel_id:
            params['panelId'] = panel_id
        if tags:
            params['tags'] = tags

        return self._request('GET', '/api/annotations', params=params)

    def create_annotation(
        self,
        text: str,
        time_ms: Optional[int] = None,
        time_end_ms: Optional[int] = None,
        dashboard_uid: Optional[str] = None,
        panel_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Create an annotation.

        Args:
            text: Annotation text
            time_ms: Start time in epoch milliseconds (default: now)
            time_end_ms: End time for region annotations
            dashboard_uid: Dashboard UID (omit for org annotation)
            panel_id: Panel ID
            tags: List of tags
        """
        payload = {
            'text': text,
            'time': time_ms or int(time.time() * 1000)
        }
        if time_end_ms:
            payload['timeEnd'] = time_end_ms
        if dashboard_uid:
            payload['dashboardUID'] = dashboard_uid
        if panel_id:
            payload['panelId'] = panel_id
        if tags:
            payload['tags'] = tags

        return self._request('POST', '/api/annotations', json_data=payload)

    def update_annotation(self, annotation_id: int, **kwargs) -> Dict:
        """Update annotation by ID."""
        return self._request('PUT', f'/api/annotations/{annotation_id}', json_data=kwargs)

    def delete_annotation(self, annotation_id: int) -> Dict:
        """Delete annotation by ID."""
        return self._request('DELETE', f'/api/annotations/{annotation_id}')

    # =========================================================================
    # Alerting
    # =========================================================================

    def list_alert_rules(self) -> List[Dict]:
        """List all alert rules."""
        return self._request('GET', '/api/v1/provisioning/alert-rules')

    def get_alert_rule(self, uid: str) -> Dict:
        """Get alert rule by UID."""
        return self._request('GET', f'/api/v1/provisioning/alert-rules/{uid}')

    def create_alert_rule(self, rule: Dict) -> Dict:
        """Create a new alert rule."""
        return self._request('POST', '/api/v1/provisioning/alert-rules', json_data=rule)

    def update_alert_rule(self, uid: str, rule: Dict) -> Dict:
        """Update alert rule by UID."""
        return self._request('PUT', f'/api/v1/provisioning/alert-rules/{uid}', json_data=rule)

    def delete_alert_rule(self, uid: str) -> Dict:
        """Delete alert rule by UID."""
        return self._request('DELETE', f'/api/v1/provisioning/alert-rules/{uid}')

    def list_contact_points(self) -> List[Dict]:
        """List all contact points."""
        return self._request('GET', '/api/v1/provisioning/contact-points')

    def get_notification_policies(self) -> Dict:
        """Get notification policy tree."""
        return self._request('GET', '/api/v1/provisioning/policies')

    def get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts."""
        return self._request('GET', '/api/alertmanager/grafana/api/v2/alerts')

    # =========================================================================
    # Users & Teams
    # =========================================================================

    def get_current_user(self) -> Dict:
        """Get current user info."""
        return self._request('GET', '/api/user')

    def search_users(self, query: Optional[str] = None, perpage: int = 100, page: int = 1) -> Dict:
        """Search users (admin only)."""
        params = {'perpage': perpage, 'page': page}
        if query:
            params['query'] = query
        return self._request('GET', '/api/users/search', params=params)

    def search_teams(self, query: Optional[str] = None, perpage: int = 100, page: int = 1) -> Dict:
        """Search teams."""
        params = {'perpage': perpage, 'page': page}
        if query:
            params['query'] = query
        return self._request('GET', '/api/teams/search', params=params)

    def get_team(self, team_id: int) -> Dict:
        """Get team by ID."""
        return self._request('GET', f'/api/teams/{team_id}')

    def create_team(self, name: str, email: Optional[str] = None) -> Dict:
        """Create a new team."""
        payload = {'name': name}
        if email:
            payload['email'] = email
        return self._request('POST', '/api/teams', json_data=payload)

    def delete_team(self, team_id: int) -> Dict:
        """Delete team by ID."""
        return self._request('DELETE', f'/api/teams/{team_id}')

    # =========================================================================
    # Service Accounts
    # =========================================================================

    def search_service_accounts(self, query: Optional[str] = None, perpage: int = 100, page: int = 1) -> Dict:
        """Search service accounts."""
        params = {'perpage': perpage, 'page': page}
        if query:
            params['query'] = query
        return self._request('GET', '/api/serviceaccounts/search', params=params)

    def create_service_account(self, name: str, role: str = 'Viewer') -> Dict:
        """
        Create a new service account.

        Args:
            name: Service account name
            role: Role (Viewer, Editor, Admin)
        """
        return self._request('POST', '/api/serviceaccounts', json_data={'name': name, 'role': role})

    def create_service_account_token(
        self,
        service_account_id: int,
        name: str,
        seconds_to_live: int = 0
    ) -> Dict:
        """
        Create a service account token.

        Args:
            service_account_id: Service account ID
            name: Token name
            seconds_to_live: Token TTL (0 = no expiration)
        """
        payload = {'name': name, 'secondsToLive': seconds_to_live}
        return self._request(
            'POST',
            f'/api/serviceaccounts/{service_account_id}/tokens',
            json_data=payload
        )

    # =========================================================================
    # Organizations
    # =========================================================================

    def get_current_org(self) -> Dict:
        """Get current organization."""
        return self._request('GET', '/api/org')

    def list_orgs(self) -> List[Dict]:
        """List all organizations (admin only)."""
        return self._request('GET', '/api/orgs')

    def create_org(self, name: str) -> Dict:
        """Create organization (admin only)."""
        return self._request('POST', '/api/orgs', json_data={'name': name})


# CLI support for quick testing
if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Grafana API Client')
    parser.add_argument('--url', default=os.environ.get('GRAFANA_URL', 'http://localhost:3000'))
    parser.add_argument('--token', default=os.environ.get('GRAFANA_TOKEN', ''))
    parser.add_argument('action', choices=['health', 'dashboards', 'datasources', 'folders'])

    args = parser.parse_args()

    if not args.token:
        print("Error: GRAFANA_TOKEN environment variable or --token required")
        exit(1)

    client = GrafanaAPI(base_url=args.url, token=args.token)

    try:
        if args.action == 'health':
            result = client.health()
        elif args.action == 'dashboards':
            result = client.search_dashboards()
        elif args.action == 'datasources':
            result = client.list_datasources()
        elif args.action == 'folders':
            result = client.list_folders()

        print(json.dumps(result, indent=2))
    except GrafanaAPIError as e:
        print(f"Error: {e}")
        exit(1)
