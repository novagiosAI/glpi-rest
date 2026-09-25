from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SearchType = Literal[
    "contains",
    "equals",
    "notequals",
    "lessthan",
    "morethan",
    "under",
    "notunder",
]
LogicalOperator = Literal["AND", "OR", "AND NOT", "OR NOT"]
SortOrder = Literal["ASC", "DESC"]


@dataclass(frozen=True, slots=True)
class SearchCriterion:
    """One row of a GLPI multi-criteria search.

    ``field`` is the numeric search-option id for the item type (visible in
    the GLPI search UI when hovering a column, or via ``listSearchOptions``).
    """

    field: int
    value: str | int
    searchtype: SearchType = "contains"
    link: LogicalOperator | None = None


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Typed view of a GLPI ``/search/<itemtype>`` response."""

    total_count: int
    count: int
    content_range: str | None
    data: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> SearchResult:
        return cls(
            total_count=payload.get("totalcount", 0),
            count=payload.get("count", 0),
            content_range=payload.get("content-range"),
            data=payload.get("data", []),
        )
