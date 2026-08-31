#!/usr/bin/env python3
"""Download the latest quarterly Cambridge Development Log snapshots."""

from __future__ import annotations

import argparse
import os
import tempfile
import urllib.request
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/raw/development-logs"
DATASETS = {
    "Development_Log_Current_Edition": "wjwg-93qh",
    "Development_Log_Historical_Projects": "a5ud-8kjv",
}


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "cambridge-building-age-map/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if not payload.startswith((b'"', b"Project")) or b"Year Complete" not in payload[:2000]:
        raise ValueError(f"Unexpected CSV response from {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=destination.parent, suffix=".csv")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary_name, destination)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-date", default=date.today().strftime("%Y%m%d"))
    args = parser.parse_args()
    for label, dataset_id in DATASETS.items():
        destination = OUT_DIR / f"{label}_{args.snapshot_date}.csv"
        url = f"https://data.cambridgema.gov/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"
        download(url, destination)
        print(f"Updated {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
