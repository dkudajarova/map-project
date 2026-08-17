#!/usr/bin/env python3
"""Scrape Harvard's archived Cambridge Buildings reference shelf.

The archive is split over a.html through z.html.  Each street section contains
building summary lines followed by indented historical records.  This script
writes one row per building and one row per historical record attached to it.

Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ARCHIVE_URL = (
    "https://wayback.archive-it.org/5488/20170330145535/"
    "http://hul.harvard.edu/lib/archives/refshelf/cba/{letter}.html"
)
BUILDING_FIELDS = [
    "building_id", "street_name", "address_raw", "address_min", "address_max",
    "historic_address", "building_type", "stories", "construction_year",
    "architect", "builder", "owner_at_construction", "razed", "source_page",
    "source_anchor", "summary_raw",
]
EVENT_FIELDS = [
    "building_id", "event_index", "event_year", "event_raw", "source_type",
    "source_reference", "architect", "builder", "owner", "source_page",
    "source_anchor",
]


@dataclass
class DD:
    text: str
    anchor: str | None = None
    links: list[tuple[str, str]] = field(default_factory=list)


class DDParser(HTMLParser):
    """Extract malformed-but-regular DD records without external packages."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[DD] = []
        self.current: DD | None = None
        self.in_link = False
        self.link_href = ""
        self.link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "dd":
            self._finish()
            self.current = DD("")
        elif tag == "a":
            if self.current is None:
                return
            if values.get("name"):
                self.current.anchor = values["name"]
            if values.get("href"):
                self.in_link = True
                self.link_href = values["href"] or ""
                self.link_text = []
        elif tag == "br" and self.current is not None:
            self.current.text += " "

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_link and self.current is not None:
            self.current.links.append((self.link_href, "".join(self.link_text).strip()))
            self.in_link = False
        elif tag == "dl":
            self._finish()

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current.text += data
            if self.in_link:
                self.link_text.append(data)

    def close(self) -> None:
        super().close()
        self._finish()

    def _finish(self) -> None:
        if self.current is not None:
            self.current.text = normalize(self.current.text)
            if self.current.text or self.current.anchor or self.current.links:
                self.records.append(self.current)
        self.current = None


def normalize(value: str) -> str:
    value = html.unescape(value).replace("\ufffd", "½").replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def slug(value: str) -> str:
    value = value.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def street_slug(value: str) -> str:
    """Create stable IDs using the archive's familiar street abbreviations."""
    words = value.lower().split()
    suffixes = {
        "avenue": "ave", "boulevard": "blvd", "circle": "cir", "court": "ct",
        "drive": "dr", "highway": "hwy", "lane": "ln", "park": "pk",
        "parkway": "pkwy", "place": "pl", "road": "rd", "square": "sq",
        "street": "st", "terrace": "terr", "turnpike": "tpk", "way": "way",
    }
    if words and words[-1] in suffixes:
        words[-1] = suffixes[words[-1]]
    return slug(" ".join(words))


def fetch(url: str, retries: int = 6) -> str:
    request = Request(url, headers={"User-Agent": "cambridge-buildings-research/1.0"})
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=60) as response:
                return response.read().decode("windows-1252", errors="replace")
        except HTTPError as exc:
            if exc.code == 404:
                raise
            error: Exception = exc
        except URLError as exc:
            error = exc
        if attempt + 1 < retries:
            # Archive-It commonly answers bursts with 429; honor Retry-After and
            # otherwise use a longer backoff than for transient network errors.
            retry_after = error.headers.get("Retry-After") if isinstance(error, HTTPError) else None
            wait = float(retry_after) if retry_after and retry_after.isdigit() else (10 * (attempt + 1) if isinstance(error, HTTPError) and error.code == 429 else 2 ** attempt)
            time.sleep(wait)
    raise error


