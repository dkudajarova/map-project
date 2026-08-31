import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from development_logs import completed_year, load_completed_projects  # noqa: E402


class DevelopmentLogEligibilityTests(unittest.TestCase):
    def test_requires_complete_status_and_year(self):
        self.assertEqual(completed_year({"Status": "Complete", "Year Complete": "2024"}), 2024)
        self.assertIsNone(completed_year({"Status": "Permitting", "Year Complete": "2024"}))
        self.assertIsNone(completed_year({"Status": "Complete", "Year Complete": ""}))
        self.assertIsNone(completed_year({"Project Stage": "Complete", "Year Complete": "1996"}))
        self.assertIsNone(
            completed_year({"Status": "Complete", "Year Complete": str(date.today().year + 1)})
        )

    def test_map_lot_rows_supersede_historical_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            historical = directory / "Development_Log_Historical_Projects_20260101.csv"
            map_lots = directory / "Development_Log_MapLots_20260101.csv"
            with historical.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["ProjectID", "Project Stage", "Year Complete"])
                writer.writeheader()
                writer.writerow({"ProjectID": "10", "Project Stage": "Complete", "Year Complete": "2020"})
            with map_lots.open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["Project ID", "Status", "Year Complete", "Map-Lot"],
                )
                writer.writeheader()
                writer.writerow({"Project ID": "10", "Status": "Complete", "Year Complete": "2021", "Map-Lot": " 80-1"})
                writer.writerow({"Project ID": "10", "Status": "Complete", "Year Complete": "2021", "Map-Lot": "80-2"})

            projects = load_completed_projects(directory)

        self.assertEqual([(project.map_lot, project.year_complete) for project in projects], [("80-1", 2021), ("80-2", 2021)])


if __name__ == "__main__":
    unittest.main()
