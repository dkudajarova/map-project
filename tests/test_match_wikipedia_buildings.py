import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Point, Polygon

from scripts.match_wikipedia_buildings import PROJECTED_CRS, match_articles, missing_decision_rows


class WikipediaBuildingMatchingTests(unittest.TestCase):
    def articles(self, coordinates):
        frame = pd.DataFrame(
            [
                {
                    "page_id": index + 1,
                    "title": f"Article {index + 1}",
                    "url": f"https://en.wikipedia.org/wiki/Article_{index + 1}",
                    "longitude": longitude,
                    "latitude": latitude,
                }
                for index, (longitude, latitude) in enumerate(coordinates)
            ]
        )
        return gpd.GeoDataFrame(
            frame,
            geometry=gpd.points_from_xy(frame.longitude, frame.latitude),
            crs=PROJECTED_CRS,
        )

    def buildings(self, records):
        return gpd.GeoDataFrame(records, geometry="geometry", crs=PROJECTED_CRS)

    def test_unique_contained_point_is_strong(self):
        rows = match_articles(
            self.articles([(5, 5)]),
            self.buildings([{"BldgID": "one", "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])}]),
        )
        self.assertEqual(rows[0]["match_method"], "contained")
        self.assertEqual(rows[0]["confidence_status"], "strong")
        self.assertEqual(rows[0]["matched_bldgid"], "one")
        self.assertEqual(rows[0]["decision_status"], "needs_review")

    def test_human_approval_publishes_current_contained_match(self):
        articles = self.articles([(5, 5)]).to_crs("EPSG:4326")
        article = articles.iloc[0]
        decisions = {
            1: {
                "wikipedia_page_id": 1,
                "decision": "approved",
                "bldgid": "one",
                "latitude": article["latitude"],
                "longitude": article["longitude"],
            }
        }
        row = match_articles(
            articles,
            self.buildings([{"BldgID": "one", "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])}]),
            decisions,
        )[0]
        self.assertEqual(row["decision_status"], "approved")
        self.assertEqual(row["matched_bldgid"], "one")

    def test_overlapping_buildings_are_ambiguous(self):
        rows = match_articles(
            self.articles([(5, 5)]),
            self.buildings([
                {"BldgID": "two", "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])},
                {"BldgID": "one", "geometry": Polygon([(4, 4), (8, 4), (8, 8), (4, 8)])},
            ]),
        )
        self.assertEqual(rows[0]["candidate_bldgids"], "one|two")
        self.assertEqual(rows[0]["confidence_status"], "ambiguous")

    def test_polygon_hole_is_not_contained(self):
        polygon = Polygon(
            [(0, 0), (10, 0), (10, 10), (0, 10)],
            holes=[[(4, 4), (6, 4), (6, 6), (4, 6)]],
        )
        row = match_articles(self.articles([(5, 5)]), self.buildings([{"BldgID": "one", "geometry": polygon}]))[0]
        self.assertEqual(row["match_method"], "nearest")
        self.assertAlmostEqual(float(row["match_distance_meters"]), 1.0, places=2)

    def test_multipolygon_component_contains_point(self):
        geometry = MultiPolygon([
            Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),
            Polygon([(8, 8), (10, 8), (10, 10), (8, 10)]),
        ])
        row = match_articles(self.articles([(9, 9)]), self.buildings([{"BldgID": "one", "geometry": geometry}]))[0]
        self.assertEqual(row["match_method"], "contained")

    def test_nearest_match_and_threshold(self):
        building = self.buildings([{"BldgID": "one", "geometry": Polygon([(10, 0), (20, 0), (20, 10), (10, 10)])}])
        near, far = match_articles(self.articles([(5, 5), (-20, 5)]), building, nearest_threshold_meters=25)
        self.assertEqual(near["match_method"], "nearest")
        self.assertAlmostEqual(float(near["match_distance_meters"]), 5.0, places=2)
        self.assertEqual(far["match_method"], "none")

    def test_human_rejection_is_preserved_when_coordinate_is_unchanged(self):
        articles = self.articles([(5, 5)])
        # Decision coordinates are WGS84, so use the article represented in that CRS.
        articles = articles.to_crs("EPSG:4326")
        article = articles.iloc[0]
        decisions = {
            1: {
                "wikipedia_page_id": 1,
                "decision": "rejected",
                "bldgid": None,
                "latitude": article["latitude"],
                "longitude": article["longitude"],
            }
        }
        row = match_articles(
            articles,
            self.buildings([{"BldgID": "one", "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])}]),
            decisions,
        )[0]
        self.assertEqual(row["decision_status"], "rejected")

    def test_moved_decision_becomes_stale(self):
        articles = self.articles([(5, 5)]).to_crs("EPSG:4326")
        article = articles.iloc[0]
        decisions = {
            1: {
                "wikipedia_page_id": 1,
                "decision": "approved",
                "bldgid": "one",
                "latitude": article["latitude"] + 0.001,
                "longitude": article["longitude"],
            }
        }
        row = match_articles(
            articles,
            self.buildings([{"BldgID": "one", "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])}]),
            decisions,
        )[0]
        self.assertEqual(row["decision_status"], "stale_decision")

    def test_missing_reviewed_article_becomes_stale(self):
        rows = missing_decision_rows(
            {7: {"decision": "approved", "bldgid": "one", "wikipedia_title": "Gone"}},
            set(),
        )
        self.assertEqual(rows[0]["decision_status"], "stale_decision")
        self.assertIn("missing", rows[0]["review_reason"])

    def test_manual_marker_approval_can_preserve_non_candidate_building(self):
        articles = self.articles([(5, 5)]).to_crs("EPSG:4326")
        article = articles.iloc[0]
        decisions = {
            1: {
                "wikipedia_page_id": 1,
                "decision": "approved",
                "bldgid": "manual",
                "selection_method": "manual_marker",
                "latitude": article["latitude"],
                "longitude": article["longitude"],
            }
        }
        buildings = self.buildings([
            {"BldgID": "generated", "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])},
            {"BldgID": "manual", "geometry": Polygon([(100, 100), (110, 100), (110, 110), (100, 110)])},
        ])
        row = match_articles(articles, buildings, decisions)[0]
        self.assertEqual(row["decision_status"], "approved")
        self.assertEqual(row["matched_bldgid"], "manual")


if __name__ == "__main__":
    unittest.main()