def street_names(records: Iterable[DD]) -> dict[str, str]:
    """Return section-anchor street names from both navigation and headings.

    The archive is inconsistent: some navigation labels contain mixed-case
    qualifiers (for example, ``ELM STREET (Cambridgeport)``), and a few valid
    street anchors are omitted from the navigation entirely. Section headings
    are therefore the authoritative fallback; uppercase navigation is not a
    requirement.
    """
    names: dict[str, str] = {}
    for record in records:
        for href, label in record.links:
            if href.startswith("#") and label and re.search(
                r"\b(?:avenue|court|drive|lane|park|parkway|place|plaza|road|square|street|terrace|turnpike|way)\b",
                label,
                re.I,
            ):
                names[href[1:]] = format_street_name(label)
    heading_pattern = re.compile(
        r"^(?P<name>.*?\b(?:AVENUE|COURT|DRIVE|LANE|PARK|PARKWAY|PLACE|PLAZA|ROAD|SQUARE|STREET|TERRACE|TURNPIKE|WAY)"
        r"(?:\s*\([^)]*\))?)\s+(?:dead-end|through|private|former|street|laid\s+out|opened)\b",
        re.I,
    )
    for record in records:
        if not record.anchor or record.anchor in names:
            continue
        match = heading_pattern.match(record.text)
        if match:
            names[record.anchor] = format_street_name(match.group("name"))
    return names


def format_street_name(value: str) -> str:
    formatted = re.sub(
        r"\s*\((?:Cambridgeport|North Cambridge)\)\s*$",
        "",
        normalize(value),
        flags=re.I,
    ).title()
    return re.sub(r"\bMc([a-z])", lambda match: f"Mc{match.group(1).upper()}", formatted)


def is_building_summary(text: str) -> bool:
    text = text.lstrip("• ")
    return bool(re.match(r"\d", text)) and not text.startswith(".....")


def split_summary(text: str) -> tuple[str, str | None, str]:
    clean = text.lstrip("• ")
    # Address can contain ranges, comma-separated numbers, rear markers and '+'.
    match = re.match(
        r"(?P<address>\d+[A-Za-z]?(?:\s*[-–]\s*\d+[A-Za-z]?)?(?:\+)?)"
        r"(?:\s*(?P<historic>\([^)]*\)))?\s*(?P<body>.*)",
        clean,
    )
    if not match:
        return clean.split(maxsplit=1)[0], None, clean
    historic = match.group("historic")
    return match.group("address"), historic[1:-1].strip() if historic else None, match.group("body")


def summary_fields(body: str) -> tuple[str | None, str | None, str | None]:
    stories_match = re.search(r"(?<!\w)(\d+(?:[½¼¾]|[.]5)?)-st\b", body, re.I)
    year_match = re.search(r"(?<!\d)((?:17|18|19|20)\d{2})(?!\d)", body)
    cut = min(
        [m.start() for m in (stories_match, year_match) if m is not None],
        default=len(body),
    )
    building_type = body[:cut].strip(" ;:") or None
    stories = stories_match.group(1) if stories_match else None
    if stories:
        stories = stories.translate(str.maketrans({"½": ".5", "¼": ".25", "¾": ".75"}))
    year = year_match.group(1) if year_match else None
    return building_type, stories, year


def people(text: str) -> dict[str, str | None]:
    result: dict[str, str | None] = {"architect": None, "builder": None, "owner": None}
    markers = list(re.finditer(r"\((a|b|o)(?:\s*&\s*(a|b|o))?\)\s*", text, re.I))
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        value = text[marker.end():end].strip(" ;,.") or None
        for code in marker.groups():
            if code and value:
                result[{"a": "architect", "b": "builder", "o": "owner"}[code.lower()]] = value
    return result


