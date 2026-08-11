#!/usr/bin/env python3
"""Summarize manual Hail-to-footprint overrides and suggest evidence-based rules."""

from __future__ import annotations

import json
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERRIDES_PATH = ROOT / "data/manual/hail-building-overrides.json"
REVIEW_BUNDLE_PATH = ROOT / "data/processed/hail-manual-review.json"
MATCH_AUDIT_PATH = ROOT / "data/processed/hail-address-matches.csv"
REPORT_PATH = ROOT / "reports/manual-override-analysis.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(count: int, total: int) -> str:
    return f"{100 * count / total:.1f}%" if total else "—"


def table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |"
        for row in rows
    )
    return lines


def main() -> None:
    override_file = load_json(OVERRIDES_PATH)
    overrides = override_file.get("overrides", [])
    bundle = load_json(REVIEW_BUNDLE_PATH) if REVIEW_BUNDLE_PATH.exists() else {"records": []}
    review_by_id = {row["building_id"]: row for row in bundle.get("records", [])}
    if MATCH_AUDIT_PATH.exists():
        with MATCH_AUDIT_PATH.open(newline="", encoding="utf-8") as handle:
            audit_by_id = {row["building_id"]: row for row in csv.DictReader(handle)}
    else:
        audit_by_id = {}

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Manual override analysis",
        "",
        f"Generated: {generated}",
        "",
        "This report analyzes the separate manual-override layer. It does not modify Hail, Address Points, assessor, or footprint source files.",
        "",
    ]

    if not overrides:
        lines.extend(
            [
                "## Status",
                "",
                "No manual decisions have been saved yet. Complete one street in `/review`, then run `npm run overrides:analyze` again.",
                "",
                "The next report will measure proposed-candidate acceptance, neighboring-building selections, no-match decisions, and consistency by original match stage and review reason.",
                "",
            ]
        )
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {REPORT_PATH} (0 overrides)")
        return

    decisions = Counter(row.get("decision", "") for row in overrides)
    proposed = sum(row.get("selected_was_proposed") is True for row in overrides)
    neighbor = sum(row.get("selected_was_proposed") is False for row in overrides)
    matched = decisions["matched"]
    no_match = decisions["no_map_match"]

    lines.extend(
        [
            "## Overall decisions",
            "",
            *table(
                ["Measure", "Records", "Rate"],
                [
                    ["Reviewed", len(overrides), "100.0%"],
                    ["Matched to a proposed candidate", proposed, pct(proposed, len(overrides))],
                    ["Matched to a neighboring/non-proposed building", neighbor, pct(neighbor, len(overrides))],
                    ["All matched decisions", matched, pct(matched, len(overrides))],
                    ["No map match", no_match, pct(no_match, len(overrides))],
                ],
            ),
            "",
        ]
    )

    by_street: dict[str, list[dict]] = defaultdict(list)
    for override in overrides:
        by_street[str(override.get("street_name", "") or "(blank)")].append(override)
    street_rows = []
    for street, rows in sorted(by_street.items()):
        street_proposed = sum(row.get("selected_was_proposed") is True for row in rows)
        street_neighbor = sum(row.get("selected_was_proposed") is False for row in rows)
        street_none = sum(row.get("decision") == "no_map_match" for row in rows)
        street_rows.append([street, len(rows), street_proposed, street_neighbor, street_none])
    lines.extend(
        [
            "## Results by street",
            "",
            *table(
                ["Street", "Reviewed", "Proposed", "Neighbor", "No match"],
                street_rows,
            ),
            "",
        ]
    )

    replay_rows = []
    replay_counts = Counter()
    for override in overrides:
        audit = audit_by_id.get(str(override.get("building_id", "")), {})
        generated_status = audit.get("pre_override_match_status", "")
        generated_bldgid = audit.get("pre_override_matched_bldgid", "")
        selected_bldgid = str(override.get("bldgid") or "")
        if not generated_status:
            outcome = "not recorded"
        elif generated_status == "accepted" and generated_bldgid == selected_bldgid:
            outcome = "reproduced automatically"
        elif generated_status == "accepted":
            outcome = "automatic result conflicts"
        elif generated_status == "review":
            outcome = "still requires review"
        else:
            outcome = f"still {generated_status}"
        replay_counts[outcome] += 1
        replay_rows.append(
            [
                override.get("hail_address", ""),
                selected_bldgid or "—",
                audit.get("pre_override_match_stage", "—") or "—",
                generated_status or "—",
                generated_bldgid or "—",
                outcome,
            ]
        )
    if any(outcome != "not recorded" for outcome in replay_counts):
        lines.extend(
            [
                "## Replay against current deterministic rules",
                "",
                "Saved decisions remain authoritative, but the pipeline also records what the current rules would have done before applying each override.",
                "",
                *table(
                    ["Hail address", "Reviewer BldgID", "Generated stage", "Generated status", "Generated BldgID", "Comparison"],
                    replay_rows,
                ),
                "",
            ]
        )

    evidence = Counter()
    for row in overrides:
        stage = str(row.get("original_match_stage", ""))
        reason = str(row.get("review_reason_category", "") or "unspecified")
        outcome = (
            "proposed"
            if row.get("selected_was_proposed") is True
            else "neighbor"
            if row.get("selected_was_proposed") is False
            else "no_match"
        )
        evidence[(stage, reason, outcome)] += 1
    evidence_rows = [
        [stage or "—", reason, outcome.replace("_", " "), count]
        for (stage, reason, outcome), count in sorted(evidence.items())
    ]
    lines.extend(
        [
            "## Evidence by original review condition",
            "",
            *table(["Stage", "Reason", "Outcome", "Records"], evidence_rows),
            "",
            "## Candidate automatic rules",
            "",
        ]
    )

    rule_lines: list[str] = []
    reproduced = replay_counts["reproduced automatically"]
    conflicts = replay_counts["automatic result conflicts"]
    if reproduced:
        rule_lines.append(
            f"- The current deterministic rules reproduce {reproduced} of {len(overrides)} saved selections before overrides are applied; {conflicts} produce a conflicting automatic building."
        )
    if proposed == len(overrides):
        rule_lines.append(
            "- Every reviewer selection was in the proposed candidate set. This validates candidate recall, but candidate membership alone is not a deterministic selection rule when more than one footprint was proposed."
        )
    if not rule_lines:
        rule_lines.append(
            "- No review outcome supplies enough evidence for a new deterministic selection rule yet. Preserve the current manual-review treatment."
        )
    lines.extend(rule_lines)
    lines.extend(
        [
            "",
            "These are hypotheses, not pipeline changes. The script intentionally requires repeated, consistent decisions and still recommends validation on another street.",
            "",
            "## Decision detail",
            "",
        ]
    )

    detail_rows = []
    for override in sorted(
        overrides,
        key=lambda row: (str(row.get("street_name", "")), str(row.get("hail_address", ""))),
    ):
        review = review_by_id.get(override.get("building_id"), {})
        candidate_ids = override.get("original_candidate_bldgids") or str(
            review.get("candidate_bldgids", "")
        ).split("|")
        detail_rows.append(
            [
                override.get("street_name", ""),
                override.get("hail_address", ""),
                override.get("decision", "").replace("_", " "),
                override.get("bldgid") or "—",
                ", ".join(value for value in candidate_ids if value) or "—",
                "yes" if override.get("selected_was_proposed") is True else "no" if override.get("selected_was_proposed") is False else "—",
                override.get("note", "") or "—",
            ]
        )
    lines.extend(
        table(
            ["Street", "Hail address", "Decision", "Selected BldgID", "Proposed BldgIDs", "Proposed?", "Note"],
            detail_rows,
        )
    )
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH} ({len(overrides)} overrides)")


if __name__ == "__main__":
    main()
