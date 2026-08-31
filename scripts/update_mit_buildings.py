#!/usr/bin/env python3
"""Refresh the public MIT building polygon metadata snapshot."""

from __future__ import annotations

import json
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/mit-buildings.geojson"
ENDPOINT = "https://maps.mit.edu/pub/rest/services/demos/Map/MapServer/24/query"
FIELDS = "FACILITY,Address,BLDG_NAME,Ownership,Type,Floor_Count,DATE_BUILT"


def date_built_year(value: object) -> int | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).year


def main() -> None:
    query = urllib.parse.urlencode(
        {
            "where": "1=1",
            "outFields": FIELDS,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
    )
    request = urllib.request.Request(
        f"{ENDPOINT}?{query}",
        headers={"User-Agent": "Cambridge-building-map MIT metadata updater"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    if data.get("type") != "FeatureCollection" or not data.get("features"):
        raise ValueError("MIT GIS did not return a non-empty GeoJSON FeatureCollection")
    for feature in data["features"]:
        properties = feature.get("properties") or {}
        properties["DATE_BUILT_YEAR"] = date_built_year(properties.get("DATE_BUILT"))
        feature["properties"] = properties
    data["metadata"] = {
        "source": "MIT Department of Facilities public GIS",
        "source_url": "https://maps.mit.edu/pub/rest/services/demos/Map/MapServer/24",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=OUT.parent, delete=False, encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(OUT)
    print(f"Wrote {len(data['features'])} MIT facilities to {OUT}")


if __name__ == "__main__":
    main()
