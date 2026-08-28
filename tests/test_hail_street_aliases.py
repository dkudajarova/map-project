import unittest
from collections import defaultdict

from scripts.build_building_database import match_hail_record, normalize_house, normalize_street, parse_house


def hail(address: str, classification: str = "Current building") -> dict[str, str]:
    return {
        "building_id": f"allen-{address}",
        "street_name": "Allen Drive",
        "address_raw": address,
        "classification": classification,
        "razed": "false",
        "historic_address": "",
        "building_type": "house",
    }


def point(address: str, bldgid: str) -> dict:
    return {
        "feature_index": hash((address, bldgid)),
        "address": f"{address} Bishop Allen Dr",
        "street_name": "Bishop Allen Dr",
        "street": normalize_street("Bishop Allen Dr"),
        "house": normalize_house(address),
        "house_parts": parse_house(address),
        "bldgid": bldgid,
    }


def match(record: dict[str, str], points: list[dict]):
    points_by_street = defaultdict(list)
    points_by_number = defaultdict(list)
    for candidate in points:
        points_by_street[candidate["street"]].append(candidate)
        if candidate["house_parts"].minimum is not None:
            points_by_number[candidate["house_parts"].minimum].append(candidate)
    return match_hail_record(
        record,
        {},
        points_by_street,
        points_by_number,
        {candidate["bldgid"] for candidate in points},
        {(normalize_street("Allen Drive"), normalize_street("Bishop Allen Dr"))},
        set(),
    )


class HailStreetAliasTests(unittest.TestCase):
    def test_explicit_alias_does_not_require_small_edit_distance(self):
        result = match(hail("39"), [point("39", "602-37")])
        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "602-37")
        self.assertEqual(result["treatment"], "confirmed_alias")

    def test_range_can_match_a_later_number_on_the_alias_street(self):
        result = match(hail("53-55"), [point("55", "602-10")])
        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "602-10")

    def test_multiple_alias_footprints_are_accepted_for_building_complex(self):
        result = match(hail("5-7"), [point("5", "one"), point("7", "two")])
        self.assertEqual(result["match_status"], "review")
        self.assertEqual(result["review_reason_category"], "multiple_footprint_candidates")

    def test_single_building_complex_alias_footprint_is_accepted(self):
        result = match(hail("46-50", "Building complex"), [point("48", "632-3")])
        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "632-3")

    def test_multiple_building_complex_alias_footprints_are_accepted(self):
        result = match(
            hail("46-50", "Building complex"),
            [point("46", "one"), point("48", "two"), point("50", "three")],
        )
        self.assertEqual(result["match_status"], "accepted")
        self.assertEqual(result["matched_bldgid"], "")
        self.assertEqual(result["candidate_bldgids"], "one|three|two")


if __name__ == "__main__":
    unittest.main()
