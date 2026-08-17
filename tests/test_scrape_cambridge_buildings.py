import unittest

from scripts.scrape_cambridge_buildings import parse_page


class ScrapeCambridgeBuildingsTests(unittest.TestCase):
    def test_mixed_case_navigation_label_starts_a_new_section(self):
        html = """
        <dd><a href="#ellsworthpk">ELLSWORTH PARK</a></dd>
        <dd><a href="#elmst">ELM STREET (Cambridgeport)</a></dd>
        <dd><a name="ellsworthpk"></a><hr>ELLSWORTH PARK dead-end street 1894</dd>
        <dd>1 house 1895</dd>
        <dd><a name="elmst"></a><hr>ELM STREET (CAMBRIDGEPORT) through street 1805</dd>
        <dd>17 apartments 1886</dd>
        """
        buildings, _events = parse_page(html, "test")
        self.assertEqual(
            [(row["building_id"], row["street_name"]) for row in buildings],
            [("ellsworth-pk_1", "Ellsworth Park"), ("elm-st_17", "Elm Street")],
        )

    def test_section_heading_works_when_navigation_link_is_missing(self):
        html = """
        <dd><a href="#crawfordst">CRAWFORD STREET</a></dd>
        <dd><a name="crawfordst"></a><hr>CRAWFORD STREET through street 1848</dd>
        <dd>1 house 1850</dd>
        <dd><a name="creighton"></a><hr>CREIGHTON STREET through street 1868</dd>
        <dd>2 house 1870</dd>
        """
        buildings, _events = parse_page(html, "test")
        self.assertEqual(buildings[1]["street_name"], "Creighton Street")
        self.assertEqual(buildings[1]["building_id"], "creighton-st_2")

    def test_preserves_mc_capitalization(self):
        html = """
        <dd><a href="#maynardpl">MAYNARD PLACE</a></dd>
        <dd><a href="#mccarthyrd">McCARTHY ROAD</a></dd>
        <dd><a name="maynardpl"></a><hr>MAYNARD PLACE dead-end street 1872</dd>
        <dd>1 house 1872</dd>
        <dd><a name="mccarthyrd"></a><hr>McCARTHY ROAD through street 1861</dd>
        <dd>2 house 1862</dd>
        """
        buildings, _events = parse_page(html, "test")
        self.assertEqual(buildings[1]["street_name"], "McCarthy Road")


if __name__ == "__main__":
    unittest.main()
