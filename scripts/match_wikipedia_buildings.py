#!/usr/bin/env python3
"""Match geotagged Wikipedia articles to Cambridge building footprints."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from numbers import Real
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTICLES_PATH = ROOT / "data/processed/wikipedia-articles.json"
ARTICLE_ADDITIONS_PATH = ROOT / "data/manual/wikipedia-article-additions.json"
BUILDINGS_PATH = ROOT / "cambridgegis_data/Basemap/Buildings/BASEMAP_Buildings.geojson"
CANDIDATES_PATH = ROOT / "data/processed/wikipedia-building-candidates.csv"
REVIEW_PATH = ROOT / "data/processed/wikipedia-matches-to-review.csv"
DECISIONS_PATH = ROOT / "data/manual/wikipedia-building-decisions.json"
PROJECTED_CRS = "EPSG:26986"  # NAD83 / Massachusetts Mainland, meters
NEAREST_THRESHOLD_METERS = 25.0
MATERIAL_MOVE_METERS = 5.0

COLUMNS = [
    "wikipedia_page_id", "wikipedia_title", "wikipedia_url", "latitude", "longitude",
    "match_method", "match_distance_meters", "candidate_count", "candidate_bldgids",
    "matched_bldgid", "confidence_status", "decision_status", "review_reason",
    "previous_title", "previous_latitude", "previous_longitude",
]


def load_articles(
    path: Path, additions_path: Path | None = None
) -> gpd.GeoDataFrame:
    with path.open(encoding="utf-8-sig") as handle:
        snapshot = json.load(handle)
    articles = snapshot.get("articles")
    if snapshot.get("schema_version") != 1 or not isinstance(articles, list):
        raise ValueError(f"Unsupported Wikipedia article snapshot: {path}")
    if additions_path is not None:
        with additions_path.open(encoding="utf-8-sig") as handle:
            additions = json.load(handle)
        added_articles = additions.get("articles")
        if additions.get("version") != 1 or not isinstance(added_articles, list):
            raise ValueError(f"Unsupported manual Wikipedia additions: {additions_path}")
        articles = [*articles, *added_articles]
    frame = pd.DataFrame(articles)
    required = {"page_id", "title", "url", "latitude", "longitude"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Wikipedia snapshot is missing fields: {sorted(required - set(frame.columns))}")
    if frame["page_id"].duplicated().any():
        raise ValueError("Wikipedia snapshot contains duplicate page IDs")
    return gpd.GeoDataFrame(
        frame,
        geometry=gpd.points_from_xy(frame["longitude"], frame["latitude"]),
        crs="EPSG:4326",
    )


def load_buildings(path: Path) -> gpd.GeoDataFrame:
    buildings = gpd.read_file(path)[["BldgID", "geometry"]].copy()
    buildings["BldgID"] = buildings["BldgID"].astype(str).str.strip()
    if buildings["BldgID"].eq("").any():
        raise ValueError("Building footprints require non-empty BldgID values")
    if buildings.crs is None:
        raise ValueError("Building footprints have no declared coordinate reference system")
    invalid = ~buildings.geometry.is_valid
    if invalid.any():
        buildings.loc[invalid, "geometry"] = buildings.loc[invalid, "geometry"].make_valid()
    # A small number of logical buildings have multiple separate footprint
    # features with the same BldgID. Dissolve them so BldgID remains the stable
    # matching and enrichment key used by the rest of the project.
    return buildings.dissolve(by="BldgID", as_index=False).to_crs(PROJECTED_CRS)


def load_decisions(path: Path) -> dict[int, dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    decisions = data.get("decisions")
    if data.get("version") != 1 or not isinstance(decisions, list):
        raise ValueError(f"Unsupported Wikipedia decision file: {path}")
    by_page_id: dict[int, dict[str, Any]] = {}
    for decision in decisions:
        page_id = decision.get("wikipedia_page_id")
        outcome = decision.get("decision")
        bldgid = decision.get("bldgid")
        if not isinstance(page_id, int) or page_id <= 0 or page_id in by_page_id:
            raise ValueError(f"Decision page IDs must be unique positive integers: {page_id!r}")
        if outcome not in {"approved", "rejected"}:
            raise ValueError(f"Invalid decision for Wikipedia page {page_id}: {outcome!r}")
        if outcome == "approved" and (not isinstance(bldgid, str) or not bldgid.strip()):
            raise ValueError(f"Approved Wikipedia page {page_id} requires bldgid")
        by_page_id[page_id] = decision
    return by_page_id


def coordinate_move_meters(article: pd.Series, decision: dict[str, Any]) -> float | None:
    old_latitude = decision.get("latitude")
    old_longitude = decision.get("longitude")
    if not isinstance(old_latitude, Real) or not isinstance(old_longitude, Real):
        return None
    old_latitude_radians = math.radians(float(old_latitude))
    current_latitude_radians = math.radians(float(article["latitude"]))
    latitude_delta = current_latitude_radians - old_latitude_radians
    longitude_delta = math.radians(float(article["longitude"]) - float(old_longitude))
    haversine = math.sin(latitude_delta / 2) ** 2 + (
        math.cos(old_latitude_radians)
        * math.cos(current_latitude_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * 6_371_008.8 * math.asin(math.sqrt(haversine))


def candidate_ids(joined: gpd.GeoDataFrame) -> dict[int, list[str]]:
    found: dict[int, list[str]] = {}
    for article_index, group in joined.dropna(subset=["BldgID"]).groupby(level=0):
        found[int(article_index)] = sorted(set(group["BldgID"].astype(str)))
    return found


def match_articles(
    articles: gpd.GeoDataFrame,
    buildings: gpd.GeoDataFrame,
    decisions: dict[int, dict[str, Any]] | None = None,
    nearest_threshold_meters: float = NEAREST_THRESHOLD_METERS,
) -> list[dict[str, Any]]:
    decisions = decisions or {}
    valid_bldgids = set(buildings["BldgID"].astype(str))
    articles_projected = articles.to_crs(PROJECTED_CRS)
    contained_join = gpd.sjoin(
        articles_projected,
        buildings,
        how="left",
        predicate="intersects",
    )
    contained_by_article = candidate_ids(contained_join)
    unmatched_indices = [index for index in articles_projected.index if index not in contained_by_article]
    nearest_by_article: dict[int, tuple[str, float]] = {}
    if unmatched_indices:
        nearest = gpd.sjoin_nearest(
            articles_projected.loc[unmatched_indices],
            buildings,
            how="left",
            max_distance=nearest_threshold_meters,
            distance_col="distance_meters",
        )
        for index, row in nearest.dropna(subset=["BldgID"]).iterrows():
            candidate = (str(row["BldgID"]), float(row["distance_meters"]))
            current = nearest_by_article.get(int(index))
            if current is None or candidate[1:] < current[1:] or (candidate[1] == current[1] and candidate[0] < current[0]):
                nearest_by_article[int(index)] = candidate

    rows = []
    for index, article in articles.iterrows():
        contained = contained_by_article.get(int(index), [])
        if contained:
            method = "contained"
            distance: float | None = 0.0
            candidates = contained
            matched = contained[0] if len(contained) == 1 else ""
            confidence = "strong" if len(contained) == 1 else "ambiguous"
            reason = (
                "Article coordinate is contained by exactly one building footprint."
                if len(contained) == 1
                else "Article coordinate intersects multiple building footprints."
            )
        elif int(index) in nearest_by_article:
            matched, distance = nearest_by_article[int(index)]
            method, candidates, confidence = "nearest", [matched], "ambiguous"
            reason = f"Nearest footprint is within {nearest_threshold_meters:g} meters and requires review."
        else:
            method, distance, candidates, matched, confidence = "none", None, [], "", "unmatched"
            reason = f"No building footprint is within {nearest_threshold_meters:g} meters."
        decision = decisions.get(int(article["page_id"]))
        # Spatial confidence is evidence for review, not editorial approval.
        # Only an explicit, current human decision may publish an article.
        decision_status = "needs_review"
        previous_title: Any = ""
        previous_latitude: Any = ""
        previous_longitude: Any = ""
        if decision:
            previous_title = decision.get("wikipedia_title", "")
            previous_latitude = decision.get("latitude", "")
            previous_longitude = decision.get("longitude", "")
            move_distance = coordinate_move_meters(article, decision)
            target = str(decision.get("bldgid") or "").strip()
            stale_reason = ""
            if move_distance is not None and move_distance > MATERIAL_MOVE_METERS:
                stale_reason = f"Article coordinate moved {move_distance:.2f} meters since review."
            elif decision["decision"] == "approved" and target not in valid_bldgids:
                stale_reason = "Previously approved BldgID no longer exists."
            elif (
                decision["decision"] == "approved"
                and decision.get("selection_method") != "manual_marker"
                and target not in candidates
            ):
                stale_reason = "Previously approved BldgID is no longer a current spatial candidate."
            elif decision["decision"] == "rejected" and move_distance is None:
                stale_reason = "Prior rejection lacks reviewed coordinates and cannot be verified."
            if stale_reason:
                decision_status = "stale_decision"
                reason = stale_reason
            else:
                decision_status = decision["decision"]
                if decision_status == "approved":
                    matched = target
                reason = f"Preserved human {decision_status} decision."
        rows.append({
            "wikipedia_page_id": int(article["page_id"]),
            "wikipedia_title": article["title"],
            "wikipedia_url": article["url"],
            "latitude": article["latitude"],
            "longitude": article["longitude"],
            "match_method": method,
            "match_distance_meters": "" if distance is None else f"{distance:.2f}",
            "candidate_count": len(candidates),
            "candidate_bldgids": "|".join(candidates),
            "matched_bldgid": matched,
            "confidence_status": confidence,
            "decision_status": decision_status,
            "review_reason": reason,
            "previous_title": previous_title if previous_title != article["title"] else "",
            "previous_latitude": previous_latitude,
            "previous_longitude": previous_longitude,
        })
    return rows


def missing_decision_rows(
    decisions: dict[int, dict[str, Any]], current_page_ids: set[int]
) -> list[dict[str, Any]]:
    rows = []
    for page_id in sorted(decisions.keys() - current_page_ids):
        decision = decisions[page_id]
        rows.append({
            "wikipedia_page_id": page_id,
            "wikipedia_title": decision.get("wikipedia_title", ""),
            "wikipedia_url": decision.get("wikipedia_url", ""),
            "latitude": "", "longitude": "", "match_method": "none",
            "match_distance_meters": "", "candidate_count": 0, "candidate_bldgids": "",
            "matched_bldgid": decision.get("bldgid") or "", "confidence_status": "unmatched",
            "decision_status": "stale_decision",
            "review_reason": "Previously reviewed article is missing from the latest Cambridge snapshot.",
            "previous_title": decision.get("wikipedia_title", ""),
            "previous_latitude": decision.get("latitude", ""),
            "previous_longitude": decision.get("longitude", ""),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", type=Path, default=ARTICLES_PATH)
    parser.add_argument(
        "--article-additions", type=Path, default=ARTICLE_ADDITIONS_PATH
    )
    parser.add_argument("--buildings", type=Path, default=BUILDINGS_PATH)
    parser.add_argument("--candidates-output", type=Path, default=CANDIDATES_PATH)
    parser.add_argument("--review-output", type=Path, default=REVIEW_PATH)
    parser.add_argument("--decisions", type=Path, default=DECISIONS_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    articles = load_articles(args.articles, args.article_additions)
    decisions = load_decisions(args.decisions)
    rows = match_articles(articles, load_buildings(args.buildings), decisions)
    rows.extend(missing_decision_rows(decisions, set(articles["page_id"].astype(int))))
    rows.sort(key=lambda row: int(row["wikipedia_page_id"]))
    write_csv(args.candidates_output, rows)
    review_rows = [row for row in rows if row["decision_status"] in {"needs_review", "stale_decision"}]
    write_csv(args.review_output, review_rows)
    counts = Counter(row["match_method"] for row in rows)
    print(f"Wikipedia articles: {len(rows):,}")
    print(f"Contained matches: {counts['contained']:,}")
    print(f"Nearest matches: {counts['nearest']:,}")
    print(f"Unmatched: {counts['none']:,}")
    decisions_counts = Counter(row["decision_status"] for row in rows)
    print(f"Approved: {decisions_counts['approved']:,}")
    print(f"Rejected: {decisions_counts['rejected']:,}")
    print(f"Stale decisions: {decisions_counts['stale_decision']:,}")
    print(f"Review rows: {len(review_rows):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
