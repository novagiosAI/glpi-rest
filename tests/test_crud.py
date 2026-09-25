from __future__ import annotations

import pytest

from conftest import BASE_URL
from glpi_rest import GLPIError, GLPINotFoundError


def test_get_item(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/Ticket/42", json={"id": 42, "name": "Printer down"})

    item = connected_client.get_item("Ticket", 42)

    assert item["id"] == 42
    assert requests_mock.last_request.headers["Session-Token"] == "tok-1"


def test_get_items_passes_params(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/Ticket", json=[{"id": 1}, {"id": 2}])

    items = connected_client.get_items("Ticket", range="0-1")

    assert len(items) == 2
    assert requests_mock.last_request.qs["range"] == ["0-1"]


def test_add_item_wraps_input(connected_client, requests_mock):
    requests_mock.post(f"{BASE_URL}/Ticket", json={"id": 7, "message": ""})

    result = connected_client.add_item("Ticket", {"name": "New", "content": "Body"})

    assert result["id"] == 7
    assert requests_mock.last_request.json() == {
        "input": {"name": "New", "content": "Body"}
    }


def test_update_item(connected_client, requests_mock):
    requests_mock.put(f"{BASE_URL}/Ticket/7", json=[{"7": True}])

    connected_client.update_item("Ticket", 7, {"status": 5})

    assert requests_mock.last_request.json() == {"input": {"status": 5}}


def test_delete_item_defaults_to_trash(connected_client, requests_mock):
    requests_mock.delete(f"{BASE_URL}/Ticket/7", json=[{"7": True}])

    connected_client.delete_item("Ticket", 7)

    assert requests_mock.last_request.qs["force_purge"] == ["0"]


def test_delete_item_force_purge(connected_client, requests_mock):
    requests_mock.delete(f"{BASE_URL}/Ticket/7", json=[{"7": True}])

    connected_client.delete_item("Ticket", 7, force_purge=True)

    assert requests_mock.last_request.qs["force_purge"] == ["1"]


def test_missing_item_raises_not_found(connected_client, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/Ticket/999", status_code=404, json=["ERROR_ITEM_NOT_FOUND"]
    )

    with pytest.raises(GLPINotFoundError):
        connected_client.get_item("Ticket", 999)


def test_server_error_raises_glpi_error(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/Ticket/1", status_code=500, text="boom")

    with pytest.raises(GLPIError):
        connected_client.get_item("Ticket", 1)
