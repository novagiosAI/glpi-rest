from __future__ import annotations

import pytest

from conftest import BASE_URL
from glpi_rest import GLPIAuthError


def test_expired_session_is_transparently_renewed(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-2"})
    requests_mock.get(
        f"{BASE_URL}/Ticket/42",
        [
            {"status_code": 401, "json": ["ERROR_SESSION_TOKEN_INVALID"]},
            {"status_code": 200, "json": {"id": 42}},
        ],
    )

    item = connected_client.get_item("Ticket", 42)

    assert item["id"] == 42
    assert requests_mock.last_request.headers["Session-Token"] == "tok-2"


def test_reconnect_is_attempted_only_once(connected_client, requests_mock):
    """A permanently-401 endpoint must not trigger a reconnection loop."""
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-2"})
    requests_mock.get(
        f"{BASE_URL}/Ticket/42", status_code=401, json=["ERROR_SESSION_TOKEN_INVALID"]
    )

    def count(fragment: str) -> int:
        return len([r for r in requests_mock.request_history if fragment in r.url])

    # The fixture already opened a session; only count what this call adds.
    init_before = count("initSession")

    with pytest.raises(GLPIAuthError):
        connected_client.get_item("Ticket", 42)

    assert count("initSession") - init_before == 1, "expected exactly one reconnect"
    assert count("/Ticket/42") == 2, "expected the original call plus one replay"


def test_reconnect_replays_the_request_body(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-2"})
    requests_mock.post(
        f"{BASE_URL}/Ticket",
        [
            {"status_code": 401, "json": ["ERROR_SESSION_TOKEN_INVALID"]},
            {"status_code": 201, "json": {"id": 7}},
        ],
    )

    result = connected_client.add_item("Ticket", {"name": "New"})

    assert result["id"] == 7
    assert requests_mock.last_request.json() == {"input": {"name": "New"}}
