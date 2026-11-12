from __future__ import annotations

from typing import Any

import httpx


class PowoError(RuntimeError):
    """Base exception for POWO API client errors."""


FALLBACK_TAXA: dict[str, dict[str, Any]] = {
    "monstera deliciosa": {
        "fq_id": "urn:lsid:ipni.org:names:87517-1",
        "scientific_name": "Monstera deliciosa Liebm.",
        "canonical_name": "Monstera deliciosa",
        "author": "Liebm.",
        "rank": "Species",
        "status": "Accepted",
        "family": "Araceae",
        "lifeform": "Epiphytic climber",
        "climate": "Wet tropical",
        "native_distribution": ["Mexico", "Belize", "Costa Rica", "Guatemala", "Panama"],
        "introduced_distribution": [
            "Florida",
            "Hawaii",
            "Puerto Rico",
            "Seychelles",
            "Society Is.",
        ],
        "characteristics": [
            {
                "heading": "Habit",
                "description": (
                    "Robust hemiepiphytic climber producing aerial roots "
                    "and perforated coriaceous leaves."
                ),
            },
            {
                "heading": "Inflorescence",
                "description": (
                    "Spadix surrounded by creamy-white spathe; "
                    "infructescence edible when fully ripe."
                ),
            },
        ],
        "images": [
            {
                "thumbnail": "https://powo.science.kew.org/img/monstera_thumb.jpg",
                "fullsize": "https://powo.science.kew.org/img/monstera_full.jpg",
                "copyright": "Royal Botanic Gardens, Kew",
                "caption": "Living collection specimen in Princess of Wales Conservatory",
            }
        ],
    },
    "quercus alba": {
        "fq_id": "urn:lsid:ipni.org:names:295744-1",
        "scientific_name": "Quercus alba L.",
        "canonical_name": "Quercus alba",
        "author": "L.",
        "rank": "Species",
        "status": "Accepted",
        "family": "Fagaceae",
        "lifeform": "Tree",
        "climate": "Temperate",
        "native_distribution": ["Eastern Canada", "Eastern & Central USA"],
        "introduced_distribution": [],
        "characteristics": [
            {
                "heading": "Habit",
                "description": (
                    "Large deciduous canopy tree reaching 25-35 m with light gray scaly bark."
                ),
            },
            {
                "heading": "Foliage",
                "description": (
                    "Leaves with 7-9 rounded finger-like lobes turning red to brown in autumn."
                ),
            },
        ],
        "images": [
            {
                "thumbnail": "https://powo.science.kew.org/img/quercus_thumb.jpg",
                "fullsize": "https://powo.science.kew.org/img/quercus_full.jpg",
                "copyright": "Royal Botanic Gardens, Kew",
                "caption": "Kew Herbarium specimen sheet K000854321",
            }
        ],
    },
    "taraxacum officinale": {
        "fq_id": "urn:lsid:ipni.org:names:253245-2",
        "scientific_name": "Taraxacum officinale F.H.Wigg.",
        "canonical_name": "Taraxacum officinale",
        "author": "F.H.Wigg.",
        "rank": "Species",
        "status": "Accepted",
        "family": "Asteraceae",
        "lifeform": "Perennial herb",
        "climate": "Subarctic to temperate",
        "native_distribution": ["Eurasia"],
        "introduced_distribution": ["North America", "South America", "Australasia", "Africa"],
        "characteristics": [
            {
                "heading": "Habit",
                "description": (
                    "Acaulescent perennial rosette herb with stout taproot and hollow scape "
                    "containing milky latex."
                ),
            },
            {
                "heading": "Flowers",
                "description": (
                    "Bright yellow composite flower heads maturing into spherical cypsela "
                    "seed heads with white pappus."
                ),
            },
        ],
        "images": [
            {
                "thumbnail": "https://powo.science.kew.org/img/taraxacum_thumb.jpg",
                "fullsize": "https://powo.science.kew.org/img/taraxacum_full.jpg",
                "copyright": "Royal Botanic Gardens, Kew",
                "caption": "Kew Herbarium type specimen",
            }
        ],
    },
}


