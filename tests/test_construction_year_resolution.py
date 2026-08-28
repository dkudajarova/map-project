import unittest

from scripts.build_building_database import assessor_year_takes_precedence


class ConstructionYearResolutionTests(unittest.TestCase):
    def test_assessor_year_from_2003_takes_precedence(self):
        self.assertTrue(assessor_year_takes_precedence(2003))

    def test_assessor_year_before_2003_does_not_take_precedence(self):
        self.assertFalse(assessor_year_takes_precedence(2002))

    def test_missing_assessor_year_does_not_take_precedence(self):
        self.assertFalse(assessor_year_takes_precedence(None))


if __name__ == "__main__":
    unittest.main()