def event_fields(text: str) -> tuple[str | None, str | None, str | None]:
    clean = text.lstrip(".")
    year = (re.match(r"((?:17|18|19|20)\d{2})\b", clean) or [None, None])[1]
    source_match = re.search(r"\b(permit|tax|deed|atlas|directory|bird's-eye view|permit card file)\b(?:\s+([^()]+?))?(?=\s*\(|$)", clean, re.I)
    if not source_match:
        return year, None, None
    return year, source_match.group(1), normalize(source_match.group(2) or "") or None


def parse_page(page_html: str, source_page: str) -> tuple[list[dict], list[dict]]:
    parser = DDParser()
    parser.feed(page_html)
    parser.close()
    names = street_names(parser.records)
    buildings: list[dict] = []
    events: list[dict] = []
    anchor: str | None = None
    current: dict | None = None
    event_index = 0
    used_ids: dict[str, int] = {}

    for record in parser.records:
        if record.anchor in names:
            anchor = record.anchor
            current = None
        if not anchor or not record.text:
            continue
        if is_building_summary(record.text):
            address, historic_address, body = split_summary(record.text)
            street = names[anchor]
            base_id = f"{street_slug(street)}_{slug(address)}"
            used_ids[base_id] = used_ids.get(base_id, 0) + 1
            building_id = base_id if used_ids[base_id] == 1 else f"{base_id}_{used_ids[base_id]}"
            numbers = [int(n) for n in re.findall(r"\d+", address)]
            building_type, stories, year = summary_fields(body)
            current = {
                "building_id": building_id,
                "street_name": street,
                "address_raw": address,
                "address_min": min(numbers) if numbers else None,
                "address_max": max(numbers) if numbers else None,
                "historic_address": historic_address,
                "building_type": building_type,
                "stories": stories,
                "construction_year": year,
                "architect": None,
                "builder": None,
                "owner_at_construction": None,
                "razed": "true" if "razed" in record.text.lower() else "false",
                "source_page": source_page,
                "source_anchor": anchor,
                "summary_raw": record.text,
            }
            buildings.append(current)
            event_index = 0
        elif current is not None and record.text.startswith("."):
            event_index += 1
            event_year, source_type, source_reference = event_fields(record.text)
            persons = people(record.text)
            events.append({
                "building_id": current["building_id"],
                "event_index": event_index,
                "event_year": event_year,
                "event_raw": record.text,
                "source_type": source_type,
                "source_reference": source_reference,
                **persons,
                "source_page": source_page,
                "source_anchor": anchor,
            })
            if event_year == current["construction_year"]:
                current["architect"] = current["architect"] or persons["architect"]
                current["builder"] = current["builder"] or persons["builder"]
                current["owner_at_construction"] = current["owner_at_construction"] or persons["owner"]
        elif not record.text.startswith("."):
            current = None
    return buildings, events


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument("--letters", default="abcdefghijklmnopqrstuvwxyz", help="Page letters to scrape")
    arg_parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    arg_parser.add_argument("--delay", type=float, default=0.2, help="Delay between archive requests")
    args = arg_parser.parse_args()

    buildings: list[dict] = []
    events: list[dict] = []
    for letter in dict.fromkeys(args.letters.lower()):
        if not letter.isalpha() or len(letter) != 1:
            arg_parser.error("--letters must contain only individual letters")
        url = ARCHIVE_URL.format(letter=letter)
        try:
            page_buildings, page_events = parse_page(fetch(url), url)
        except HTTPError as exc:
            if exc.code == 404:
                print(f"Skipping missing page: {url}", file=sys.stderr)
                continue
            raise
        buildings.extend(page_buildings)
        events.extend(page_events)
        print(f"{letter}: {len(page_buildings)} buildings, {len(page_events)} events", file=sys.stderr)
        time.sleep(args.delay)

    write_csv(args.output_dir / "buildings.csv", BUILDING_FIELDS, buildings)
    write_csv(args.output_dir / "building-events.csv", EVENT_FIELDS, events)
    print(f"Wrote {len(buildings)} buildings and {len(events)} events to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
