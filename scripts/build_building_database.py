#!/usr/bin/env python3
"""Build the footprint-master Cambridge building database.

The Cambridge building footprint layer is the master geometry. Address Points
bridge footprints to assessor GISIDs and provide the deterministic address
candidate index used to match non-razed Hail records.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
HAIL_PATH = ROOT / "data/raw/Hail_buildings_dataset.csv"
ASSESSOR_PATH = ROOT / "data/processed/Cambridge_Property_Database_FY2016-FY2026_20260805_deduped.geojson"
ADDRESS_POINTS_PATH = ROOT / "cambridgegis_data/Address/Address_Points/ADDRESS_AddressPoints.geojson"
FOOTPRINTS_PATH = ROOT / "cambridgegis_data/Basemap/Buildings/BASEMAP_Buildings.geojson"
AGE_BANDS_PATH = ROOT / "src/data/Age_bands.json"
STREET_ALIASES_PATH = ROOT / "data/config/hail-street-aliases.json"
MANUAL_OVERRIDES_PATH = ROOT / "data/manual/hail-building-overrides.json"
PROCESSED_OUT = ROOT / "data/processed/cambridge-buildings-enriched.geojson"
PUBLIC_OUT = ROOT / "public/data/cambridge-buildings.geojson"
MATCH_AUDIT_OUT = ROOT / "data/processed/hail-address-matches.csv"
REVIEW_OUT = ROOT / "data/processed/hail-address-review.csv"
REVIEW_SUMMARY_OUT = ROOT / "data/processed/hail-address-review-summary.md"
REVIEW_BUNDLE_OUT = ROOT / "data/processed/hail-manual-review.json"

STREET_SUFFIXES = {
    "avenue": "ave",
    "boulevard": "blvd",
    "circle": "cir",
    "court": "ct",
    "drive": "dr",
    "highway": "hwy",
    "lane": "ln",
    "parkway": "pkwy",
    "place": "pl",
    "road": "rd",
    "square": "sq",
    "street": "st",
    "terrace": "terr",
}

CLASS_PRIORITY = {
    "Current building": 0,
    "Addition, rear, or secondary building": 1,
    "Building complex": 2,
}

MATCH_COLUMNS = [
    "building_id",
    "hail_address",
    "hail_street_name",
    "classification",
    "construction_year",
    "match_stage",
    "match_status",
    "treatment",
    "candidate_address_point_count",
    "candidate_bldgid_count",
    "candidate_bldgids",
    "candidate_addresses",
    "candidate_street_names",
    "matched_bldgid",
    "match_reason",
    "review_reason_category",
    "review_reason_summary",
    "override_decision",
    "override_note",
    "override_reviewed_at",
    "pre_override_match_stage",
    "pre_override_match_status",
    "pre_override_matched_bldgid",
    "pre_override_candidate_bldgids",
]


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError(f"Expected a GeoJSON FeatureCollection: {path}")
    return data


def text(value: Any) -> str:
    if value is None:
        return ""
    value_text = str(value).strip()
    if value_text.casefold() in {"none", "null", "nan"}:
        return ""
    return value_text


def normalize_id(value: Any) -> str:
    value_text = text(value).upper()
    return value_text[:-2] if value_text.endswith(".0") else value_text


def ascii_words(value: Any) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text(value)).encode("ascii", "ignore").decode().casefold()
    return re.findall(r"[a-z0-9]+", normalized)


def normalize_street(value: Any) -> str:
    words = ascii_words(value)
    return " ".join(STREET_SUFFIXES.get(word, word) for word in words)


def normalize_house(value: Any) -> str:
    value_text = unicodedata.normalize("NFKD", text(value)).encode("ascii", "ignore").decode().casefold()
    value_text = value_text.replace("rear", "r").replace("½", "1/2")
    return re.sub(r"[^a-z0-9/+-]", "", value_text)


@dataclass(frozen=True)
class HouseParts:
    minimum: int | None
    maximum: int | None
    suffix: str
    is_range: bool


def parse_house(value: Any) -> HouseParts:
    normalized = normalize_house(value)
    numbers = [int(item) for item in re.findall(r"\d+", normalized)]
    if not numbers:
        return HouseParts(None, None, "", False)
    first = numbers[0]
    range_match = re.match(r"^0*\d+[a-z]*-0*(\d+)", normalized)
    maximum = int(range_match.group(1)) if range_match else first
    suffix_match = re.match(r"^0*\d+([a-z]+)", normalized)
    suffix = suffix_match.group(1) if suffix_match else ""
    return HouseParts(min(first, maximum), max(first, maximum), suffix, bool(range_match))


def address_numbers(parts: HouseParts) -> set[int]:
    """Return only street numbers that an address or range can represent.

    Cambridge odd and even numbers are on opposite sides of a street. Normal
    ranges whose endpoints have the same parity therefore advance by two:
    215-217 represents 215 and 217, never 216. A malformed/mixed-parity range
    is kept conservative by admitting only its explicitly written endpoints.
    """
    if parts.minimum is None or parts.maximum is None:
        return set()
    if not parts.is_range or parts.minimum == parts.maximum:
        return {parts.minimum}
    if parts.minimum % 2 != parts.maximum % 2:
        return {parts.minimum, parts.maximum}
    return set(range(parts.minimum, parts.maximum + 1, 2))


def house_numbers_overlap(left: HouseParts, right: HouseParts) -> bool:
    return bool(address_numbers(left) & address_numbers(right))


def complete_year(value: Any) -> int | None:
    value_text = text(value)
    if not re.fullmatch(r"\d{4}", value_text):
        return None
    year = int(value_text)
    return year if 1600 <= year <= date.today().year else None


def choose_lowest_address(addresses: Iterable[str]) -> str | None:
    unique = sorted({text(address) for address in addresses if text(address)})
    if not unique:
        return None

    def key(address: str) -> tuple[int, str]:
        parts = parse_house(address)
        return (parts.minimum if parts.minimum is not None else 10**9, address.casefold())

    return min(unique, key=key)


def levenshtein(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for index, left_char in enumerate(left, 1):
        current = [index]
        for right_index, right_char in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def round_coordinates(value: Any) -> Any:
    if isinstance(value, list):
        return [round_coordinates(item) for item in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


def assign_age_band(bands: list[dict[str, Any]], year: int | None) -> str:
    if year is None:
        return "unknown"
    for band in bands:
        minimum = band.get("minYear")
        maximum = band.get("maxYear")
        if (minimum is None or year >= minimum) and (maximum is None or year <= maximum):
            return text(band.get("id") or band.get("label")) or "unknown"
    return "unknown"


def point_record(feature: dict[str, Any], feature_index: int) -> dict[str, Any]:
    props = feature.get("properties") or {}
    street = normalize_street(props.get("StName"))
    house = normalize_house(props.get("StNm"))
    return {
        "feature_index": feature_index,
        "address_id": text(props.get("address_id")),
        "address": text(props.get("Full_Addr")),
        "street_name": text(props.get("StName")),
        "street": street,
        "house": house,
        "house_parts": parse_house(props.get("StNm")),
        "bldgid": normalize_id(props.get("BldgID")),
        "gisid": normalize_id(props.get("ml")),
        "entry": text(props.get("Entry")),
    }


def unique_candidates(points: Iterable[dict[str, Any]], valid_bldgids: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    point_list = list(points)
    bldgids = sorted({point["bldgid"] for point in point_list if point["bldgid"] in valid_bldgids})
    return point_list, bldgids


def historical_candidates(
    historic_address: str,
    points_by_street: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    normalized = " ".join(ascii_words(historic_address))
    if not normalized:
        return []
    candidates: list[dict[str, Any]] = []
    for street, points in points_by_street.items():
        street_words = street.split()
        if not street_words or not re.search(rf"\b{re.escape(' '.join(street_words))}\b", normalized):
            continue
        numbers = {int(value) for value in re.findall(r"\d+", normalized)}
        if not numbers:
            continue
        for point in points:
            parts = point["house_parts"]
            if parts.minimum in numbers or parts.maximum in numbers:
                candidates.append(point)
    return candidates


def build_match_result(
    hail: dict[str, str],
    stage: int,
    status: str,
    treatment: str,
    candidates: list[dict[str, Any]],
    bldgids: list[str],
    reason: str,
) -> dict[str, Any]:
    review_category = ""
    review_summary = ""
    if status == "review":
        if stage in {4, 6} and len(bldgids) > 1:
            review_category = "multiple_footprint_candidates"
            review_summary = (
                "The street and base number agree, but suffix, rear, or range differences "
                "leave more than one plausible footprint."
            )
        elif hail.get("classification") == "Building complex":
            review_category = "building_complex_geometry_uncertain"
            review_summary = (
                "The address resolves, but the Hail entry is a building complex and may "
                "represent more than one footprint."
            )
        elif stage == 5:
            review_category = "historical_address_or_alias"
            review_summary = (
                "A historical address or street alias produced candidates, but the alias "
                "has not yet been proven for automatic matching."
            )
        elif stage == 6:
            review_category = "street_spelling_difference"
            review_summary = (
                "The number is compatible and the street spelling is close, but fuzzy "
                "street-name matches require manual confirmation."
            )
        else:
            review_category = "other_manual_review"
            review_summary = "The deterministic evidence is insufficient for automatic acceptance."
    return {
        "building_id": hail["building_id"],
        "hail_address": f"{hail['address_raw']} {hail['street_name']}".strip(),
        "hail_street_name": hail["street_name"],
        "classification": hail.get("classification", ""),
        "construction_year": hail.get("construction_year", ""),
        "match_stage": str(stage),
        "match_status": status,
        "treatment": treatment,
        "candidate_address_point_count": len(candidates),
        "candidate_bldgid_count": len(bldgids),
        "candidate_bldgids": "|".join(bldgids),
        "candidate_addresses": "|".join(sorted({point["address"] for point in candidates if point["address"]})),
        "candidate_street_names": "|".join(
            sorted({point["street_name"] for point in candidates if point["street_name"]})
        ),
        "matched_bldgid": bldgids[0] if status == "accepted" and len(bldgids) == 1 else "",
        "match_reason": reason,
        "review_reason_category": review_category,
        "review_reason_summary": review_summary,
        "override_decision": "",
        "override_note": "",
        "override_reviewed_at": "",
        "pre_override_match_stage": "",
        "pre_override_match_status": "",
        "pre_override_matched_bldgid": "",
        "pre_override_candidate_bldgids": "",
    }


def match_hail_record(
    hail: dict[str, str],
    exact_index: dict[tuple[str, str], list[dict[str, Any]]],
    points_by_street: dict[str, list[dict[str, Any]]],
    points_by_number: dict[int, list[dict[str, Any]]],
    valid_bldgids: set[str],
    confirmed_street_aliases: set[tuple[str, str]],
    manual_street_aliases: set[tuple[str, str]],
) -> dict[str, Any]:
    classification = hail.get("classification", "")
    if hail.get("razed", "").strip().casefold() == "true" or classification == "Razed":
        return build_match_result(hail, 0, "excluded", "exclude", [], [], "Hail record is razed")
    if classification in {"Cross reference to another address", "Unclear"}:
        return build_match_result(
            hail, 7, "unmatched", "leave_unmatched", [], [], f"Classification is {classification}"
        )

    street = normalize_street(hail.get("street_name"))
    house = normalize_house(hail.get("address_raw"))
    hail_parts = parse_house(hail.get("address_raw"))

    exact_points, exact_bldgids = unique_candidates(exact_index.get((street, house), []), valid_bldgids)
    if len(exact_points) == 1 and len(exact_bldgids) == 1:
        treatment = "review" if classification == "Building complex" else "auto_accept"
        status = "review" if treatment == "review" else "accepted"
        return build_match_result(hail, 1, status, treatment, exact_points, exact_bldgids, "Exact standardized address")

    if hail_parts.is_range and hail_parts.minimum is not None and hail_parts.maximum is not None:
        range_points = [
            point
            for point in points_by_street.get(street, [])
            if house_numbers_overlap(hail_parts, point["house_parts"])
        ]
        range_points, range_bldgids = unique_candidates(range_points, valid_bldgids)
        if len(range_bldgids) == 1:
            treatment = "review" if classification == "Building complex" else "usually_auto_accept"
            status = "review" if treatment == "review" else "accepted"
            return build_match_result(
                hail, 2, status, treatment, range_points, range_bldgids, "Hail range contains Address Point number(s)"
            )

    if len(exact_points) > 1 and len(exact_bldgids) == 1:
        treatment = "review" if classification == "Building complex" else "auto_accept"
        status = "review" if treatment == "review" else "accepted"
        return build_match_result(
            hail, 3, status, treatment, exact_points, exact_bldgids, "Multiple Address Points share one BLDGID"
        )

    stage4_points: list[dict[str, Any]] = []
    if hail_parts.minimum is not None:
        for point in points_by_street.get(street, []):
            point_parts = point["house_parts"]
            if point_parts.minimum is None or point_parts.maximum is None or hail_parts.maximum is None:
                continue
            if house_numbers_overlap(hail_parts, point_parts):
                stage4_points.append(point)
    stage4_points, stage4_bldgids = unique_candidates(stage4_points, valid_bldgids)
    if stage4_bldgids:
        if len(stage4_bldgids) == 1 and classification != "Building complex":
            return build_match_result(
                hail, 4, "accepted", "auto_accept_unique", stage4_points, stage4_bldgids,
                "Street and number agree; suffix/rear/range differs but only one footprint is plausible",
            )
        return build_match_result(
            hail, 4, "review", "manual_review", stage4_points, stage4_bldgids,
            "Street and number agree but suffix/rear/range yields multiple or complex candidates",
        )

    alias_points = historical_candidates(hail.get("historic_address", ""), points_by_street)
    alias_points, alias_bldgids = unique_candidates(alias_points, valid_bldgids)
    if alias_bldgids:
        return build_match_result(
            hail, 5, "review", "manual_review", alias_points, alias_bldgids,
            "Historical address or street alias produces current-address candidate(s)",
        )

    spelling_points: list[dict[str, Any]] = []
    if hail_parts.minimum is not None:
        for point in points_by_number.get(hail_parts.minimum, []):
            candidate_street = point["street"]
            distance = levenshtein(street, candidate_street)
            threshold = min(3, max(1, round(max(len(street), len(candidate_street)) * 0.15)))
            if 0 < distance <= threshold:
                spelling_points.append(point)
    spelling_points, spelling_bldgids = unique_candidates(spelling_points, valid_bldgids)
    if spelling_bldgids:
        street_pairs = {
            (street, point["street"])
            for point in spelling_points
            if point["street"]
        }
        aliases_confirmed = bool(street_pairs) and street_pairs <= confirmed_street_aliases
        aliases_manual = bool(street_pairs & manual_street_aliases)
        if aliases_confirmed and len(spelling_bldgids) == 1 and classification != "Building complex":
            return build_match_result(
                hail, 6, "accepted", "confirmed_alias", spelling_points, spelling_bldgids,
                "Confirmed street-name alias with compatible number and one footprint",
            )
        if aliases_manual:
            reason = "Street-name pair is explicitly reserved for manual review"
        elif aliases_confirmed and len(spelling_bldgids) > 1:
            reason = "Confirmed street-name alias, but the address has multiple plausible footprints"
        elif classification == "Building complex":
            reason = "Street-name candidate is a building complex that may span footprints"
        else:
            reason = "Unconfirmed small street-name spelling difference with compatible number"
        return build_match_result(
            hail, 6, "review", "manual_review", spelling_points, spelling_bldgids,
            reason,
        )

    return build_match_result(hail, 7, "unmatched", "leave_unmatched", [], [], "No credible address candidate")


def select_assessor(records: list[dict[str, Any]], primary_address: str | None) -> dict[str, Any] | None:
    if not records:
        return None
    normalized_primary = normalize_street(primary_address)

    def key(record: dict[str, Any]) -> tuple[int, int, str]:
        address_match = int(normalize_street(record.get("address")) != normalized_primary)
        year = complete_year(record.get("yearofassessment")) or 0
        return (address_match, -year, text(record.get("pid")))

    return min(records, key=key)


def choose_hail_record(records: list[tuple[dict[str, str], dict[str, Any]]]) -> tuple[dict[str, str], dict[str, Any]] | None:
    if not records:
        return None

    def key(item: tuple[dict[str, str], dict[str, Any]]) -> tuple[int, int, int, str]:
        hail, match = item
        return (
            CLASS_PRIORITY.get(hail.get("classification", ""), 9),
            int(match["match_stage"]),
            int(complete_year(hail.get("construction_year")) is None),
            hail["building_id"],
        )

    return min(records, key=key)


def apply_manual_overrides(
    match_rows: list[dict[str, Any]],
    override_records: list[dict[str, Any]],
    points_by_bldgid: dict[str, list[dict[str, Any]]],
    valid_bldgids: set[str],
) -> None:
    """Layer reviewer decisions over generated matches without changing sources."""
    matches_by_hail_id = {row["building_id"]: row for row in match_rows}
    for override in override_records:
        building_id = text(override.get("building_id"))
        decision = text(override.get("decision"))
        match = matches_by_hail_id.get(building_id)
        if match is None:
            continue
        match["pre_override_match_stage"] = match["match_stage"]
        match["pre_override_match_status"] = match["match_status"]
        match["pre_override_matched_bldgid"] = match["matched_bldgid"]
        match["pre_override_candidate_bldgids"] = match["candidate_bldgids"]
        match["match_stage"] = "8"
        match["treatment"] = "manual_override"
        match["override_decision"] = decision
        match["override_note"] = text(override.get("note"))
        match["override_reviewed_at"] = text(override.get("reviewed_at"))
        match["review_reason_category"] = ""
        match["review_reason_summary"] = ""
        if decision == "matched":
            bldgid = normalize_id(override.get("bldgid"))
            if bldgid not in valid_bldgids:
                raise ValueError(f"Manual override for {building_id} has invalid BldgID {bldgid!r}")
            candidate_points = points_by_bldgid.get(bldgid, [])
            match.update(
                {
                    "match_status": "accepted",
                    "candidate_address_point_count": len(candidate_points),
                    "candidate_bldgid_count": 1,
                    "candidate_bldgids": bldgid,
                    "candidate_addresses": "|".join(
                        sorted({point["address"] for point in candidate_points if point["address"]})
                    ),
                    "candidate_street_names": "|".join(
                        sorted({point["street_name"] for point in candidate_points if point["street_name"]})
                    ),
                    "matched_bldgid": bldgid,
                    "match_reason": "Reviewer selected this footprint",
                }
            )
        elif decision == "no_map_match":
            match.update(
                {
                    "match_status": "unmatched",
                    "candidate_bldgid_count": 0,
                    "candidate_bldgids": "",
                    "matched_bldgid": "",
                    "match_reason": "Reviewer determined there is no map match",
                }
            )
        else:
            raise ValueError(f"Manual override for {building_id} has unknown decision {decision!r}")


def main() -> None:
    for source in (
        HAIL_PATH,
        ASSESSOR_PATH,
        ADDRESS_POINTS_PATH,
        FOOTPRINTS_PATH,
        AGE_BANDS_PATH,
        STREET_ALIASES_PATH,
        MANUAL_OVERRIDES_PATH,
    ):
        if not source.exists():
            raise FileNotFoundError(source)

    footprints = load_geojson(FOOTPRINTS_PATH)
    address_points = load_geojson(ADDRESS_POINTS_PATH)
    assessor = load_geojson(ASSESSOR_PATH)
    with HAIL_PATH.open(newline="", encoding="utf-8-sig") as handle:
        hail_rows = list(csv.DictReader(handle))
    with AGE_BANDS_PATH.open(encoding="utf-8-sig") as handle:
        age_bands = json.load(handle)
    with STREET_ALIASES_PATH.open(encoding="utf-8-sig") as handle:
        street_alias_config = json.load(handle)
    with MANUAL_OVERRIDES_PATH.open(encoding="utf-8-sig") as handle:
        override_data = json.load(handle)
    confirmed_street_aliases = {
        (normalize_street(pair[0]), normalize_street(pair[1]))
        for pair in street_alias_config.get("confirmed", [])
    }
    manual_street_aliases = {
        (normalize_street(pair[0]), normalize_street(pair[1]))
        for pair in street_alias_config.get("manual_review", [])
    }

    valid_bldgids = {
        normalize_id(feature.get("properties", {}).get("BldgID"))
        for feature in footprints["features"]
        if normalize_id(feature.get("properties", {}).get("BldgID"))
    }

    points = [point_record(feature, index) for index, feature in enumerate(address_points["features"])]
    exact_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    points_by_street: dict[str, list[dict[str, Any]]] = defaultdict(list)
    points_by_number: dict[int, list[dict[str, Any]]] = defaultdict(list)
    points_by_bldgid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        exact_index[(point["street"], point["house"])].append(point)
        points_by_street[point["street"]].append(point)
        if point["house_parts"].minimum is not None:
            points_by_number[point["house_parts"].minimum].append(point)
        if point["bldgid"]:
            points_by_bldgid[point["bldgid"]].append(point)

    match_rows = [
        match_hail_record(
            row,
            exact_index,
            points_by_street,
            points_by_number,
            valid_bldgids,
            confirmed_street_aliases,
            manual_street_aliases,
        )
        for row in hail_rows
    ]
    apply_manual_overrides(
        match_rows,
        override_data.get("overrides", []),
        points_by_bldgid,
        valid_bldgids,
    )
    hail_by_id = {row["building_id"]: row for row in hail_rows}
    accepted_hail_by_bldgid: dict[str, list[tuple[dict[str, str], dict[str, Any]]]] = defaultdict(list)
    for match in match_rows:
        if match["match_status"] == "accepted" and match["matched_bldgid"]:
            accepted_hail_by_bldgid[match["matched_bldgid"]].append((hail_by_id[match["building_id"]], match))

    assessor_by_gisid = {
        normalize_id(feature.get("properties", {}).get("gisid")): feature.get("properties") or {}
        for feature in assessor["features"]
        if normalize_id(feature.get("properties", {}).get("gisid"))
    }

    output_features: list[dict[str, Any]] = []
    year_source_counts: Counter[str] = Counter()
    year_review_count = 0
    current_year = date.today().year

    for footprint_index, footprint in enumerate(footprints["features"]):
        footprint_props = footprint.get("properties") or {}
        bldgid = normalize_id(footprint_props.get("BldgID"))
        building_points = points_by_bldgid.get(bldgid, [])
        addresses = sorted({point["address"] for point in building_points if point["address"]})
        primary_address = choose_lowest_address(addresses)
        gisids = sorted({point["gisid"] for point in building_points if point["gisid"]})
        assessor_records = [assessor_by_gisid[gisid] for gisid in gisids if gisid in assessor_by_gisid]
        selected_assessor = select_assessor(assessor_records, primary_address)
        assessor_year = complete_year(selected_assessor.get("condition_yearbuilt")) if selected_assessor else None

        accepted_hail = accepted_hail_by_bldgid.get(bldgid, [])
        primary_hail_pair = choose_hail_record(accepted_hail)
        primary_hail = primary_hail_pair[0] if primary_hail_pair else None
        primary_hail_match = primary_hail_pair[1] if primary_hail_pair else None
        hail_years = sorted(
            {
                year
                for hail, _match in accepted_hail
                if (year := complete_year(hail.get("construction_year"))) is not None
            }
        )
        unambiguous_hail_year = hail_years[0] if len(hail_years) == 1 else None
        year_difference = (
            abs(unambiguous_hail_year - assessor_year)
            if unambiguous_hail_year is not None and assessor_year is not None
            else None
        )
        year_needs_review = len(hail_years) > 1 or (year_difference is not None and year_difference > 50)
        if unambiguous_hail_year is not None and (assessor_year is None or (year_difference is not None and year_difference <= 50)):
            year_built = unambiguous_hail_year
            year_source = "Hail"
        elif assessor_year is not None:
            year_built = assessor_year
            year_source = "Assessor"
        else:
            year_built = None
            year_source = "Unknown"
        year_source_counts[year_source] += 1
        year_review_count += int(year_needs_review)

        out_props = {
            "BldgID": bldgid or None,
            "footprint_feature_index": footprint_index,
            "Address": primary_address,
            "address": primary_address,
            "addresses": " | ".join(addresses) or None,
            "address_count": len(addresses),
            "address_point_count": len(building_points),
            "assessor_record_count": len(assessor_records),
            "assessor_gisids": "|".join(gisids) or None,
            "assessor_gisid": normalize_id(selected_assessor.get("gisid")) if selected_assessor else None,
            "assessor_pid": text(selected_assessor.get("pid")) if selected_assessor else None,
            "assessor_address": text(selected_assessor.get("address")) if selected_assessor else None,
            "assessor_year_built": assessor_year,
            "Condition_YearBuilt": assessor_year,
            "PropertyClass": text(selected_assessor.get("propertyclass")) if selected_assessor else None,
            "Zoning": text(selected_assessor.get("zoning")) if selected_assessor else None,
            "hail_match_count": len(accepted_hail),
            "hail_building_ids": "|".join(hail["building_id"] for hail, _match in accepted_hail) or None,
            "hail_years": "|".join(str(year) for year in hail_years) or None,
            "hail_year_built": unambiguous_hail_year,
            "hail_year_conflict": len(hail_years) > 1,
            "hail_primary_building_id": primary_hail.get("building_id") if primary_hail else None,
            "hail_match_stage": int(primary_hail_match["match_stage"]) if primary_hail_match else None,
            "hail_classification": primary_hail.get("classification") if primary_hail else None,
            "hail_building_name": primary_hail.get("building_type") if primary_hail else None,
            "hail_building_type": primary_hail.get("building_type") if primary_hail else None,
            "hail_architect": primary_hail.get("architect") if primary_hail else None,
            "hail_builder": primary_hail.get("builder") if primary_hail else None,
            "hail_owner_at_construction": primary_hail.get("owner_at_construction") if primary_hail else None,
            "hail_summary": primary_hail.get("summary_raw") if primary_hail else None,
            "year_built": year_built,
            "year_built_source": year_source,
            "year_difference_hail_assessor": year_difference,
            "year_needs_review": year_needs_review,
            "age": current_year - year_built if year_built is not None else None,
            "age_band": assign_age_band(age_bands, year_built),
            "join_status": "matched" if selected_assessor else "unmatched",
            "join_ambiguous": len(gisids) > 1,
        }
        output_features.append(
            {
                "type": "Feature",
                "geometry": round_coordinates(footprint.get("geometry")),
                "properties": out_props,
            }
        )

    output = {"type": "FeatureCollection", "features": output_features}
    for destination in (PROCESSED_OUT, PUBLIC_OUT):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    MATCH_AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with MATCH_AUDIT_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATCH_COLUMNS)
        writer.writeheader()
        writer.writerows(match_rows)
    with REVIEW_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATCH_COLUMNS)
        writer.writeheader()
        writer.writerows(row for row in match_rows if row["match_status"] == "review")

    review_rows = [row for row in match_rows if row["match_status"] == "review"]
    review_hail_fields = [
        "building_id",
        "street_name",
        "address_raw",
        "normalized_address",
        "historic_address",
        "building_type",
        "stories",
        "construction_year",
        "architect",
        "builder",
        "owner_at_construction",
        "classification",
        "summary_raw",
        "source_page",
    ]
    review_bundle_records = []
    for match in review_rows:
        hail = hail_by_id[match["building_id"]]
        review_bundle_records.append(
            {
                **match,
                "hail": {field: hail.get(field, "") for field in review_hail_fields},
            }
        )
    review_bundle = {
        "generated_at": date.today().isoformat(),
        "record_count": len(review_bundle_records),
        "records": review_bundle_records,
    }
    REVIEW_BUNDLE_OUT.write_text(
        json.dumps(review_bundle, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    review_categories = Counter(row["review_reason_category"] for row in review_rows)
    review_descriptions = {
        row["review_reason_category"]: row["review_reason_summary"]
        for row in review_rows
        if row["review_reason_category"]
    }
    category_labels = {
        "multiple_footprint_candidates": "Multiple plausible footprints",
        "building_complex_geometry_uncertain": "Building complex may span footprints",
        "historical_address_or_alias": "Unproven historical address or alias",
        "street_spelling_difference": "Small street-name spelling difference",
        "other_manual_review": "Other manual review",
    }
    summary_lines = [
        "# Hail address manual-review summary",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        f"The review queue contains **{len(review_rows):,}** Hail records that were not confidently auto-matched.",
        "",
        "| Reason | Records | Share | Explanation |",
        "|---|---:|---:|---|",
    ]
    for category, count in review_categories.most_common():
        share = count / len(review_rows) * 100 if review_rows else 0
        summary_lines.append(
            f"| {category_labels.get(category, category)} | {count:,} | {share:.1f}% | "
            f"{review_descriptions.get(category, '')} |"
        )
    summary_lines.extend(
        [
            "",
            "## Street-name spelling differences",
            "",
            "These Stage 6 review rows share a compatible house number but use a different street spelling. "
            "A confirmed alias can still appear here when a separate footprint or building-complex ambiguity remains.",
            "",
            "| Hail street name | Address Point street name | Review records | Review basis |",
            "|---|---|---:|---|",
        ]
    )
    spelling_pairs: Counter[tuple[str, str]] = Counter()
    spelling_pair_reasons: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in review_rows:
        if row["match_stage"] != "6":
            continue
        alternatives = [value for value in row["candidate_street_names"].split("|") if value]
        for alternative in alternatives:
            pair = (row["hail_street_name"], alternative)
            spelling_pairs[pair] += 1
            spelling_pair_reasons[pair].add(row["review_reason_category"])
    for (hail_street, candidate_street), count in sorted(
        spelling_pairs.items(), key=lambda item: (-item[1], item[0][0].casefold(), item[0][1].casefold())
    ):
        pair = (hail_street, candidate_street)
        basis = "; ".join(
            category_labels.get(category, category)
            for category in sorted(spelling_pair_reasons[pair])
        )
        summary_lines.append(f"| {hail_street} | {candidate_street} | {count:,} | {basis} |")
    summary_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A review row is a candidate set, not a rejected match. `candidate_bldgids` and "
            "`candidate_addresses` contain the evidence to inspect.",
            "- Multiple-footprint cases should be resolved using rear/suffix/range context and spatial evidence.",
            "- Building-complex cases need a decision about whether one Hail entry applies to one footprint or several.",
            "- Historical aliases should become automatic only after an explicit alias is validated and documented.",
            "- Spelling-difference candidates must remain manual until the spelling correspondence is proven.",
            "",
        ]
    )
    REVIEW_SUMMARY_OUT.write_text("\n".join(summary_lines), encoding="utf-8")

    match_counts = Counter((row["match_stage"], row["match_status"]) for row in match_rows)
    print(f"Footprint master records: {len(output_features):,}")
    print(f"Address Points: {len(points):,}")
    print(f"Assessor records: {len(assessor['features']):,}")
    print(f"Hail records audited: {len(match_rows):,}")
    for (stage, status), count in sorted(match_counts.items(), key=lambda item: (int(item[0][0]), item[0][1])):
        print(f"  Stage {stage} {status}: {count:,}")
    print("Displayed year sources:")
    for source, count in year_source_counts.items():
        print(f"  {source}: {count:,}")
    print(f"Year-review flags: {year_review_count:,}")
    print(f"Wrote {PROCESSED_OUT}")
    print(f"Wrote {PUBLIC_OUT}")
    print(f"Wrote {MATCH_AUDIT_OUT}")
    print(f"Wrote {REVIEW_OUT}")
    print(f"Wrote {REVIEW_SUMMARY_OUT}")
    print(f"Wrote {REVIEW_BUNDLE_OUT}")


if __name__ == "__main__":
    main()
