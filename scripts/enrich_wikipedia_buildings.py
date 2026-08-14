#!/usr/bin/env python3
"""Refresh Wikipedia properties in the existing map-ready building dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from scripts.build_building_database import (
        PROCESSED_OUT,
        PUBLIC_OUT,
        WIKIPEDIA_MATCHES_PATH,
        load_approved_wikipedia_matches,
        load_geojson,
        normalize_id,
    )
except ModuleNotFoundError:  # Direct execution sets scripts/ as the import root.
    from build_building_database import (
        PROCESSED_OUT,
        PUBLIC_OUT,
        WIKIPEDIA_MATCHES_PATH,
        load_approved_wikipedia_matches,
        load_geojson,
        normalize_id,
    )


def enrich_wikipedia_properties(
    feature_collection: dict[str, Any],
    approved_by_bldgid: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], int]:
    """Return the collection with publication-approved Wikipedia properties."""
    present_bldgids: set[str] = set()
    linked_features = 0

    for feature in feature_collection["features"]:
        properties = feature.setdefault("properties", {})
        bldgid = normalize_id(properties.get("BldgID"))
        if bldgid:
            present_bldgids.add(bldgid)
        articles = approved_by_bldgid.get(bldgid, [])
        properties["wikipedia_article_count"] = len(articles)
        properties["wikipedia_articles_json"] = (
            json.dumps(articles, ensure_ascii=False, separators=(",", ":"))
            if articles
            else None
        )
        linked_features += int(bool(articles))

    missing = sorted(set(approved_by_bldgid) - present_bldgids)
    if missing:
        raise ValueError(
            "Approved Wikipedia matches reference missing BldgIDs: " + ", ".join(missing)
        )
    return feature_collection, linked_features


def write_geojson(data: dict[str, Any], destinations: tuple[Path, ...]) -> None:
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(destination)


def main() -> None:
    approved = load_approved_wikipedia_matches(WIKIPEDIA_MATCHES_PATH)
    buildings = load_geojson(PROCESSED_OUT)
    output, linked_features = enrich_wikipedia_properties(buildings, approved)
    write_geojson(output, (PROCESSED_OUT, PUBLIC_OUT))

    article_count = sum(len(items) for items in approved.values())
    print(f"Approved Wikipedia articles: {article_count:,}")
    print(f"Approved BldgIDs: {len(approved):,}")
    print(f"Linked GeoJSON features: {linked_features:,}")
    print(f"Wrote {PROCESSED_OUT}")
    print(f"Wrote {PUBLIC_OUT}")


if __name__ == "__main__":
    main()
