import unittest

from scripts.build_building_database import references_move_to_another_location


class HailMovedRecordTests(unittest.TestCase):
    def test_detects_explicit_move_to_destination(self):
        self.assertTrue(
            references_move_to_another_location(
                "73 house 1821; moved to Bradbury st 38 1875"
            )
        )

    def test_detects_move_and_joined_to_destination(self):
        self.assertTrue(
            references_move_to_another_location(
                "457 house 1825; moved and joined to Coolidge pl 2-4 1884"
            )
        )

    def test_does_not_treat_moved_from_as_departure(self):
        self.assertFalse(
            references_move_to_another_location(
                "9 house 1840; moved from Follen st 25 1889"
            )
        )

    def test_does_not_cross_detail_clauses(self):
        self.assertFalse(
            references_move_to_another_location(
                "House moved on lot 1929; altered to offices 1940"
            )
        )


if __name__ == "__main__":
    unittest.main()
