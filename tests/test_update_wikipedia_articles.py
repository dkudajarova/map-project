import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.update_wikipedia_articles import (
    boundary_polygons,
    build_snapshot,
    fetch_articles,
    load_feature_collection,
    point_in_cambridge,
    search_geometry,
    write_json_atomically,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures/wikipedia"


class WikipediaRetrievalTests(unittest.TestCase):
    def test_fetch_articles_queries_tiles_deduplicates_and_sorts_page_ids(self):
        requests = []

        def open_url(request, _timeout):
            requests.append(request)
            return {
                "query": {
                    "geosearch": [
                        {
                            "pageid": 20,
                            "title": "Second Article",
                            "lat": 42.3736,
                            "lon": -71.1097,
                        },
                        {
                            "pageid": 10,
                            "title": "First Article",
                            "lat": 42.374,
                            "lon": -71.1089,
                        },
                    ]
                }
            }

        boundary = load_feature_collection(FIXTURE_ROOT / "buildings.geojson")
        articles, tile_count = fetch_articles(boundary, "TestBot/1.0 (test)", open_url)

        self.assertEqual([article["page_id"] for article in articles], [10, 20])
        self.assertEqual(len(requests), tile_count)
        first_query = parse_qs(urlparse(requests[0].full_url).query)
        self.assertIn("gsbbox", first_query)

    def test_fixture_articles_are_clipped_to_fixture_buildings_extent_polygon(self):
        articles = json.loads((FIXTURE_ROOT / "articles.json").read_text())["articles"]
        boundary = load_feature_collection(FIXTURE_ROOT / "buildings.geojson")
        polygons = boundary_polygons(boundary)
        center_latitude, center_longitude, radius = search_geometry(boundary)

        snapshot = build_snapshot(
            articles,
            polygons,
            "2026-08-13T12:00:00Z",
            center_latitude,
            center_longitude,
            radius,
            1,
        )

        self.assertEqual(snapshot["source"]["retrieved_count"], 2)
        self.assertEqual(snapshot["source"]["cambridge_count"], 2)

    def test_polygon_holes_are_excluded_and_outer_boundary_is_included(self):
        polygons = [
            [
                [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
                [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]],
            ]
        ]
        self.assertTrue(point_in_cambridge(0, 2, polygons))
        self.assertTrue(point_in_cambridge(0.5, 0.5, polygons))
        self.assertFalse(point_in_cambridge(2, 2, polygons))

    def test_atomic_write_replaces_complete_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            output.write_text('{"old": true}\n')
            write_json_atomically(output, {"new": True})
            self.assertEqual(json.loads(output.read_text()), {"new": True})


if __name__ == "__main__":
    unittest.main()
