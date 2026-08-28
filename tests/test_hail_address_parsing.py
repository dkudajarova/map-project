import unittest

from scripts.build_building_database import (
    house_numbers_overlap,
    normalize_house,
    parse_house,
)


class HailAddressParsingTests(unittest.TestCase):
    def test_fraction_notation_has_one_canonical_form(self):
        self.assertEqual(normalize_house("185-1/2"), "1851/2")
        self.assertEqual(normalize_house("185½"), "1851/2")
        self.assertEqual(normalize_house("185 1/2"), "1851/2")

    def test_fraction_is_a_single_address_not_a_range(self):
        parts = parse_house("185-1/2")
        self.assertEqual(parts.minimum, 185)
        self.assertEqual(parts.maximum, 185)
        self.assertEqual(parts.suffix, "1/2")
        self.assertFalse(parts.is_range)

    def test_fraction_does_not_overlap_unrelated_range(self):
        self.assertFalse(
            house_numbers_overlap(parse_house("185-1/2"), parse_house("119-121"))
        )

    def test_standard_numeric_range_is_unchanged(self):
        parts = parse_house("119-121")
        self.assertEqual((parts.minimum, parts.maximum), (119, 121))
        self.assertTrue(parts.is_range)

    def test_numeric_unit_suffix_is_not_a_range(self):
        parts = parse_house("328-2")
        self.assertEqual((parts.minimum, parts.maximum, parts.suffix), (328, 328, "2"))
        self.assertFalse(parts.is_range)

    def test_numeric_unit_suffix_does_not_overlap_unrelated_range(self):
        self.assertFalse(
            house_numbers_overlap(parse_house("174-176"), parse_house("328-2"))
        )


if __name__ == "__main__":
    unittest.main()
