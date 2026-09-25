"""Integration tests against a real GLPI server.

Skipped unless ``GLPI_TEST_URL`` is set, so the default test run stays offline.

To run them, point the variables at a disposable GLPI instance — never a
production one, since these tests create and purge tickets::

    export GLPI_TEST_URL=http://localhost:8088/apirest.php
    export GLPI_TEST_APP_TOKEN=...
    export GLPI_TEST_USER_TOKEN=...
    pytest tests/test_integration.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest
import requests

from glpi_rest import GLPIClient, GLPINotFoundError, SearchCriterion

URL = os.environ.get("GLPI_TEST_URL")
APP_TOKEN = os.environ.get("GLPI_TEST_APP_TOKEN", "")
USER_TOKEN = os.environ.get("GLPI_TEST_USER_TOKEN", "")
USERNAME = os.environ.get("GLPI_TEST_USERNAME")
PASSWORD = os.environ.get("GLPI_TEST_PASSWORD")

pytestmark = pytest.mark.skipif(
    not URL, reason="set GLPI_TEST_URL to run integration tests"
)

TICKET_NAME_FIELD = 1  # GLPI search-option id for a ticket's title


@pytest.fixture
def glpi():
    with GLPIClient(URL, app_token=APP_TOKEN, user_token=USER_TOKEN) as client:
        yield client


@pytest.fixture
def ticket(glpi):
    """Create a uniquely named ticket and purge it afterwards."""
    name = f"glpi-rest integration {uuid.uuid4().hex[:12]}"
    created = glpi.add_item("Ticket", {"name": name, "content": "created by tests"})
    ticket_id = created["id"]
    try:
        yield ticket_id, name
    finally:
        glpi.delete_item("Ticket", ticket_id, force_purge=True)


def test_session_lifecycle():
    client = GLPIClient(URL, app_token=APP_TOKEN, user_token=USER_TOKEN)
    assert not client.is_connected

    token = client.init_session()
    assert token and client.is_connected

    client.close()
    assert not client.is_connected


def test_session_with_username_and_password():
    if not (USERNAME and PASSWORD):
        pytest.skip("set GLPI_TEST_USERNAME and GLPI_TEST_PASSWORD")
    with GLPIClient(
        URL, app_token=APP_TOKEN, username=USERNAME, password=PASSWORD
    ) as client:
        assert client.is_connected


def test_get_items_returns_a_list(glpi):
    items = glpi.get_items("Ticket", range="0-4")
    assert isinstance(items, list)


def test_crud_round_trip(glpi, ticket):
    ticket_id, name = ticket

    fetched = glpi.get_item("Ticket", ticket_id)
    assert fetched["id"] == ticket_id
    assert fetched["name"] == name

    glpi.update_item("Ticket", ticket_id, {"priority": 4})
    assert glpi.get_item("Ticket", ticket_id)["priority"] == 4


def test_search_finds_the_created_ticket(glpi, ticket):
    _, name = ticket

    result = glpi.search(
        "Ticket",
        criteria=[SearchCriterion(field=TICKET_NAME_FIELD, value=name)],
        forcedisplay=[TICKET_NAME_FIELD],
    )

    assert result.total_count >= 1
    assert any(name in str(row) for row in result.data)


def test_search_with_no_match_is_empty(glpi):
    result = glpi.search(
        "Ticket",
        criteria=[SearchCriterion(field=TICKET_NAME_FIELD, value=uuid.uuid4().hex)],
    )

    assert result.total_count == 0
    assert result.data == []


def test_missing_item_raises_not_found(glpi):
    with pytest.raises(GLPINotFoundError):
        glpi.get_item("Ticket", 99_999_999)


def test_expired_session_is_recovered_against_a_real_server(glpi, ticket):
    """The flagship feature, end to end: invalidate the session server-side,
    then make a normal call and expect it to succeed anyway."""
    ticket_id, _ = ticket
    stale_token = glpi._session_token

    # Kill the session out-of-band, exactly as GLPI does on inactivity.
    killed = requests.get(
        f"{URL.rstrip('/')}/killSession",
        headers={"App-Token": APP_TOKEN, "Session-Token": stale_token},
        timeout=30,
    )
    assert killed.ok

    fetched = glpi.get_item("Ticket", ticket_id)

    assert fetched["id"] == ticket_id
    assert glpi._session_token != stale_token, "expected a fresh session token"
