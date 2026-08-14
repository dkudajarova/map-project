#!/usr/bin/env python3
"""Download and geographically filter English Wikipedia articles for Cambridge."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://en.wikipedia.org/w/api.php"
BOUNDARY_PATH = (
    ROOT
    / "cambridgegis_data/Boundary/City_Boundary/BOUNDARY_CityBoundary.geojson"
)
OUTPUT_PATH = ROOT / "data/processed/wikipedia-articles.json"
MAX_RADIUS_METERS = 10_000
SEARCH_MARGIN_METERS = 250
PAGE_LIMIT = 500
TILE_SIZE_METERS = 1_000
REQUEST_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 4

JsonObject = dict[str, Any]
OpenUrl = Callable[[Request, float], JsonObject]


def load_feature_collection(path: Path) -> JsonObject:
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if data.get("type") != "FeatureCollection" or not isinstance(
        data.get("features"), list
    ):
        raise ValueError(f"Expected a GeoJSON FeatureCollection: {path}")
    return data


def iter_rings(geometry: JsonObject) -> Iterable[list[list[float]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon" and isinstance(coordinates, list):
        yield from coordinates
    elif geometry_type == "MultiPolygon" and isinstance(coordinates, list):
        for polygon in coordinates:
            yield from polygon
    else:
        raise ValueError(f"Unsupported boundary geometry: {geometry_type!r}")


def boundary_polygons(boundary: JsonObject) -> list[list[list[list[float]]]]:
    polygons: list[list[list[list[float]]]] = []
    for feature in boundary["features"]:
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if geometry_type == "Polygon" and isinstance(coordinates, list):
            polygons.append(coordinates)
        elif geometry_type == "MultiPolygon" and isinstance(coordinates, list):
            polygons.extend(coordinates)
        else:
            raise ValueError(f"Unsupported boundary geometry: {geometry_type!r}")
    if not polygons:
        raise ValueError("Cambridge boundary contains no polygons")
    return polygons


def point_on_segment(
    longitude: float,
    latitude: float,
    start: list[float],
    end: list[float],
    tolerance: float = 1e-12,
) -> bool:
    start_x, start_y = start[:2]
    end_x, end_y = end[:2]
    cross = (longitude - start_x) * (end_y - start_y) - (
        latitude - start_y
    ) * (end_x - start_x)
    if abs(cross) > tolerance:
        return False
    return (
        min(start_x, end_x) - tolerance
        <= longitude
        <= max(start_x, end_x) + tolerance
        and min(start_y, end_y) - tolerance
        <= latitude
        <= max(start_y, end_y) + tolerance
    )


def point_in_ring(longitude: float, latitude: float, ring: list[list[float]]) -> bool:
    inside = False
    for index, start in enumerate(ring):
        end = ring[(index + 1) % len(ring)]
        if point_on_segment(longitude, latitude, start, end):
            return True
        start_x, start_y = start[:2]
        end_x, end_y = end[:2]
        crosses = (start_y > latitude) != (end_y > latitude)
        if crosses:
            intersection_x = (
                (end_x - start_x) * (latitude - start_y) / (end_y - start_y)
                + start_x
            )
            if longitude < intersection_x:
                inside = not inside
    return inside


def point_in_polygon(
    longitude: float, latitude: float, polygon: list[list[list[float]]]
) -> bool:
    if not polygon or not point_in_ring(longitude, latitude, polygon[0]):
        return False
    return not any(
        point_in_ring(longitude, latitude, hole) for hole in polygon[1:]
    )


def point_in_cambridge(
    longitude: float,
    latitude: float,
    polygons: list[list[list[list[float]]]],
) -> bool:
    return any(point_in_polygon(longitude, latitude, polygon) for polygon in polygons)


def haversine_meters(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    earth_radius_meters = 6_371_008.8
    first_latitude_radians = math.radians(first_latitude)
    second_latitude_radians = math.radians(second_latitude)
    latitude_delta = math.radians(second_latitude - first_latitude)
    longitude_delta = math.radians(second_longitude - first_longitude)
    haversine = math.sin(latitude_delta / 2) ** 2 + (
        math.cos(first_latitude_radians)
        * math.cos(second_latitude_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius_meters * math.asin(math.sqrt(haversine))


def search_geometry(boundary: JsonObject) -> tuple[float, float, int]:
    vertices = [
        coordinate
        for feature in boundary["features"]
        for coordinate in iter_rings(feature.get("geometry") or {})
        for coordinate in coordinate
    ]
    if not vertices:
        raise ValueError("Cambridge boundary contains no coordinates")
    longitudes = [float(vertex[0]) for vertex in vertices]
    latitudes = [float(vertex[1]) for vertex in vertices]
    center_longitude = (min(longitudes) + max(longitudes)) / 2
    center_latitude = (min(latitudes) + max(latitudes)) / 2
    radius = math.ceil(
        max(
            haversine_meters(
                center_latitude,
                center_longitude,
                float(vertex[1]),
                float(vertex[0]),
            )
            for vertex in vertices
        )
        + SEARCH_MARGIN_METERS
    )
    if radius > MAX_RADIUS_METERS:
        raise ValueError(
            f"Boundary requires a {radius:,} meter search radius; MediaWiki allows "
            f"at most {MAX_RADIUS_METERS:,} meters"
        )
    return center_latitude, center_longitude, radius


def default_open_url(request: Request, timeout: float) -> JsonObject:
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def request_json(
    request: Request,
    open_url: OpenUrl,
    sleep: Callable[[float], None] = time.sleep,
) -> JsonObject:
    for attempt in range(MAX_ATTEMPTS):
        try:
            return open_url(request, REQUEST_TIMEOUT_SECONDS)
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"MediaWiki request failed with HTTP {error.code}") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"MediaWiki request failed: {error}") from error
        sleep(2**attempt)
    raise AssertionError("unreachable")


def fetch_geosearch_tile(
    bounding_box: tuple[float, float, float, float],
    user_agent: str,
    open_url: OpenUrl = default_open_url,
) -> list[JsonObject]:
    north, west, south, east = bounding_box
    base_params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "list": "geosearch",
        "gsbbox": f"{north:.7f}|{west:.7f}|{south:.7f}|{east:.7f}",
        "gslimit": str(PAGE_LIMIT),
        "gsnamespace": "0",
    }
    query = urlencode(base_params)
    request = Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    payload = request_json(request, open_url)
    if payload.get("error"):
        raise RuntimeError(f"MediaWiki API error: {payload['error']}")
    results = payload.get("query", {}).get("geosearch")
    if not isinstance(results, list):
        raise RuntimeError("MediaWiki response did not contain query.geosearch")
    if len(results) >= PAGE_LIMIT:
        raise RuntimeError(
            "A Wikipedia search tile reached the 500-result API limit; reduce "
            f"TILE_SIZE_METERS below {TILE_SIZE_METERS} to avoid an incomplete snapshot"
        )

    articles: list[JsonObject] = []
    for result in results:
        page_id = result.get("pageid")
        title = result.get("title")
        latitude = result.get("lat")
        longitude = result.get("lon")
        if (
            not isinstance(page_id, int)
            or page_id <= 0
            or not isinstance(title, str)
            or not title.strip()
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
        ):
            raise RuntimeError(f"Malformed MediaWiki geosearch result: {result!r}")
        articles.append(
            {
                "page_id": page_id,
                "title": title,
                "url": f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='()/,:')}",
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    return articles


def boundary_tiles(boundary: JsonObject) -> list[tuple[float, float, float, float]]:
    vertices = [
        vertex
        for feature in boundary["features"]
        for ring in iter_rings(feature.get("geometry") or {})
        for vertex in ring
    ]
    longitudes = [float(vertex[0]) for vertex in vertices]
    latitudes = [float(vertex[1]) for vertex in vertices]
    west, east = min(longitudes), max(longitudes)
    south, north = min(latitudes), max(latitudes)
    middle_latitude = (south + north) / 2
    height_meters = haversine_meters(south, west, north, west)
    width_meters = haversine_meters(middle_latitude, west, middle_latitude, east)
    row_count = max(1, math.ceil(height_meters / TILE_SIZE_METERS))
    column_count = max(1, math.ceil(width_meters / TILE_SIZE_METERS))
    latitude_step = (north - south) / row_count
    longitude_step = (east - west) / column_count
    return [
        (
            north - row * latitude_step,
            west + column * longitude_step,
            north - (row + 1) * latitude_step,
            west + (column + 1) * longitude_step,
        )
        for row in range(row_count)
        for column in range(column_count)
    ]


def fetch_articles(
    boundary: JsonObject,
    user_agent: str,
    open_url: OpenUrl = default_open_url,
) -> tuple[list[JsonObject], int]:
    tiles = boundary_tiles(boundary)
    articles_by_page_id: dict[int, JsonObject] = {}
    for tile in tiles:
        for article in fetch_geosearch_tile(tile, user_agent, open_url):
            articles_by_page_id[article["page_id"]] = article
    return (
        [articles_by_page_id[key] for key in sorted(articles_by_page_id)],
        len(tiles),
    )


def build_snapshot(
    articles: list[JsonObject],
    polygons: list[list[list[list[float]]]],
    retrieved_at: str,
    center_latitude: float,
    center_longitude: float,
    radius_meters: int,
    tile_count: int,
) -> JsonObject:
    filtered_articles = [
        article
        for article in articles
        if point_in_cambridge(
            float(article["longitude"]), float(article["latitude"]), polygons
        )
    ]
    return {
        "schema_version": 1,
        "retrieved_at": retrieved_at,
        "source": {
            "api": API_URL,
            "language": "en",
            "query": "geosearch",
            "search_center": {
                "latitude": round(center_latitude, 7),
                "longitude": round(center_longitude, 7),
            },
            "search_radius_meters": radius_meters,
            "search_tile_size_meters": TILE_SIZE_METERS,
            "search_tile_count": tile_count,
            "retrieved_count": len(articles),
            "cambridge_count": len(filtered_articles),
        },
        "articles": filtered_articles,
    }


def write_json_atomically(path: Path, data: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, default=BOUNDARY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--user-agent",
        default=os.environ.get("WIKIMEDIA_USER_AGENT"),
        help="Identifying Wikimedia user agent with contact information; may also be set with WIKIMEDIA_USER_AGENT",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.user_agent or not args.user_agent.strip():
        print(
            "error: provide --user-agent or WIKIMEDIA_USER_AGENT with project contact information",
            file=sys.stderr,
        )
        return 2

    boundary = load_feature_collection(args.boundary)
    polygons = boundary_polygons(boundary)
    center_latitude, center_longitude, radius_meters = search_geometry(boundary)
    articles, tile_count = fetch_articles(boundary, args.user_agent.strip())
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )
    snapshot = build_snapshot(
        articles,
        polygons,
        retrieved_at,
        center_latitude,
        center_longitude,
        radius_meters,
        tile_count,
    )
    write_json_atomically(args.output, snapshot)
    source = snapshot["source"]
    print(f"Retrieved articles: {source['retrieved_count']:,}")
    print(f"Articles inside Cambridge: {source['cambridge_count']:,}")
    print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
