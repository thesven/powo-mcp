from __future__ import annotations

import argparse
import sys
from typing import Any

from mcp.server import MCPServer

from . import __version__
from .client import PowoClient, PowoError

DEFAULT_INSTRUCTIONS = """
POWO MCP Server: Access Royal Botanic Gardens Kew Plants of the World Online (POWO)
for global plant taxonomy, accepted botanical names, and native/introduced distributions.

Key Best Practices:
1. When checking a plant species or resolving ambiguous botanical names, call `search_plants`
   first to retrieve its official IPNI/POWO `fq_id` and taxonomic status.
2. Call `get_plant_details` to inspect lifeform, climate requirements, family, and citations.
3. Call `get_plant_distribution` to verify whether a plant is native or introduced in a region
   according to official TDWG botanical standards.
4. Use `resolve_plant_synonymy` to determine if an older botanical name is an invalid synonym
   and find its currently accepted scientific name.
""".strip()


def create_server(client: PowoClient | None = None) -> MCPServer:
    """Create and configure the Kew POWO MCPServer instance."""
    api = client or PowoClient()

    server = MCPServer(
        "powo",
        version=__version__,
        instructions=DEFAULT_INSTRUCTIONS,
    )

    @server.tool()
    def search_plants(
        query: str,
        accepted_only: bool = False,
        limit: int = 15,
    ) -> dict[str, Any]:
        """Search plant names and taxa in the Royal Botanic Gardens Kew POWO database."""
        try:
            results = api.search_plants(query=query, accepted_only=accepted_only, limit=limit)
            lines = [
                f"- {item.get('scientific_name')} ({item.get('family')}) "
                f"[{item.get('taxonomic_status')}] [id: {item.get('fq_id')}]"
                for item in results[:10]
            ]
            summary = "\n".join(lines) if lines else f"No plant taxa found matching '{query}'."
            return {"results": results, "count": len(results), "summary": summary}
        except PowoError as exc:
            return {
                "error": str(exc),
                "results": [],
                "count": 0,
                "summary": f"Search failed: {exc}",
            }

    @server.tool()
    def get_plant_details(fq_id: str) -> dict[str, Any]:
        """Retrieve lifeform, climate, family, and taxonomic status for a plant by POWO ID."""
        try:
            details = api.get_plant_details(fq_id=fq_id)
            sci = details.get("scientific_name")
            fam = details.get("family")
            life = details.get("lifeform") or "Unknown lifeform"
            climate = details.get("climate") or "Unknown climate"
            status = details.get("status") or "Unknown status"
            summary = f"{sci} ({fam}) - Status: {status} | Lifeform: {life} | Climate: {climate}"
            return {"details": details, "summary": summary}
        except PowoError as exc:
            return {"error": str(exc), "summary": f"Details lookup failed: {exc}"}

    @server.tool()
    def get_plant_distribution(fq_id: str) -> dict[str, Any]:
        """Retrieve native and introduced TDWG geographical distribution for a plant."""
        try:
            dist = api.get_plant_distribution(fq_id=fq_id)
            native_str = ", ".join(dist.get("native_distribution", [])[:5]) or "None listed"
            intro_str = ", ".join(dist.get("introduced_distribution", [])[:5]) or "None listed"
            summary = (
                f"Distribution for {dist.get('species')}: "
                f"Native ({dist.get('total_native_regions')} regions): {native_str}... | "
                f"Introduced ({dist.get('total_introduced_regions')} regions): {intro_str}..."
            )
            return {"distribution": dist, "summary": summary}
        except PowoError as exc:
            return {"error": str(exc), "summary": f"Distribution lookup failed: {exc}"}

    @server.tool()
    def resolve_plant_synonymy(name: str) -> dict[str, Any]:
        """Check if a botanical name is accepted or a synonym of another accepted species."""
        try:
            res = api.resolve_plant_synonymy(name=name)
            is_acc = res.get("is_accepted")
            status = "ACCEPTED SPECIES" if is_acc else "SYNONYM"
            acc_name = res.get("accepted_scientific_name")
            summary = f"{name} is a {status}. Accepted botanical name: {acc_name}"
            return {"synonymy": res, "summary": summary}
        except PowoError as exc:
            return {"error": str(exc), "summary": f"Synonymy resolution failed: {exc}"}

    return server


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="powo-mcp",
        description="Model Context Protocol (MCP) server for Kew Plants of the World Online",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind for SSE transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for SSE transport (default: 8000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = create_server()
    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="sse", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
