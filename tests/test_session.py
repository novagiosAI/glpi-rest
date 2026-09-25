from __future__ import annotations

import pytest

from conftest import BASE_URL
from glpi_rest import GLPIAuthError, GLPIClient, GLPISessionError


def test_requires_some_credentials():
    with pytest.raises(ValueError):
        GLPIClient(BASE_URL, app_token="app-token")


def test_init_session_with_user_token(requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-1"})
    client = GLPIClient(BASE_URL, app_token="app-token", user_token="user-token")

    assert client.init_session() == "tok-1"
    assert client.is_connected
    headers = requests_mock.last_request.headers
    assert headers["Authorization"] == "user_token user-token"
    assert headers["App-Token"] == "app-token"


def test_init_session_with_basic_auth(requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-1"})
    client = GLPIClient(BASE_URL, app_token="app-token", username="glpi", password="pw")

    client.init_session()

    assert "Authorization" in requests_mock.last_request.headers
    assert requests_mock.last_request.headers["Authorization"].startswith("Basic ")


def test_init_session_rejects_bad_credentials(requests_mock):
    requests_mock.get(
        f"{BASE_URL}/initSession", status_code=401, json=["ERROR_GLPI_LOGIN"]
    )
    client = GLPIClient(BASE_URL, app_token="app-token", user_token="bad")

    with pytest.raises(GLPIAuthError):
        client.init_session()


def test_request_without_session_raises():
    client = GLPIClient(BASE_URL, app_token="app-token", user_token="user-token")

    with pytest.raises(GLPISessionError):
        client.get_item("Ticket", 1)


def test_context_manager_opens_and_kills_session(requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-1"})
    kill = requests_mock.get(f"{BASE_URL}/killSession", json={})

    with GLPIClient(BASE_URL, app_token="app-token", user_token="user-token") as client:
        assert client.is_connected

    assert kill.called
    assert not client.is_connected


def test_close_is_idempotent(requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-1"})
    kill = requests_mock.get(f"{BASE_URL}/killSession", json={})
    client = GLPIClient(BASE_URL, app_token="app-token", user_token="user-token")
    client.init_session()

    client.close()
    client.close()

    assert kill.call_count == 1
