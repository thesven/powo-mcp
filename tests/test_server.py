from __future__ import annotations

import httpx
import pytest

from powo_mcp.client import PowoClient
from powo_mcp.server import create_server


@pytest.fixture
def mock_client() -> PowoClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/search" in path:
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "fqId": "urn:test:p1",
                            "name": "Quercus alba",
                            "author": "L.",
                            "taxonomicStatus": "Accepted",
                            "family": "Fagaceae",
                        }
                    ]
                },
            )
        if "/taxon/" in path:
            return httpx.Response(
                200,
                json={
                    "fqId": "urn:test:p1",
                    "name": "Quercus alba",
                    "author": "L.",
                    "family": "Fagaceae",
                    "taxonomicStatus": "Accepted",
                    "lifeform": "Tree",
                    "climate": "Temperate",
                    "descriptions": [{"heading": "Habit", "description": "Large tree"}],
                    "images": [
                        {"thumbnail": "thumb.jpg", "fullsize": "full.jpg", "copyright": "Kew"}
                    ],
                    "distribution": {
                        "natives": [{"name": "North America"}],
                        "introduced": [],
                    },
                },
            )
        return httpx.Response(404, text="Not Found")

    return PowoClient(transport=httpx.MockTransport(handler))


@pytest.fixture
def failing_client() -> PowoClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Server Error")

    return PowoClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_server_tools(mock_client: PowoClient) -> None:
    server = create_server(mock_client)

    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert "search_plants" in tool_names
    assert "get_plant_details" in tool_names
    assert "get_plant_distribution" in tool_names
    assert "resolve_plant_synonymy" in tool_names
    assert "verify_plant_native_status" in tool_names
    assert "get_plant_characteristics" in tool_names
    assert "get_plant_images" in tool_names

    res = await server.call_tool("search_plants", {"query": "Quercus alba"})
    assert "Quercus alba" in res.content[0].text

    res = await server.call_tool("get_plant_details", {"fq_id": "urn:test:p1"})
    assert "Quercus alba" in res.content[0].text
    assert "Tree" in res.content[0].text

    res = await server.call_tool("get_plant_distribution", {"fq_id": "urn:test:p1"})
    assert "North America" in res.content[0].text

    res = await server.call_tool("resolve_plant_synonymy", {"name": "Quercus alba"})
    assert "ACCEPTED SPECIES" in res.content[0].text

    res = await server.call_tool(
        "verify_plant_native_status", {"query": "Quercus alba", "target_region": "North America"}
    )
    assert "NATIVE" in res.content[0].text

    res = await server.call_tool("get_plant_characteristics", {"fq_id": "urn:test:p1"})
    assert "Large tree" in res.content[0].text

    res = await server.call_tool("get_plant_images", {"fq_id": "urn:test:p1"})
    assert "full.jpg" in res.content[0].text


@pytest.mark.asyncio
async def test_server_tool_errors(failing_client: PowoClient) -> None:
    server = create_server(failing_client)

    res = await server.call_tool("get_plant_details", {"fq_id": "urn:nonexistent:id"})
    assert "failed" in res.content[0].text

    res = await server.call_tool("get_plant_distribution", {"fq_id": "urn:nonexistent:id"})
    assert "failed" in res.content[0].text

    res = await server.call_tool("resolve_plant_synonymy", {"name": "NonexistentUnknownPlant"})
    assert "failed" in res.content[0].text

    res = await server.call_tool(
        "verify_plant_native_status", {"query": "NonexistentUnknownPlant", "target_region": "Space"}
    )
    assert "failed" in res.content[0].text

    res = await server.call_tool("get_plant_characteristics", {"fq_id": "urn:nonexistent:id"})
    assert "failed" in res.content[0].text

    res = await server.call_tool("get_plant_images", {"fq_id": "urn:nonexistent:id"})
    assert "failed" in res.content[0].text
