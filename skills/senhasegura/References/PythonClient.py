"""
Senhasegura A2A API Client for Python
OAuth 2.0 authentication with credential management
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, TypeVar
from contextlib import contextmanager

import requests
from requests.auth import AuthBase


@dataclass
class Credential:
    """Credential model"""
    id: str
    identifier: str
    username: str
    hostname: str
    ip: str | None = None
    credential_type: str = "Local User"
    additional_info: str | None = None
    tags: list[str] | None = None


@dataclass
class CredentialPassword:
    """Credential password model"""
    id: str
    password: str
    expiration: datetime


class OAuth2Auth(AuthBase):
    """OAuth 2.0 authentication handler for requests"""

    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: str | None = None
        self.token_expiry: datetime | None = None

    def _get_token(self) -> str:
        """Obtain new access token"""
        response = requests.post(
            f"{self.base_url}/iso/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        # Set expiry with 1 minute buffer
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self.access_token

    def __call__(self, request):
        if not self.access_token or not self.token_expiry or self.token_expiry < datetime.now():
            self._get_token()
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        return request


class SenhaseguraClient:
    """Senhasegura A2A API Client"""

    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: int = 30,
    ):
        self.base_url = base_url or os.environ["SENHASEGURA_URL"]
        self.timeout = timeout
        self.auth = OAuth2Auth(
            self.base_url,
            client_id or os.environ["SENHASEGURA_CLIENT_ID"],
            client_secret or os.environ["SENHASEGURA_CLIENT_SECRET"],
        )
        self.session = requests.Session()
        self.session.auth = self.auth

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request"""
        response = self.session.request(
            method,
            f"{self.base_url}{endpoint}",
            params=params,
            json=json,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def list_credentials(self) -> list[Credential]:
        """List all credentials"""
        data = self._request("GET", "/api/pam/credential")
        return [
            Credential(
                id=c["id"],
                identifier=c["identifier"],
                username=c["username"],
                hostname=c["hostname"],
                ip=c.get("ip"),
                credential_type=c.get("type", "Local User"),
                additional_info=c.get("additional_info"),
                tags=c.get("tags"),
            )
            for c in data["response"]["credentials"]
        ]

    def get_credential(self, credential_id: str) -> Credential:
        """Get credential by ID"""
        data = self._request("GET", f"/api/pam/credential/{credential_id}")
        c = data["response"]["credential"]
        return Credential(
            id=c["id"],
            identifier=c["identifier"],
            username=c["username"],
            hostname=c["hostname"],
            ip=c.get("ip"),
            credential_type=c.get("type", "Local User"),
        )

    def get_password(self, credential_id: str) -> CredentialPassword:
        """Get credential password"""
        data = self._request(
            "GET",
            "/iso/coe/senha",
            params={"credentialId": credential_id},
        )
        cred = data["response"]["credential"]
        return CredentialPassword(
            id=cred["id"],
            password=cred["password"],
            expiration=datetime.fromisoformat(cred["expiration"].replace("Z", "+00:00")),
        )

    def create_credential(
        self,
        identifier: str,
        username: str,
        password: str,
        hostname: str,
        **kwargs,
    ) -> Credential:
        """Create new credential"""
        payload = {
            "identifier": identifier,
            "username": username,
            "password": password,
            "hostname": hostname,
            **kwargs,
        }
        data = self._request("POST", "/api/pam/credential", json=payload)
        c = data["response"]["credential"]
        return Credential(
            id=c["id"],
            identifier=c["identifier"],
            username=c["username"],
            hostname=c["hostname"],
        )

    def update_credential(self, credential_id: str, **updates) -> Credential:
        """Update credential"""
        data = self._request(
            "PUT",
            f"/api/pam/credential/{credential_id}",
            json=updates,
        )
        c = data["response"]["credential"]
        return Credential(
            id=c["id"],
            identifier=c["identifier"],
            username=c["username"],
            hostname=c["hostname"],
        )

    def release_custody(self, credential_id: str) -> None:
        """Release credential custody"""
        self._request("DELETE", f"/iso/pam/credential/custody/{credential_id}")

    @contextmanager
    def password_context(self, credential_id: str):
        """Context manager for password with automatic custody release"""
        cred = self.get_password(credential_id)
        try:
            yield cred.password
        finally:
            self.release_custody(credential_id)


# DSM Client for DevOps Secrets
class DSMClient(SenhaseguraClient):
    """Senhasegura DSM (DevOps Secrets Manager) Client"""

    def list_secrets(self, application: str | None = None) -> list[dict[str, Any]]:
        """List all secrets"""
        params = {}
        if application:
            params["application"] = application
        data = self._request("GET", "/api/dsm/secret", params=params)
        return data["response"]["secrets"]

    def get_secret(self, identifier: str) -> dict[str, Any]:
        """Get secret by identifier"""
        data = self._request("GET", f"/api/dsm/secret/{identifier}")
        return data["response"]["secret"]

    def create_secret(
        self,
        identifier: str,
        data: dict[str, str],
        application: str,
        system: str,
        environment: str,
    ) -> dict[str, Any]:
        """Create new secret"""
        payload = {
            "identifier": identifier,
            "data": data,
            "application": application,
            "system": system,
            "environment": environment,
        }
        response = self._request("POST", "/api/dsm/secret", json=payload)
        return response["response"]["secret"]

    def update_secret(self, identifier: str, data: dict[str, str]) -> dict[str, Any]:
        """Update secret"""
        response = self._request(
            "PUT",
            f"/api/dsm/secret/{identifier}",
            json={"data": data},
        )
        return response["response"]["secret"]

    def delete_secret(self, identifier: str) -> None:
        """Delete secret"""
        self._request("DELETE", f"/api/dsm/secret/{identifier}")


def main():
    """Example usage"""
    # Initialize client (uses environment variables)
    client = SenhaseguraClient()

    # List credentials
    credentials = client.list_credentials()
    for cred in credentials:
        print(f"  {cred.identifier}: {cred.username}@{cred.hostname}")

    # Get password with automatic custody release
    with client.password_context("123") as password:
        print(f"Using password for connection...")
        # Use password here

    # DSM example
    dsm = DSMClient()
    secrets = dsm.list_secrets(application="my-app")
    for secret in secrets:
        print(f"  Secret: {secret['identifier']}")


if __name__ == "__main__":
    main()
