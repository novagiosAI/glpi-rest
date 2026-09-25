from __future__ import annotations

import pytest

from conftest import BASE_URL
from glpi_rest import GLPIClient, GLPIError
from glpi_rest.client import MAX_ERROR_DETAIL_CHARS


def test_repr_never_leaks_credentials():
    client = GLPIClient(
        BASE_URL,
        app_token="app-token-secret-value",
        user_token="user-token-secret-value",
    )

    rendered = repr(client)

    assert "app-token-secret-value" not in rendered
    assert "user-token-secret-value" not in rendered
    assert "app-..." in rendered
    # Must stay printable on a legacy Windows console code page.
    rendered.encode("cp1252")


def test_error_detail_is_truncated(connected_client, requests_mock):
    """A large error body must not be echoed wholesale into the caller's logs."""
    requests_mock.get(
        f"{BASE_URL}/Ticket", status_code=500, text="x" * (MAX_ERROR_DETAIL_CHARS * 3)
    )

    with pytest.raises(GLPIError) as excinfo:
        connected_client.get_items("Ticket")

    message = str(excinfo.value)
    assert "(truncated)" in message
    assert len(message) < MAX_ERROR_DETAIL_CHARS * 2


def test_tls_verification_is_on_by_default():
    client = GLPIClient(BASE_URL, app_token="app", user_token="tok")

    assert client._verify_ssl is True


def test_requests_carry_a_timeout(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/Ticket/1", json={"id": 1})

    connected_client.get_item("Ticket", 1)

    assert connected_client._timeout == 30.0


def test_credentials_are_not_sent_in_the_url(requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-1"})
    client = GLPIClient(BASE_URL, app_token="app-token", user_token="user-token")

    client.init_session()

    assert "user-token" not in requests_mock.last_request.url
    assert "app-token" not in requests_mock.last_request.url
