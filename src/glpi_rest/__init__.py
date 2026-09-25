from .client import GLPIClient
from .exceptions import GLPIAuthError, GLPIError, GLPINotFoundError, GLPISessionError
from .models import SearchCriterion, SearchResult

__version__ = "0.1.0"

__all__ = [
    "GLPIClient",
    "GLPIError",
    "GLPIAuthError",
    "GLPISessionError",
    "GLPINotFoundError",
    "SearchCriterion",
    "SearchResult",
]
