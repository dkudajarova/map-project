import unittest
from collections import defaultdict

from scripts.build_building_database import (
    normalize_house,
    normalize_street,
    parse_house,
    propose_unclaimed_loose_address_candidates,
)


def point(address: str) -> dict:
    return {
        "feature_index": 1,
        "address": f"{address} Test Street",
        "street_name": "Test Street",
        "street": normalize_street("Test Street"),
        "house": normalize_house(address),
        "house_parts": parse_house(address),
        "bldgid": "stale",
        "coordinates": [-71.1, 42.37],
    }


def footprint(bldgid: str) -> dict:
    return {
        "type": "Feature",
        "properties": {"BldgID": bldgid},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-71.10001, 42.36999],
                [-71.09999, 42.36999],
                [-71.09999, 42.37001],
                [-71.10001, 42.37001],
                [-71.10001, 42.36999],
            ]],
        },
    }


def hail() -> dict[str, str]:
    return {
        "building_id": "test-st_10",
        "address_raw": "10",
        "street_name": "Test Street",
        "classification": "Current building",
        "construction_year": "1900",
        "summary_raw": "",
    }


def unmatched_row() -> dict:
    return {
        "building_id": "test-st_10",
        "match_status": "unmatched",
        "classification": "Current building",
        "matched_bldgid": "",
        "matched_bldgids": "",
        "override_decision": "",
    }


class HailResidualSpatialMatchingTests(unittest.TestCase):
    def test_routes_exact_address_near_unclaimed_footprint_to_review(self):
        row = unmatched_row()
        points_by_street = defaultdict(list)
        points_by_street[normalize_street("Test Street")].append(point("10"))
        propose_unclaimed_loose_address_candidates(
            [row], {"features": [footprint("new-footprint")]}, points_by_street,
            {"test-st_10": hail()},
        )
        self.assertEqual(row["match_status"], "review")
        self.assertEqual(row["candidate_bldgids"], "NEW-FOOTPRINT")
        self.assertEqual(
            row["review_reason_category"],
            "loose_address_near_unclaimed_footprint",
        )

    def test_does_not_propose_occupied_footprint(self):
        row = unmatched_row()
        accepted = {
            "building_id": "claimed",
            "match_status": "accepted",
            "matched_bldgid": "CLAIMED-FOOTPRINT",
            "matched_bldgids": "CLAIMED-FOOTPRINT",
        }
        points_by_street = defaultdict(list)
        points_by_street[normalize_street("Test Street")].append(point("10"))
        propose_unclaimed_loose_address_candidates(
            [accepted, row], {"features": [footprint("claimed-footprint")]},
            points_by_street, {"test-st_10": hail()},
        )
        self.assertEqual(row["match_status"], "unmatched")

    def test_preserves_explicit_no_map_match(self):
        row = unmatched_row()
        row["override_decision"] = "no_map_match"
        points_by_street = defaultdict(list)
        points_by_street[normalize_street("Test Street")].append(point("10"))
        propose_unclaimed_loose_address_candidates(
            [row], {"features": [footprint("new-footprint")]}, points_by_street,
            {"test-st_10": hail()},
        )
        self.assertEqual(row["match_status"], "unmatched")

    def test_accepts_same_street_address_within_ten_house_numbers(self):
        row = unmatched_row()
        points_by_street = defaultdict(list)
        points_by_street[normalize_street("Test Street")].append(point("19"))
        propose_unclaimed_loose_address_candidates(
            [row], {"features": [footprint("cross-street-footprint")]},
            points_by_street, {"test-st_10": hail()},
        )
        self.assertEqual(row["match_status"], "review")
        self.assertIn("Δ9 house numbers", row["match_reason"])

    def test_rejects_same_street_address_beyond_ten_house_numbers(self):
        row = unmatched_row()
        points_by_street = defaultdict(list)
        points_by_street[normalize_street("Test Street")].append(point("21"))
        propose_unclaimed_loose_address_candidates(
            [row], {"features": [footprint("too-far-by-number")]},
            points_by_street, {"test-st_10": hail()},
        )
        self.assertEqual(row["match_status"], "unmatched")


if __name__ == "__main__":
    unittest.main()
