import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_building_database import load_fun_facts


class BuildingFunFactTests(unittest.TestCase):
    def write_facts(self, directory: str, facts: list[dict]) -> Path:
        path = Path(directory) / "facts.json"
        path.write_text(json.dumps({"version": 1, "facts": facts}), encoding="utf-8")
        return path

    def test_loads_extensible_source_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_facts(
                directory,
                [
                    {
                        "bldgid": "10-1",
                        "text": "This building once housed a neighborhood bakery.",
                        "source": {
                            "type": "future_archive",
                            "label": "Neighborhood archive",
                            "record_id": "A-7",
                            "url": "https://example.org/records/A-7",
                        },
                        "reviewed_at": "2026-08-17T12:00:00Z",
                    }
                ],
            )
            facts = load_fun_facts(path, {"10-1"})

        self.assertEqual(facts["10-1"]["source_type"], "future_archive")
        self.assertEqual(facts["10-1"]["source_record_id"], "A-7")

    def test_rejects_unknown_footprint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_facts(
                directory,
                [{
                    "bldgid": "missing",
                    "text": "A fact.",
                    "source": {"type": "hail", "label": "Hail register"},
                }],
            )
            with self.assertRaisesRegex(ValueError, "unknown BldgID"):
                load_fun_facts(path, {"10-1"})

    def test_rejects_duplicate_fact_for_footprint(self):
        fact = {
            "bldgid": "10-1",
            "text": "A fact.",
            "source": {"type": "hail", "label": "Hail register"},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_facts(directory, [fact, fact])
            with self.assertRaisesRegex(ValueError, "Duplicate fun fact"):
                load_fun_facts(path, {"10-1"})

    def test_rejects_unsafe_source_url(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_facts(
                directory,
                [{
                    "bldgid": "10-1",
                    "text": "A fact.",
                    "source": {
                        "type": "wikipedia",
                        "label": "Wikipedia",
                        "url": "javascript:alert(1)",
                    },
                }],
            )
            with self.assertRaisesRegex(ValueError, "invalid source URL"):
                load_fun_facts(path, {"10-1"})


if __name__ == "__main__":
    unittest.main()
