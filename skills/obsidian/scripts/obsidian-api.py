#!/usr/bin/env python3
"""
Obsidian Local REST API Client

A Python client for interacting with Obsidian via the Local REST API plugin.

Requirements:
    pip install requests urllib3

Usage:
    from obsidian_api import ObsidianAPI

    api = ObsidianAPI(api_key="your-api-key")
    files = api.list_files()
    content = api.read_file("Notes/MyNote.md")
"""

import os
import json
import urllib3
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    raise


@dataclass
class VaultFile:
    """Represents a file in the vault."""
    path: str
    name: str
    is_folder: bool
    size: Optional[int] = None
    mtime: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VaultFile":
        return cls(
            path=data.get("path", ""),
            name=data.get("name", ""),
            is_folder=data.get("isFolder", False),
            size=data.get("size"),
            mtime=datetime.fromisoformat(data["mtime"]) if data.get("mtime") else None,
        )


@dataclass
class SearchResult:
    """Represents a search result."""
    filename: str
    score: float
    matches: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        return cls(
            filename=data.get("filename", ""),
            score=data.get("score", 0.0),
            matches=data.get("matches", []),
        )


class ObsidianAPIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ObsidianAPI:
    """
    Client for Obsidian's Local REST API plugin.

    The Local REST API plugin must be installed and enabled in Obsidian.
    Get the API key from the plugin settings.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://127.0.0.1:27124",
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        """
        Initialize the Obsidian API client.

        Args:
            api_key: API key from Local REST API plugin settings.
                     Falls back to OBSIDIAN_API_KEY environment variable.
            base_url: Base URL for the API (default: https://127.0.0.1:27124)
            verify_ssl: Whether to verify SSL certificates (default: False for self-signed)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("OBSIDIAN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set via api_key parameter or OBSIDIAN_API_KEY env var"
            )

        self.base_url = base_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_ssl

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[str, Dict]] = None,
        content_type: str = "application/json",
        **kwargs,
    ) -> requests.Response:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(content_type)

        try:
            if isinstance(data, dict):
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                    **kwargs,
                )
            elif isinstance(data, str):
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    data=data.encode("utf-8"),
                    timeout=self.timeout,
                    **kwargs,
                )
            else:
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs,
                )

            if response.status_code >= 400:
                error_msg = response.text or f"HTTP {response.status_code}"
                raise ObsidianAPIError(error_msg, response.status_code)

            return response

        except requests.exceptions.ConnectionError as e:
            raise ObsidianAPIError(
                f"Connection failed. Is Obsidian running with Local REST API enabled? {e}"
            )
        except requests.exceptions.Timeout:
            raise ObsidianAPIError(f"Request timed out after {self.timeout}s")

    # -------------------------------------------------------------------------
    # Vault Operations
    # -------------------------------------------------------------------------

    def list_files(self, path: str = "") -> List[VaultFile]:
        """
        List files and folders in the vault.

        Args:
            path: Directory path (empty for root)

        Returns:
            List of VaultFile objects
        """
        endpoint = f"/vault/{path}" if path else "/vault/"
        response = self._request("GET", endpoint)

        if response.status_code == 200:
            data = response.json()
            files = data.get("files", []) if isinstance(data, dict) else data
            return [VaultFile.from_dict(f) for f in files]
        return []

    def read_file(self, path: str) -> str:
        """
        Read file content.

        Args:
            path: File path relative to vault root

        Returns:
            File content as string
        """
        endpoint = f"/vault/{path}"
        response = self._request("GET", endpoint)
        return response.text

    def write_file(self, path: str, content: str) -> bool:
        """
        Create or update a file.

        Args:
            path: File path relative to vault root
            content: File content

        Returns:
            True if successful
        """
        endpoint = f"/vault/{path}"
        response = self._request(
            "PUT", endpoint, data=content, content_type="text/markdown"
        )
        return response.status_code in (200, 201, 204)

    def append_file(self, path: str, content: str) -> bool:
        """
        Append content to a file.

        Args:
            path: File path relative to vault root
            content: Content to append

        Returns:
            True if successful
        """
        endpoint = f"/vault/{path}"
        response = self._request(
            "POST", endpoint, data=content, content_type="text/markdown"
        )
        return response.status_code in (200, 201, 204)

    def delete_file(self, path: str) -> bool:
        """
        Delete a file.

        Args:
            path: File path relative to vault root

        Returns:
            True if successful
        """
        endpoint = f"/vault/{path}"
        response = self._request("DELETE", endpoint)
        return response.status_code in (200, 204)

    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: File path relative to vault root

        Returns:
            True if file exists
        """
        try:
            self.read_file(path)
            return True
        except ObsidianAPIError as e:
            if e.status_code == 404:
                return False
            raise

    # -------------------------------------------------------------------------
    # Search Operations
    # -------------------------------------------------------------------------

    def search(self, query: str) -> List[SearchResult]:
        """
        Search the vault.

        Args:
            query: Search query

        Returns:
            List of SearchResult objects
        """
        endpoint = "/search/simple/"
        response = self._request("POST", endpoint, data={"query": query})

        if response.status_code == 200:
            results = response.json()
            return [SearchResult.from_dict(r) for r in results]
        return []

    def search_json(
        self, query: str, context_length: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search with JSON query.

        Args:
            query: Search query
            context_length: Number of characters to include around matches

        Returns:
            Raw search results
        """
        endpoint = "/search/"
        response = self._request(
            "POST",
            endpoint,
            data={"query": query, "contextLength": context_length},
        )
        return response.json() if response.status_code == 200 else []

    # -------------------------------------------------------------------------
    # Active File Operations
    # -------------------------------------------------------------------------

    def get_active_file(self) -> Optional[str]:
        """
        Get the currently active file path.

        Returns:
            Active file path or None
        """
        try:
            response = self._request("GET", "/active/")
            return response.text.strip()
        except ObsidianAPIError as e:
            if e.status_code == 404:
                return None
            raise

    def get_active_content(self) -> Optional[str]:
        """
        Get the content of the active file.

        Returns:
            File content or None
        """
        active_file = self.get_active_file()
        if active_file:
            return self.read_file(active_file)
        return None

    def open_file(self, path: str, new_leaf: bool = False) -> bool:
        """
        Open a file in Obsidian.

        Args:
            path: File path relative to vault root
            new_leaf: Open in new pane

        Returns:
            True if successful
        """
        endpoint = f"/open/{path}"
        params = {"newLeaf": str(new_leaf).lower()} if new_leaf else {}
        response = self._request("POST", endpoint, params=params)
        return response.status_code in (200, 204)

    # -------------------------------------------------------------------------
    # Command Operations
    # -------------------------------------------------------------------------

    def list_commands(self) -> List[Dict[str, str]]:
        """
        List all available commands.

        Returns:
            List of command objects with id and name
        """
        response = self._request("GET", "/commands/")
        return response.json() if response.status_code == 200 else []

    def execute_command(self, command_id: str) -> bool:
        """
        Execute a command by ID.

        Args:
            command_id: Command identifier (e.g., "app:open-settings")

        Returns:
            True if successful
        """
        endpoint = f"/commands/{command_id}"
        response = self._request("POST", endpoint)
        return response.status_code in (200, 204)

    # -------------------------------------------------------------------------
    # Periodic Notes
    # -------------------------------------------------------------------------

    def get_periodic_note(self, period: str = "daily") -> Optional[str]:
        """
        Get the path of a periodic note.

        Args:
            period: Note period (daily, weekly, monthly, quarterly, yearly)

        Returns:
            File path or None
        """
        try:
            response = self._request("GET", f"/periodic/{period}/")
            return response.text.strip()
        except ObsidianAPIError as e:
            if e.status_code == 404:
                return None
            raise

    def open_periodic_note(self, period: str = "daily") -> bool:
        """
        Open a periodic note.

        Args:
            period: Note period (daily, weekly, monthly, quarterly, yearly)

        Returns:
            True if successful
        """
        try:
            response = self._request("POST", f"/periodic/{period}/")
            return response.status_code in (200, 204)
        except ObsidianAPIError:
            return False

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_vault_info(self) -> Dict[str, Any]:
        """
        Get vault information.

        Returns:
            Dict with vault name and path
        """
        response = self._request("GET", "/")
        return response.json() if response.status_code == 200 else {}

    def is_connected(self) -> bool:
        """
        Check if connection to Obsidian is working.

        Returns:
            True if connected
        """
        try:
            self.get_vault_info()
            return True
        except ObsidianAPIError:
            return False

    # -------------------------------------------------------------------------
    # Higher-Level Operations
    # -------------------------------------------------------------------------

    def create_note(
        self,
        path: str,
        title: Optional[str] = None,
        content: str = "",
        frontmatter: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Create a new note with optional frontmatter.

        Args:
            path: File path (without .md extension)
            title: Note title (defaults to filename)
            content: Note body content
            frontmatter: Dict of frontmatter fields

        Returns:
            True if successful
        """
        # Ensure .md extension
        if not path.endswith(".md"):
            path = f"{path}.md"

        # Build note content
        parts = []

        if frontmatter or title:
            parts.append("---")
            if title:
                parts.append(f"title: {title}")
            parts.append(f"created: {datetime.now().strftime('%Y-%m-%d')}")
            if frontmatter:
                for key, value in frontmatter.items():
                    if isinstance(value, list):
                        parts.append(f"{key}:")
                        for item in value:
                            parts.append(f"  - {item}")
                    else:
                        parts.append(f"{key}: {value}")
            parts.append("---")
            parts.append("")

        if title:
            parts.append(f"# {title}")
            parts.append("")

        if content:
            parts.append(content)

        full_content = "\n".join(parts)
        return self.write_file(path, full_content)

    def append_to_daily(self, content: str, heading: Optional[str] = None) -> bool:
        """
        Append content to today's daily note.

        Args:
            content: Content to append
            heading: Optional heading to append under

        Returns:
            True if successful
        """
        daily_path = self.get_periodic_note("daily")
        if not daily_path:
            # Try to open/create daily note first
            self.open_periodic_note("daily")
            daily_path = self.get_periodic_note("daily")

        if daily_path:
            if heading:
                content = f"\n## {heading}\n{content}"
            else:
                content = f"\n{content}"
            return self.append_file(daily_path, content)
        return False

    def get_all_notes(self, folder: str = "") -> List[str]:
        """
        Get all markdown files in the vault or folder.

        Args:
            folder: Optional folder to list

        Returns:
            List of file paths
        """
        files = self.list_files(folder)
        result = []

        for f in files:
            if f.is_folder:
                # Recursively get files in subfolders
                subfolder_path = f.path if folder else f.name
                result.extend(self.get_all_notes(subfolder_path))
            elif f.path.endswith(".md"):
                result.append(f.path)

        return result

    def find_notes_with_tag(self, tag: str) -> List[str]:
        """
        Find notes containing a specific tag.

        Args:
            tag: Tag to search for (with or without #)

        Returns:
            List of file paths
        """
        if not tag.startswith("#"):
            tag = f"#{tag}"

        results = self.search(tag)
        return [r.filename for r in results]


# -------------------------------------------------------------------------
# CLI Interface
# -------------------------------------------------------------------------

def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian Local REST API Client")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OBSIDIAN_API_KEY"),
        help="API key (or set OBSIDIAN_API_KEY)",
    )
    parser.add_argument(
        "--url",
        default="https://127.0.0.1:27124",
        help="API base URL",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List files")
    list_parser.add_argument("path", nargs="?", default="", help="Directory path")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read file")
    read_parser.add_argument("path", help="File path")

    # Write command
    write_parser = subparsers.add_parser("write", help="Write file")
    write_parser.add_argument("path", help="File path")
    write_parser.add_argument("content", help="Content to write")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search vault")
    search_parser.add_argument("query", help="Search query")

    # Open command
    open_parser = subparsers.add_parser("open", help="Open file in Obsidian")
    open_parser.add_argument("path", help="File path")

    # Commands list
    subparsers.add_parser("commands", help="List available commands")

    # Execute command
    exec_parser = subparsers.add_parser("exec", help="Execute command")
    exec_parser.add_argument("command_id", help="Command ID")

    # Daily note
    subparsers.add_parser("daily", help="Open daily note")

    # Active file
    subparsers.add_parser("active", help="Get active file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        api = ObsidianAPI(api_key=args.api_key, base_url=args.url)

        if args.command == "list":
            files = api.list_files(args.path)
            for f in files:
                prefix = "D" if f.is_folder else "F"
                print(f"[{prefix}] {f.path}")

        elif args.command == "read":
            content = api.read_file(args.path)
            print(content)

        elif args.command == "write":
            success = api.write_file(args.path, args.content)
            print("Written successfully" if success else "Failed to write")

        elif args.command == "search":
            results = api.search(args.query)
            for r in results:
                print(f"{r.filename} (score: {r.score:.2f})")

        elif args.command == "open":
            success = api.open_file(args.path)
            print("Opened successfully" if success else "Failed to open")

        elif args.command == "commands":
            commands = api.list_commands()
            for cmd in commands:
                print(f"{cmd.get('id')}: {cmd.get('name')}")

        elif args.command == "exec":
            success = api.execute_command(args.command_id)
            print("Executed successfully" if success else "Failed to execute")

        elif args.command == "daily":
            success = api.open_periodic_note("daily")
            print("Opened daily note" if success else "Failed to open daily note")

        elif args.command == "active":
            active = api.get_active_file()
            print(active if active else "No active file")

    except ObsidianAPIError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
