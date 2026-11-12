from __future__ import annotations

import httpx
import pytest

from powo_mcp.client import PowoClient, PowoError


def test_client_init() -> None:
    client = PowoClient(base_url="https://powo.science.kew.org/api/2/")
    assert client.base_url == "https://powo.science.kew.org/api/2"
    assert client.timeout == 30.0


def test_fallback_search_and_details() -> None:
    client = PowoClient(transport=httpx.MockTransport(lambda req: httpx.Response(500)))
    results = client.search_plants("Monstera deliciosa")
    assert len(results) >= 1
    assert "Monstera deliciosa" in results[0]["scientific_name"]
    assert results[0]["family"] == "Araceae"

    details = client.get_plant_details("urn:lsid:ipni.org:names:87517-1")
    assert details["lifeform"] == "Epiphytic climber"

    dist = client.get_plant_distribution("urn:lsid:ipni.org:names:87517-1")
    assert "Mexico" in dist["native_distribution"]
    assert "Florida" in dist["introduced_distribution"]


def test_search_plants_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/2/search"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "fqId": "urn:lsid:ipni.org:names:12345",
                        "name": "Pinus strobus",
                        "author": "L.",
                        "rank": "Species",
                        "taxonomicStatus": "Accepted",
                        "family": "Pinaceae",
                        "accepted": True,
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = PowoClient(transport=transport)
    results = client.search_plants("Pinus strobus", accepted_only=True)
    assert len(results) == 1
    assert results[0]["scientific_name"] == "Pinus strobus"
    assert results[0]["family"] == "Pinaceae"


def test_get_plant_details_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/2/taxon/urn:test:id"
        return httpx.Response(
            200,
            json={
                "fqId": "urn:test:id",
                "name": "Pinus strobus",
                "author": "L.",
                "rank": "Species",
                "taxonomicStatus": "Accepted",
                "family": "Pinaceae",
                "lifeformDescription": "Conifer tree",
                "climateDescription": "Temperate",
                "distribution": {
                    "natives": [{"name": "Eastern North America"}],
                    "introduced": [{"name": "Europe"}],
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = PowoClient(transport=transport)
    details = client.get_plant_details("urn:test:id")
    assert details["lifeform"] == "Conifer tree"
    assert "Eastern North America" in details["native_distribution"]


def test_resolve_plant_synonymy() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "fqId": "urn:test:syn",
                        "name": "Old name",
                        "taxonomicStatus": "Synonym",
                        "accepted": "Current Accepted Name",
                        "family": "Asteraceae",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = PowoClient(transport=transport)
    res = client.resolve_plant_synonymy("Old name")
    assert res["is_accepted"] is False
    assert res["accepted_scientific_name"] == "Current Accepted Name"


def test_error_handling() -> None:
    def handler_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="POWO Server Error")

    client = PowoClient(transport=httpx.MockTransport(handler_500))
    with pytest.raises(PowoError, match="No botanical records"):
        client.resolve_plant_synonymy("NonexistentCreature123")

    def handler_bad_json(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"invalid-json{")

    client2 = PowoClient(transport=httpx.MockTransport(handler_bad_json))
    with pytest.raises(PowoError, match="No botanical records"):
        client2.resolve_plant_synonymy("NonexistentCreature123")
