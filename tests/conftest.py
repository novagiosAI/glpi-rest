from __future__ import annotations

import pytest
import requests_mock as rm_module

from glpi_rest import GLPIClient

BASE_URL = "https://glpi.example.com/apirest.php"


@pytest.fixture
def requests_mock():
    with rm_module.Mocker() as m:
        yield m


@pytest.fixture
def connected_client(requests_mock):
    requests_mock.get(f"{BASE_URL}/initSession", json={"session_token": "tok-1"})
    client = GLPIClient(BASE_URL, app_token="app-token", user_token="user-token")
    client.init_session()
    return client
