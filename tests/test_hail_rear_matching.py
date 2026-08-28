import unittest
from collections import defaultdict

from scripts.build_building_database import (
    match_hail_record,
    normalize_house,
    normalize_street,
    parse_house,
)


def hail(address: str, classification: str = "Current building") -> dict[str, str]:
    return {
        "building_id": f"dana-st_{address.casefold()}",
        "street_name": "Dana Street",
        "address_raw": address,
        "classification": classification,
        "razed": "false",
        "historic_address": "",
        "building_type": "house",
    }


def point(address: str, bldgid: str, street_name: str = "Dana St") -> dict:
    return {
        "feature_index": hash((address, bldgid)),
        "address": f"{address} {street_name}",
        "street_name": street_name,
        "street": normalize_street(street_name),
        "house": normalize_house(address),
        "house_parts": parse_house(address),
        "bldgid": bldgid,
    }


def match(record: dict[str, str], points: list[dict], confirmed_aliases=None):
    exact_index = defaultdict(list)
    points_by_street = defaultdict(list)
    points_by_number = defaultdict(list)
    for candidate in points:
        exact_index[(candidate["street"], candidate["house"])].append(candidate)
        points_by_street[candidate["street"]].append(candidate)
        points_by_number[candidate["house_parts"].minimum].append(candidate)
    return match_hail_record(
        record,
        exact_index,
        points_by_street,
        points_by_number,
        {candidate["bldgid"] for candidate in points},
        confirmed_aliases or set(),
        set(),
    )


class HailRearMatchingTests(unittest.TestCase):
    def test_explicit_letter_modifier_matches_hyphenated_canonical_address(self):
        result = match(
            hail("67A", "Addition, rear, or secondary building"),
            [point("67", "front"), point("67-A", "auxiliary")],
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "auxiliary")
        self.assertEqual(result["match_stage"], "1")

    def test_plain_hail_range_prefers_front_over_rear_canonical_address(self):
        result = match(
            hail("63-65"),
            [point("63", "front"), point("65", "front"), point("65-R", "rear")],
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "front")
        self.assertNotIn("rear", result["candidate_bldgids"])

    def test_plain_hail_range_prefers_front_over_lettered_alias_address(self):
        alias = {(normalize_street("Dana Street"), normalize_street("Mt Auburn St"))}
        result = match(
            hail("4-6"),
            [
                point("4", "476-3", "Mt Auburn St"),
                point("6", "476-3", "Mt Auburn St"),
                point("4-A", "476-10", "Mt Auburn St"),
            ],
            alias,
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "476-3")
        self.assertEqual(result["candidate_bldgids"], "476-3")

    def test_numeric_unit_is_not_treated_as_auxiliary_building_modifier(self):
        result = match(
            hail("4-6"),
            [point("4", "front"), point("4-2", "unit")],
        )

        self.assertEqual(result["match_status"], "review")

    def test_fractional_address_is_treated_as_rear_designation(self):
        result = match(
            hail("122", "Addition, rear, or secondary building"),
            [point("122", "front"), point("122-1/2", "rear")],
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "rear")
        self.assertEqual(result["treatment"], "auto_accept_unique_modifier")

    def test_plain_range_excludes_fractional_rear_footprints(self):
        result = match(
            hail("122-124"),
            [
                point("122", "front"),
                point("124", "front"),
                point("122-1/2", "rear"),
                point("124-1/2", "rear"),
            ],
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "front")

    def test_explicit_rear_hail_record_still_matches_rear_address(self):
        result = match(
            hail("65r", "Addition, rear, or secondary building"),
            [point("65", "front"), point("65-R", "rear")],
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "rear")

    def test_secondary_record_uses_only_unique_modified_address(self):
        result = match(
            hail("4r", "Addition, rear, or secondary building"),
            [point("4", "front"), point("4-A", "secondary")],
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "secondary")
        self.assertEqual(result["treatment"], "auto_accept_unique_modifier")

    def test_secondary_record_uses_unique_modifier_on_confirmed_alias(self):
        alias = {(normalize_street("Dana Street"), normalize_street("Mt Auburn St"))}
        result = match(
            hail("4r", "Addition, rear, or secondary building"),
            [point("4", "front", "Mt Auburn St"), point("4-A", "476-10", "Mt Auburn St")],
            alias,
        )

        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "476-10")
        self.assertEqual(result["treatment"], "confirmed_alias_unique_modifier")

    def test_multiple_modified_addresses_remain_for_review(self):
        result = match(
            hail("4r", "Addition, rear, or secondary building"),
            [point("4", "front"), point("4-A", "one"), point("4-B", "two")],
        )

        self.assertEqual(result["match_status"], "review")


if __name__ == "__main__":
    unittest.main()
