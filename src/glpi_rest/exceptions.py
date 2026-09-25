from __future__ import annotations


class GLPIError(Exception):
    """Base exception for all glpi-rest errors."""


class GLPIAuthError(GLPIError):
    """Raised when authentication with the GLPI API fails."""


class GLPISessionError(GLPIError):
    """Raised when an operation is attempted without an active session."""


class GLPINotFoundError(GLPIError):
    """Raised when the requested GLPI item does not exist."""
