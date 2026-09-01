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

    def test_harvard_law_and_oxford_parcel_1840_is_a_placeholder(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("253-6", 1840))
        self.assertTrue(hail_year_overrides_assessor_placeholder("266-18", 1840))
        self.assertFalse(hail_year_overrides_assessor_placeholder("266-18", 1841))

    def test_verified_campus_footprint_exceptions_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("237-4", 1860))
        self.assertTrue(hail_year_overrides_assessor_placeholder("266-11", 1700))
        self.assertTrue(hail_year_overrides_assessor_placeholder("241-48", 2007))
        self.assertFalse(hail_year_overrides_assessor_placeholder("237-5", 1860))
        self.assertFalse(hail_year_overrides_assessor_placeholder("266-11", 1701))

    def test_radcliffe_yard_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("307-2", 1890))
        self.assertTrue(hail_year_overrides_assessor_placeholder("307-15", 1890))
        self.assertFalse(hail_year_overrides_assessor_placeholder("307-3", 1890))

    def test_appian_way_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("319-2", 1930))
        self.assertTrue(hail_year_overrides_assessor_placeholder("319-12", 1860))
        self.assertTrue(hail_year_overrides_assessor_placeholder("319-13", 1860))
        self.assertFalse(hail_year_overrides_assessor_placeholder("319-11", 1860))

    def test_mather_house_assessor_placeholder_is_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("513-3", 1910))
        self.assertFalse(hail_year_overrides_assessor_placeholder("513-3", 1911))
        self.assertFalse(hail_year_overrides_assessor_placeholder("513-2", 1910))

    def test_currier_house_assessor_placeholders_are_exact(self):
        for bldgid in ("206-3", "206-7", "206-11", "206-13", "206-15"):
            self.assertTrue(hail_year_overrides_assessor_placeholder(bldgid, 1910))
            self.assertFalse(hail_year_overrides_assessor_placeholder(bldgid, 1911))
        self.assertFalse(hail_year_overrides_assessor_placeholder("206-10", 1910))

    def test_pforzheimer_house_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("206-2", 1910))
        self.assertTrue(hail_year_overrides_assessor_placeholder("206-4", 1910))
        self.assertFalse(hail_year_overrides_assessor_placeholder("206-2", 1911))
        self.assertFalse(hail_year_overrides_assessor_placeholder("206-8", 1910))

    def test_adams_house_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("395-5", 1903))
        self.assertTrue(hail_year_overrides_assessor_placeholder("401-11", 1920))
        self.assertFalse(hail_year_overrides_assessor_placeholder("395-5", 1902))
        self.assertFalse(hail_year_overrides_assessor_placeholder("401-10", 1920))

    def test_dunster_house_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("513-1", 1915))
        self.assertTrue(hail_year_overrides_assessor_placeholder("513-2", 1915))
        self.assertFalse(hail_year_overrides_assessor_placeholder("513-1", 1916))
        self.assertFalse(hail_year_overrides_assessor_placeholder("513-3", 1915))

    def test_eliot_house_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("437-2", 1920))
        self.assertTrue(hail_year_overrides_assessor_placeholder("437-13", 1920))
        self.assertFalse(hail_year_overrides_assessor_placeholder("437-2", 1921))
        self.assertFalse(hail_year_overrides_assessor_placeholder("437-4", 1920))

    def test_kirkland_house_assessor_placeholders_are_exact(self):
        for bldgid in ("437-1", "437-3", "437-9"):
            self.assertTrue(hail_year_overrides_assessor_placeholder(bldgid, 1920))
            self.assertFalse(hail_year_overrides_assessor_placeholder(bldgid, 1921))
        self.assertFalse(hail_year_overrides_assessor_placeholder("437-6", 1920))

    def test_leverett_tower_assessor_placeholders_are_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("498-2", 1965))
        self.assertTrue(hail_year_overrides_assessor_placeholder("498-3", 1965))
        self.assertFalse(hail_year_overrides_assessor_placeholder("498-2", 1966))
        self.assertFalse(hail_year_overrides_assessor_placeholder("498-6", 1965))

    def test_lowell_house_assessor_placeholder_is_exact(self):
        self.assertTrue(hail_year_overrides_assessor_placeholder("424-3", 1900))
        self.assertFalse(hail_year_overrides_assessor_placeholder("424-3", 1901))
        self.assertFalse(hail_year_overrides_assessor_placeholder("424-6", 1900))

    def test_quincy_house_assessor_placeholders_are_exact(self):
        for bldgid in ("438-1", "438-6", "438-8"):
            self.assertTrue(hail_year_overrides_assessor_placeholder(bldgid, 1950))
            self.assertFalse(hail_year_overrides_assessor_placeholder(bldgid, 1951))
        self.assertFalse(hail_year_overrides_assessor_placeholder("438-2", 1950))

    def test_winthrop_house_assessor_placeholders_are_exact(self):
        for bldgid in ("437-5", "437-7", "437-10"):
            self.assertTrue(hail_year_overrides_assessor_placeholder(bldgid, 1920))
            self.assertFalse(hail_year_overrides_assessor_placeholder(bldgid, 1921))
        self.assertFalse(hail_year_overrides_assessor_placeholder("437-8", 1920))


if __name__ == "__main__":
    unittest.main()