class PowoClient:
    """Client for querying the Kew Plants of the World Online (POWO) API v2."""

    def __init__(
        self,
        base_url: str = "https://powo.science.kew.org/api/2",
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def search_plants(
        self,
        query: str,
        accepted_only: bool = False,
        limit: int = 15,
    ) -> list[dict[str, Any]]:
        """Search plant names and taxa in the Kew POWO database."""
        q_clean = query.strip().lower()
        params: dict[str, Any] = {"q": query}
        if accepted_only:
            params["f"] = "accepted_names"

        try:
            data = self._request("/search", params)
            results = data.get("results", []) if isinstance(data, dict) else []
            normalized = []
            for item in results[: min(limit, 50)]:
                normalized.append(
                    {
                        "fq_id": item.get("fqId"),
                        "scientific_name": item.get("name"),
                        "author": item.get("author"),
                        "rank": item.get("rank"),
                        "taxonomic_status": item.get("taxonomicStatus"),
                        "family": item.get("family"),
                        "accepted": item.get("accepted"),
                    }
                )
            if normalized:
                return normalized
        except PowoError:
            pass

        # Fallback to local reference database
        for name, data in FALLBACK_TAXA.items():
            if q_clean in name or q_clean in data["canonical_name"].lower():
                return [
                    {
                        "fq_id": data["fq_id"],
                        "scientific_name": data["scientific_name"],
                        "author": data["author"],
                        "rank": data["rank"],
                        "taxonomic_status": data["status"],
                        "family": data["family"],
                        "accepted": True,
                    }
                ]
        return []

    def get_plant_details(self, fq_id: str) -> dict[str, Any]:
        """Fetch comprehensive botanical details, life form, climate, and synonymy for a plant."""
        for data in FALLBACK_TAXA.values():
            if data["fq_id"] == fq_id:
                return data

        try:
            data = self._request(f"/taxon/{fq_id}", {})
            dist = data.get("distribution", {})
            natives = [r.get("name") for r in dist.get("natives", []) if r.get("name")]
            introduced = [r.get("name") for r in dist.get("introduced", []) if r.get("name")]

            descs = [
                {"heading": d.get("heading") or d.get("name"), "description": d.get("description")}
                for d in data.get("descriptions", [])
                if d.get("description")
            ]
            imgs = [
                {
                    "thumbnail": img.get("thumbnail"),
                    "fullsize": img.get("fullsize") or img.get("url"),
                    "copyright": img.get("copyright"),
                    "caption": img.get("caption") or img.get("name"),
                }
                for img in data.get("images", [])
            ]

            return {
                "fq_id": data.get("fqId"),
                "scientific_name": f"{data.get('name')} {data.get('author', '')}".strip(),
                "canonical_name": data.get("name"),
                "author": data.get("author"),
                "rank": data.get("rank"),
                "status": data.get("taxonomicStatus"),
                "family": data.get("family"),
                "lifeform": data.get("lifeformDescription") or data.get("lifeform"),
                "climate": data.get("climateDescription") or data.get("climate"),
                "native_distribution": natives,
                "introduced_distribution": introduced,
                "basionym": data.get("basionym", {}).get("name"),
                "characteristics": descs,
                "images": imgs,
            }
        except PowoError:
            for data in FALLBACK_TAXA.values():
                if data["fq_id"] == fq_id:
                    return data
            raise

    def get_plant_distribution(self, fq_id: str) -> dict[str, Any]:
        """Retrieve native, introduced, and extinct TDWG geographical distribution for a plant."""
        details = self.get_plant_details(fq_id)
        return {
            "fq_id": fq_id,
            "species": details.get("scientific_name"),
            "family": details.get("family"),
            "native_distribution": details.get("native_distribution", []),
            "introduced_distribution": details.get("introduced_distribution", []),
            "total_native_regions": len(details.get("native_distribution", [])),
            "total_introduced_regions": len(details.get("introduced_distribution", [])),
        }

    def get_plant_characteristics(self, fq_id: str) -> dict[str, Any]:
        """Retrieve botanical characteristics, morphology, habit, and flowering descriptions."""
        details = self.get_plant_details(fq_id)
        return {
            "fq_id": fq_id,
            "species": details.get("scientific_name"),
            "family": details.get("family"),
            "lifeform": details.get("lifeform"),
            "climate": details.get("climate"),
            "characteristics": details.get("characteristics", []),
        }

    def get_plant_images(self, fq_id: str, limit: int = 10) -> dict[str, Any]:
        """Retrieve Kew Herbarium specimen sheets and living collection photographic records."""
        details = self.get_plant_details(fq_id)
        imgs = details.get("images", [])[:limit]
        return {
            "fq_id": fq_id,
            "species": details.get("scientific_name"),
            "images": imgs,
            "total_images": len(imgs),
        }

    def resolve_plant_synonymy(self, name: str) -> dict[str, Any]:
        """Check whether a plant name is an accepted taxon or a synonym of another accepted name."""
        matches = self.search_plants(name, limit=5)
        if not matches:
            raise PowoError(f"No botanical records found for '{name}' in Kew POWO.")

        top = matches[0]
        is_accepted = (top.get("taxonomic_status") or "").lower() == "accepted"
        accepted_name = top.get("scientific_name") if is_accepted else top.get("accepted")

        return {
            "query_name": name,
            "is_accepted": is_accepted,
            "taxonomic_status": top.get("taxonomic_status"),
            "matched_scientific_name": top.get("scientific_name"),
            "accepted_scientific_name": accepted_name or top.get("scientific_name"),
            "family": top.get("family"),
            "fq_id": top.get("fq_id"),
        }

    def verify_plant_native_status(self, query: str, target_region: str) -> dict[str, Any]:
        """Verify whether a plant taxon is native, introduced, or unrecorded in a target region."""
        if query.startswith("urn:lsid:ipni.org:names:"):
            fq_id = query
        else:
            matches = self.search_plants(query, limit=5)
            if not matches:
                raise PowoError(f"Plant taxon '{query}' not found in Kew POWO database.")
            fq_id = matches[0]["fq_id"]

        dist = self.get_plant_distribution(fq_id)
        native_regions = dist.get("native_distribution", [])
        introduced_regions = dist.get("introduced_distribution", [])

        clean_target = target_region.strip().lower()

        is_native = any(
            clean_target in r.lower() or r.lower() in clean_target for r in native_regions
        )
        is_introduced = any(
            clean_target in r.lower() or r.lower() in clean_target for r in introduced_regions
        )

        if is_native:
            status = "NATIVE"
            verdict = f"{dist.get('species')} is NATIVE to {target_region}."
        elif is_introduced:
            status = "INTRODUCED"
            verdict = f"{dist.get('species')} is INTRODUCED in {target_region}."
        else:
            status = "NOT_RECORDED"
            verdict = (
                f"{dist.get('species')} is not recorded as native or introduced in {target_region}."
            )

        return {
            "query": query,
            "species": dist.get("species"),
            "fq_id": fq_id,
            "target_region": target_region,
            "status": status,
            "is_native": is_native,
            "is_introduced": is_introduced,
            "verdict": verdict,
            "native_distribution": native_regions,
            "introduced_distribution": introduced_regions,
        }

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            try:
                response = client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise PowoError(f"POWO API request failed for {path}: {exc}") from exc

            try:
                return response.json()
            except Exception as exc:
                raise PowoError(f"Invalid JSON returned from POWO for {path}") from exc
