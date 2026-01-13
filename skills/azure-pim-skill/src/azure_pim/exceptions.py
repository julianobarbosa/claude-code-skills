"""Custom exceptions for Azure PIM operations."""

from __future__ import annotations

from typing import Any


class PIMError(Exception):
    """Base exception for all PIM-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(PIMError):
    """Authentication or authorization failure."""


class RoleNotFoundError(PIMError):
    """Requested role does not exist."""


class AssignmentNotFoundError(PIMError):
    """Role assignment not found."""


class ActivationError(PIMError):
    """Role activation failed."""


class ApprovalRequiredError(PIMError):
    """Operation requires approval that is pending."""


class PolicyViolationError(PIMError):
    """Operation violates PIM policy rules."""


class APIError(PIMError):
    """API request failed."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, {"status_code": status_code, "response": response_body})
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(APIError):
    """API rate limit exceeded."""


class MFARequiredError(AuthenticationError):
    """Multi-factor authentication is required."""
