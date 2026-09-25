from __future__ import annotations

from conftest import BASE_URL
from glpi_rest import SearchCriterion

SEARCH_PAYLOAD = {
    "totalcount": 2,
    "count": 2,
    "content-range": "0-1/2",
    "data": [{"1": "Printer down"}, {"1": "VPN issue"}],
}


def test_search_maps_response(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/search/Ticket", json=SEARCH_PAYLOAD)

    result = connected_client.search("Ticket")

    assert result.total_count == 2
    assert result.count == 2
    assert result.content_range == "0-1/2"
    assert len(result.data) == 2


def test_search_serializes_criteria(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/search/Ticket", json=SEARCH_PAYLOAD)

    connected_client.search(
        "Ticket",
        criteria=[
            SearchCriterion(field=12, value=1, searchtype="equals"),
            SearchCriterion(field=1, value="vpn", link="AND"),
        ],
    )

    qs = requests_mock.last_request.qs
    assert qs["criteria[0][field]"] == ["12"]
    assert qs["criteria[0][searchtype]"] == ["equals"]
    assert qs["criteria[0][value]"] == ["1"]
    assert qs["criteria[1][link]"] == ["and"]


def test_search_serializes_display_sort_and_range(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/search/Ticket", json=SEARCH_PAYLOAD)

    connected_client.search(
        "Ticket", forcedisplay=[1, 12], sort=19, order="DESC", range_="0-49"
    )

    qs = requests_mock.last_request.qs
    assert qs["forcedisplay[0]"] == ["1"]
    assert qs["forcedisplay[1]"] == ["12"]
    assert qs["sort"] == ["19"]
    assert qs["order"] == ["desc"]
    assert qs["range"] == ["0-49"]


def test_search_result_handles_empty_payload(connected_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/search/Ticket", json={})

    result = connected_client.search("Ticket")

    assert result.total_count == 0
    assert result.data == []
