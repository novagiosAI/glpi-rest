from __future__ import annotations

from collections.abc import Sequence
from types import TracebackType
from typing import Any

import requests

from .exceptions import GLPIAuthError, GLPIError, GLPINotFoundError, GLPISessionError
from .models import SearchCriterion, SearchResult, SortOrder

#: Longest error payload echoed into an exception message. Server responses can
#: carry business data; truncating keeps it out of the caller's logs.
MAX_ERROR_DETAIL_CHARS = 500


def _mask(secret: str | None) -> str:
    """Render a credential safe to display: ``"abcd1234"`` -> ``"abcd..."``.

    ASCII only: this string reaches Windows consoles using legacy code pages,
    where a non-ASCII character would raise ``UnicodeEncodeError`` on print.
    """
    if not secret:
        return "unset"
    return f"{secret[:4]}..." if len(secret) > 4 else "..."


class GLPIClient:
    """Typed REST client for the GLPI API (GLPI 10 and 11).

    Handles session initialization, automatic reconnection on an expired
    session token, and typed helpers for CRUD and multi-criteria search.

    Example:
        >>> with GLPIClient(
        ...     "https://glpi.example.com/apirest.php",
        ...     app_token="...",
        ...     user_token="...",
        ... ) as client:
        ...     tickets = client.get_items("Ticket", range="0-9")
    """

    def __init__(
        self,
        url: str,
        app_token: str,
        *,
        user_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        verify_ssl: bool = True,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if not user_token and not (username and password):
            raise ValueError("Provide either user_token, or username and password")
        self._base_url = url.rstrip("/")
        self._app_token = app_token
        self._user_token = user_token
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._session = session or requests.Session()
        self._session_token: str | None = None

    def __repr__(self) -> str:
        """Never expose credentials: tokens are masked in any debug output."""
        return (
            f"{type(self).__name__}(url={self._base_url!r}, "
            f"app_token={_mask(self._app_token)!r}, "
            f"connected={self.is_connected})"
        )

    def __enter__(self) -> GLPIClient:
        self.init_session()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def is_connected(self) -> bool:
        return self._session_token is not None

    def init_session(self) -> str:
        """Open a GLPI session and store the session token. Returns the token."""
        headers = {"App-Token": self._app_token, "Content-Type": "application/json"}
        auth: tuple[str, str] | None = None
        if self._user_token:
            headers["Authorization"] = f"user_token {self._user_token}"
        elif self._username is not None and self._password is not None:
            auth = (self._username, self._password)
        response = self._session.get(
            f"{self._base_url}/initSession",
            headers=headers,
            auth=auth,
            verify=self._verify_ssl,
            timeout=self._timeout,
        )
        self._raise_for_status(response)
        payload = response.json()
        token = payload.get("session_token")
        if not isinstance(token, str) or not token:
            raise GLPIAuthError("initSession response did not contain a session_token")
        self._session_token = token
        return token

    def close(self) -> None:
        """Kill the current session, if any. Safe to call multiple times."""
        if self._session_token is None:
            return
        try:
            self._request("GET", "/killSession")
        finally:
            self._session_token = None

    # -- low level -----------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if self._session_token is None:
            raise GLPISessionError("Not connected: call init_session() first")
        return {
            "App-Token": self._app_token,
            "Session-Token": self._session_token,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        _retried: bool = False,
    ) -> requests.Response:
        response = self._session.request(
            method,
            f"{self._base_url}{path}",
            headers=self._headers(),
            params=params,
            json=json_body,
            verify=self._verify_ssl,
            timeout=self._timeout,
        )
        if response.status_code == 401 and not _retried:
            # GLPI expires session tokens on inactivity; transparently
            # reconnect once and retry the exact same call.
            self._session_token = None
            self.init_session()
            return self._request(
                method, path, params=params, json_body=json_body, _retried=True
            )
        self._raise_for_status(response)
        return response

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text
        detail = str(payload)
        if len(detail) > MAX_ERROR_DETAIL_CHARS:
            detail = f"{detail[:MAX_ERROR_DETAIL_CHARS]}... (truncated)"
        if response.status_code == 401:
            raise GLPIAuthError(f"Authentication failed: {detail}")
        if response.status_code == 404:
            raise GLPINotFoundError(f"Not found: {detail}")
        raise GLPIError(f"GLPI API error {response.status_code}: {detail}")

    # -- CRUD ------------------------------------------------------------

    def get_item(self, itemtype: str, id_: int, **params: Any) -> dict[str, Any]:
        """Fetch a single item, e.g. ``get_item("Ticket", 42)``."""
        result: dict[str, Any] = self._request(
            "GET", f"/{itemtype}/{id_}", params=params
        ).json()
        return result

    def get_items(self, itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """List items of a given type, e.g. ``get_items("Ticket", range="0-19")``."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/{itemtype}", params=params
        ).json()
        return result

    def add_item(self, itemtype: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Create an item. ``fields`` are the GLPI field names for that item type."""
        result: dict[str, Any] = self._request(
            "POST", f"/{itemtype}", json_body={"input": fields}
        ).json()
        return result

    def update_item(
        self, itemtype: str, id_: int, fields: dict[str, Any]
    ) -> dict[str, Any]:
        result: dict[str, Any] = self._request(
            "PUT", f"/{itemtype}/{id_}", json_body={"input": fields}
        ).json()
        return result

    def delete_item(
        self, itemtype: str, id_: int, *, force_purge: bool = False
    ) -> dict[str, Any]:
        params = {"force_purge": int(force_purge)}
        result: dict[str, Any] = self._request(
            "DELETE", f"/{itemtype}/{id_}", params=params
        ).json()
        return result

    # -- search -----------------------------------------------------------

    def search(
        self,
        itemtype: str,
        criteria: Sequence[SearchCriterion] | None = None,
        *,
        forcedisplay: Sequence[int] | None = None,
        sort: int | None = None,
        order: SortOrder = "ASC",
        range_: str | None = None,
    ) -> SearchResult:
        """Run a GLPI multi-criteria search and return a typed :class:`SearchResult`."""
        params: dict[str, Any] = {}
        for i, crit in enumerate(criteria or []):
            params[f"criteria[{i}][field]"] = crit.field
            params[f"criteria[{i}][searchtype]"] = crit.searchtype
            params[f"criteria[{i}][value]"] = crit.value
            if crit.link:
                params[f"criteria[{i}][link]"] = crit.link
        for i, field_id in enumerate(forcedisplay or []):
            params[f"forcedisplay[{i}]"] = field_id
        if sort is not None:
            params["sort"] = sort
        params["order"] = order
        if range_:
            params["range"] = range_
        response = self._request("GET", f"/search/{itemtype}", params=params)
        return SearchResult.from_api(response.json())
