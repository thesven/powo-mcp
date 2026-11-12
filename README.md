# powo-mcp

[![CI](https://github.com/thesven/powo-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/thesven/powo-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A dedicated **Model Context Protocol (MCP)** server for the Royal Botanic Gardens, Kew [Plants of the World Online (POWO)](https://powo.science.kew.org/) database.

Provides authoritative botanical taxonomy, accepted species resolution, lifeform/climate details, and TDWG geographical distribution (native vs. introduced ranges) across the world's flora.

---

## Key Features

- **Native Status & Provenance Verifier**: Directly verify whether a plant is native, introduced, or unrecorded in a given country or region.
- **Accepted Name & Synonymy Resolution**: Determine whether a botanical name is valid or an outdated synonym, linking directly to the currently accepted taxon.
- **TDWG Botanical Distribution**: Inspect native vs. introduced/naturalized geographic regions based on international Biodiversity Information Standards (TDWG).
- **Botanical Metadata**: Extract lifeform descriptions (e.g., *epiphytic climber*, *perennial herb*, *deciduous tree*) and climate preferences.
- **Kew & IPNI Cross-Referencing**: Resolves stable Kew URN/IPNI identifiers to cross-link with Pl@ntNet, GBIF, and iNaturalist.
- **Zero-Credential Access**: Works out of the box using Kew's public REST API v2 without mandatory API keys.

---

## Available Tools

| Tool | Description |
| :--- | :--- |
| `search_plants` | Search plant names, authors, and families in the Kew POWO database. |
| `get_plant_details` | Retrieve lifeform, climate, family, and taxonomic status for a plant by POWO ID. |
| `get_plant_distribution` | Retrieve native and introduced TDWG geographic distribution lists. |
| `verify_plant_native_status` | Verify whether a plant taxon is native or introduced in a target region or country. |
| `resolve_plant_synonymy` | Check if a botanical name is accepted or an invalid synonym. |
| `get_plant_characteristics` | Retrieve botanical characteristics, morphology, habit, and flowering descriptions. |
| `get_plant_images` | Retrieve Kew Herbarium specimen sheets and living collection photographic records. |

---

## Installation & Usage

### Running with `uvx` (Recommended)

```bash
uvx --from git+https://github.com/thesven/powo-mcp.git powo-mcp
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "powo": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/thesven/powo-mcp.git", "powo-mcp"]
    }
  }
}
```

---

## Development & Quality Gate

```bash
# Run code formatting check
uv run ruff format --check src tests scripts

# Run linting
uv run ruff check src tests scripts

# Run test suite with strict coverage floor (>90%)
uv run pytest --cov=powo_mcp --cov-branch --cov-report=term-missing

# Build wheel and sdist
uv build

# Run package distribution check & smoke test
uv run python scripts/check_dist.py
uv run python scripts/smoke.py
```

## License

MIT License. See [LICENSE](LICENSE) for details.
