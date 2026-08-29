import unittest

from scripts.build_building_database import (
    assessor_year_takes_precedence,
    hail_year_overrides_assessor_placeholder,
)


class ConstructionYearResolutionTests(unittest.TestCase):
    def test_assessor_year_from_2003_takes_precedence(self):
        self.assertTrue(assessor_year_takes_precedence(2003))

    def test_assessor_year_before_2003_does_not_take_precedence(self):
        self.assertFalse(assessor_year_takes_precedence(2002))

    def test_missing_assessor_year_does_not_take_precedence(self):
        self.assertFalse(assessor_year_takes_precedence(None))

    def test_harvard_yard_1850_assessor_year_is_a_placeholder(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("318-24", 1850))

    def test_harvard_yard_exception_is_narrowly_scoped(self):
        self.assertFalse(hail_year_overrides_assessor_placeholder("318-24", 1851))
        self.assertFalse(hail_year_overrides_assessor_placeholder("319-1", 1850))


if __name__ == "__main__":
    unittest.main()
