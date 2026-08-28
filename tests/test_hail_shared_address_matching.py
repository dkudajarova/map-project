import unittest

from scripts.build_building_database import accept_unclaimed_multi_footprint_records


def match_row(building_id, status, candidates, address="10 Example St", matched=""):
    return {
        "building_id": building_id,
        "match_status": status,
        "treatment": "auto_accept" if status == "accepted" else "manual_review",
        "candidate_address_point_count": len(candidates),
        "candidate_bldgid_count": len(candidates),
        "candidate_bldgids": "|".join(candidates),
        "candidate_addresses": address,
        "matched_bldgid": matched if matched and "|" not in matched else "",
        "matched_bldgids": matched,
        "match_reason": "old reason",
        "review_reason_category": "multiple_footprint_candidates",
        "review_reason_summary": "old summary",
    }


def point(address, bldgid):
    return {"address": address, "bldgid": bldgid}


class HailSharedAddressMatchingTests(unittest.TestCase):
    def test_accepts_all_unclaimed_footprints_with_same_address(self):
        row = match_row("hail-ambiguous", "review", ["one", "two"])
        points = {
            "one": [point("10 Example St", "one")],
            "two": [point("10 Example St", "two")],
        }

        accept_unclaimed_multi_footprint_records([row], points, {})

        self.assertEqual(row["match_status"], "accepted")
        self.assertEqual(row["matched_bldgids"], "one|two")
        self.assertEqual(row["treatment"], "auto_accept_unclaimed_multi_footprint")

    def test_excludes_footprint_claimed_by_another_match(self):
        claimed = match_row("hail-exact", "accepted", ["one"], matched="one")
        ambiguous = match_row("hail-ambiguous", "review", ["one", "two"])
        points = {
            "one": [point("10 Example St", "one")],
            "two": [point("10 Example St", "two")],
        }

        accept_unclaimed_multi_footprint_records([claimed, ambiguous], points, {})

        self.assertEqual(ambiguous["match_status"], "accepted")
        self.assertEqual(ambiguous["matched_bldgid"], "two")
        self.assertEqual(ambiguous["matched_bldgids"], "two")

    def test_different_candidate_addresses_remain_for_review(self):
        row = match_row("hail-ambiguous", "review", ["one", "two"])
        row["candidate_addresses"] = "10 Example St|10-R Example St"

        accept_unclaimed_multi_footprint_records([row], {}, {})

        self.assertEqual(row["match_status"], "review")

    def test_block_description_accepts_unclaimed_range_footprints(self):
        claimed = match_row("eliot-st_14a", "accepted", ["396-1"], "14-A Eliot St", "396-1")
        block = match_row("eliot-st_10-14", "review", ["396-1", "396-5", "396-8"])
        block["candidate_addresses"] = "10 Eliot St|12 Eliot St|14 Eliot St"
        points = {
            "396-1": [point("14 Eliot St", "396-1")],
            "396-5": [point("10 Eliot St", "396-5")],
            "396-8": [point("12 Eliot St", "396-8")],
        }
        hail = {
            "eliot-st_10-14": {"building_type": "block [dwellings & stores]"}
        }

        accept_unclaimed_multi_footprint_records([claimed, block], points, hail)

        self.assertEqual(block["match_status"], "accepted")
        self.assertEqual(block["matched_bldgids"], "396-5|396-8")
        self.assertEqual(block["candidate_addresses"], "10 Eliot St|12 Eliot St")


if __name__ == "__main__":
    unittest.main()
