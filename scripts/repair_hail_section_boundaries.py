#!/usr/bin/env python3
"""Repair Hail rows assigned past missed C, E, and M street headings."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scrape_cambridge_buildings import BUILDING_FIELDS, parse_page


ROOT = Path(__file__).resolve().parents[1]
HAIL_PATH = ROOT / "data/raw/Hail_buildings_dataset.csv"
OVERRIDES_PATH = ROOT / "data/manual/hail-building-overrides.json"
AFFECTED_LETTERS = ("c", "e", "m")
EXPECTED_REASSIGNMENTS = 227


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-dir", type=Path, required=True)
    args = parser.parse_args()

    with HAIL_PATH.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    mapping: dict[str, dict[str, str]] = {}
    for letter in AFFECTED_LETTERS:
        html_path = args.html_dir / f"{letter}.html"
        page_rows = [
            row for row in rows if row.get("source_page", "").endswith(f"/{letter}.html")
        ]
        if not page_rows:
            raise ValueError(f"Canonical Hail data has no rows for {letter}.html")
        parsed_rows, _events = parse_page(
            html_path.read_bytes().decode("windows-1252", errors="replace"),
            page_rows[0]["source_page"],
        )
        if len(page_rows) != len(parsed_rows):
            raise ValueError(
                f"{letter}.html row count changed: {len(page_rows)} canonical vs "
                f"{len(parsed_rows)} parsed"
            )
        for canonical, reparsed in zip(page_rows, parsed_rows):
            if canonical["summary_raw"] != reparsed["summary_raw"]:
                raise ValueError(
                    f"{letter}.html row order diverged at {canonical['building_id']}"
                )
            if canonical["street_name"] == reparsed["street_name"]:
                continue
            old_id = canonical["building_id"]
            mapping[old_id] = {
                "building_id": reparsed["building_id"],
                "street_name": reparsed["street_name"],
                "address_raw": reparsed["address_raw"],
            }
            for field in BUILDING_FIELDS:
                canonical[field] = reparsed[field]
            canonical["normalized_address"] = (
                f"{canonical['address_min']} {canonical['street_name']}".strip()
            )

    if not mapping:
        print("Hail section-boundary repair is already applied")
        return
    if len(mapping) != EXPECTED_REASSIGNMENTS:
        raise ValueError(
            f"Expected {EXPECTED_REASSIGNMENTS} street reassignments, found {len(mapping)}"
        )
    ids = [row["building_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Reparsed Hail building IDs are not unique")

    with HAIL_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    override_data = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    migrated_overrides = 0
    for override in override_data.get("overrides", []):
        replacement = mapping.get(str(override.get("building_id", "")))
        if not replacement:
            continue
        override["building_id"] = replacement["building_id"]
        override["street_name"] = replacement["street_name"]
        override["hail_address"] = (
            f"{replacement['address_raw']} {replacement['street_name']}".strip()
        )
        migrated_overrides += 1
    override_data["overrides"].sort(
        key=lambda item: (
            str(item.get("street_name", "")).casefold(),
            str(item.get("hail_address", "")).casefold(),
            str(item.get("building_id", "")),
        )
    )
    OVERRIDES_PATH.write_text(
        f"{json.dumps(override_data, indent=2)}\n",
        encoding="utf-8",
    )
    print(
        f"Reassigned {len(mapping)} Hail records and migrated "
        f"{migrated_overrides} manual overrides"
    )


if __name__ == "__main__":
    main()
