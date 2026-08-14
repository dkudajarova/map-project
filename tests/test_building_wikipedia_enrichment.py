import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_building_database import load_approved_wikipedia_matches
from scripts.enrich_wikipedia_buildings import enrich_wikipedia_properties


class WikipediaEnrichmentTests(unittest.TestCase):
    def test_loader_groups_only_approved_articles_and_sorts_titles(self):
        csv_text = (
            "wikipedia_page_id,wikipedia_title,wikipedia_url,matched_bldgid,decision_status\n"
            "2,Zeta House,https://en.wikipedia.org/wiki/Zeta_House,10-1,approved\n"
            "3,Rejected House,https://en.wikipedia.org/wiki/Rejected_House,10-1,rejected\n"
            "1,Alpha House,https://en.wikipedia.org/wiki/Alpha_House,10-1,approved\n"
            "4,Pending House,https://en.wikipedia.org/wiki/Pending_House,10-2,needs_review\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matches.csv"
            path.write_text(csv_text, encoding="utf-8")
            grouped = load_approved_wikipedia_matches(path)

        self.assertEqual(list(grouped), ["10-1"])
        self.assertEqual(
            [article["page_id"] for article in grouped["10-1"]],
            [1, 2],
        )

    def test_loader_rejects_duplicate_approved_page_ids(self):
        csv_text = (
            "wikipedia_page_id,wikipedia_title,wikipedia_url,matched_bldgid,decision_status\n"
            "1,Alpha House,https://en.wikipedia.org/wiki/Alpha_House,10-1,approved\n"
            "1,Alpha House,https://en.wikipedia.org/wiki/Alpha_House,10-2,approved\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matches.csv"
            path.write_text(csv_text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate approved"):
                load_approved_wikipedia_matches(path)

    def test_enrichment_replaces_existing_wikipedia_properties(self):
        collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {
                        "BldgID": "10-1",
                        "wikipedia_article_count": 99,
                        "wikipedia_articles_json": "stale",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {"BldgID": "10-2"},
                },
            ],
        }
        approved = {
            "10-1": [
                {
                    "page_id": 1,
                    "title": "Alpha House",
                    "url": "https://en.wikipedia.org/wiki/Alpha_House",
                }
            ]
        }

        enriched, linked_features = enrich_wikipedia_properties(collection, approved)

        self.assertEqual(linked_features, 1)
        first = enriched["features"][0]["properties"]
        second = enriched["features"][1]["properties"]
        self.assertEqual(first["wikipedia_article_count"], 1)
        self.assertEqual(json.loads(first["wikipedia_articles_json"])[0]["page_id"], 1)
        self.assertEqual(second["wikipedia_article_count"], 0)
        self.assertIsNone(second["wikipedia_articles_json"])

    def test_enrichment_rejects_approved_missing_building(self):
        collection = {"type": "FeatureCollection", "features": []}
        with self.assertRaisesRegex(ValueError, "missing BldgIDs: 10-1"):
            enrich_wikipedia_properties(collection, {"10-1": []})


if __name__ == "__main__":
    unittest.main()
