"""Load and match completed Cambridge Development Log projects to footprints."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.strtree import STRtree


MINIMUM_YEAR = 1997
MAXIMUM_POINT_DISTANCE_METERS = 40


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def normalize_map_lot(value: Any) -> str:
    return re.sub(r"\s+", "", _text(value)).upper()


def completed_year(row: dict[str, str]) -> int | None:
    status = _text(row.get("Status") or row.get("Project Stage")).casefold()
    raw_year = _text(row.get("Year Complete"))
    if status != "complete" or not re.fullmatch(r"\d{4}", raw_year):
        return None
    year = int(raw_year)
    return year if MINIMUM_YEAR <= year <= date.today().year else None


def _project_id(row: dict[str, str]) -> str:
    return _text(row.get("Project ID") or row.get("ProjectID"))


def _coordinates(row: dict[str, str]) -> tuple[float, float] | None:
    try:
        latitude = float(_text(row.get("Latitude")))
        longitude = float(_text(row.get("Longitude")))
    except ValueError:
        return None
    if not (42.2 <= latitude <= 42.5 and -71.3 <= longitude <= -70.9):
        return None
    return longitude, latitude


@dataclass(frozen=True)
class DevelopmentProject:
    project_id: str
    project_name: str
    address: str
    street_number: str
    street_name: str
    map_lot: str
    year_complete: int
    longitude: float | None
    latitude: float | None
    dataset: str


def load_completed_projects(directory: Path) -> list[DevelopmentProject]:
    """Read the newest snapshot of each Development Log table.

    Rows from the map-lot table supersede duplicate historical project rows.
    """
    patterns = {
        "map_lots": "Development_Log_MapLots_*.csv",
        "historical": "Development_Log_Historical_Projects_*.csv",
        "current": "Development_Log_Current_Edition_*.csv",
    }
    selected: list[tuple[str, Path]] = []
    for dataset, pattern in patterns.items():
        matches = sorted(directory.glob(pattern))
        if matches:
            selected.append((dataset, matches[-1]))

    projects: dict[str, DevelopmentProject] = {}
    map_lot_project_ids: set[str] = set()
    map_lot_path = next((path for dataset, path in selected if dataset == "map_lots"), None)
    if map_lot_path:
        with map_lot_path.open(newline="", encoding="utf-8-sig") as handle:
            map_lot_project_ids = {
                _project_id(row)
                for row in csv.DictReader(handle)
                if completed_year(row) is not None and _project_id(row)
            }
    for dataset, path in selected:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                year = completed_year(row)
                if year is None:
                    continue
                project_id = _project_id(row)
                if dataset != "map_lots" and project_id in map_lot_project_ids:
                    continue
                map_lot = normalize_map_lot(row.get("Map-Lot"))
                key = f"{project_id}|{map_lot}" if map_lot else (
                    project_id or f"{_text(row.get('Address'))}|{year}"
                )
                coordinates = _coordinates(row)
                projects[key] = DevelopmentProject(
                    project_id=project_id,
                    project_name=_text(row.get("Project Name")),
                    address=_text(row.get("Address")),
                    street_number=_text(row.get("Street Number")),
                    street_name=_text(row.get("Street Name")),
                    map_lot=map_lot,
                    year_complete=year,
                    longitude=coordinates[0] if coordinates else None,
                    latitude=coordinates[1] if coordinates else None,
                    dataset=dataset,
                )
    return list(projects.values())


def match_projects_to_footprints(
    projects: list[DevelopmentProject],
    footprints: dict[str, Any],
    points: list[dict[str, Any]],
    normalize_street: Callable[[Any], str],
    normalize_house: Callable[[Any], str],
) -> tuple[dict[str, list[DevelopmentProject]], dict[str, int]]:
    """Match projects by map-lot, then exact address, then a conservative point join."""
    points_by_lot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    points_by_address: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        points_by_lot[normalize_map_lot(point.get("gisid"))].append(point)
        points_by_address[(point.get("street", ""), point.get("house", ""))].append(point)

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:26986", always_xy=True)
    geometries: list[Any] = []
    geometry_bldgids: list[str] = []
    geometry_by_bldgid: dict[str, Any] = {}
    for feature in footprints.get("features", []):
        bldgid = _text((feature.get("properties") or {}).get("BldgID"))
        if bldgid and feature.get("geometry"):
            geometry = transform(transformer.transform, shape(feature["geometry"]))
            geometries.append(geometry)
            geometry_bldgids.append(bldgid)
            geometry_by_bldgid[bldgid] = geometry
    tree = STRtree(geometries)

    matched: dict[str, list[DevelopmentProject]] = defaultdict(list)
    counts: dict[str, int] = defaultdict(int)
    for project in projects:
        point = None
        if project.longitude is not None and project.latitude is not None:
            point = transform(
                transformer.transform, Point(project.longitude, project.latitude)
            )

        candidates: set[str] = set()
        method = ""
        if project.map_lot:
            candidates = {
                _text(item.get("bldgid"))
                for item in points_by_lot.get(project.map_lot, [])
                if _text(item.get("bldgid")) in geometry_by_bldgid
            }
            method = "map_lot"

        if not candidates and project.street_number and project.street_name:
            house = normalize_house(project.street_number)
            street = normalize_street(project.street_name)
            candidates = {
                _text(item.get("bldgid"))
                for item in points_by_address.get((street, house), [])
                if _text(item.get("bldgid")) in geometry_by_bldgid
            }
            method = "address"

        if candidates:
            if point is not None and len(candidates) > 1:
                bldgid = min(candidates, key=lambda value: point.distance(geometry_by_bldgid[value]))
            else:
                bldgid = sorted(candidates)[0]
            matched[bldgid].append(project)
            counts[method] += 1
            continue

        if point is not None and geometries:
            nearest_index = int(tree.nearest(point))
            if point.distance(geometries[nearest_index]) <= MAXIMUM_POINT_DISTANCE_METERS:
                matched[geometry_bldgids[nearest_index]].append(project)
                counts["coordinate"] += 1
                continue
        counts["unmatched"] += 1
    return dict(matched), dict(counts)


def choose_project(projects: list[DevelopmentProject]) -> DevelopmentProject | None:
    if not projects:
        return None
    dataset_priority = {"historical": 0, "current": 1, "map_lots": 2}
    return max(
        projects,
        key=lambda project: (
            project.year_complete,
            dataset_priority.get(project.dataset, -1),
            project.project_id,
        ),
    )
