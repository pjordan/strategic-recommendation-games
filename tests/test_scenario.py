import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("scenario", Path(__file__).resolve().parents[1] / "tools/scenario.py")
scenario = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenario)

class ScenarioChecks(unittest.TestCase):
    def test_complete_frozen_scenario(self):
        self.assertEqual([x["records"] for x in scenario.validate()], [279, 186])

    def test_actor_views_keep_preferences_separate(self):
        recommender = scenario.load_context()
        buyer = scenario.load_context("buyer")
        self.assertEqual(set(recommender), {"public_context"})
        self.assertNotIn("80000", str(recommender))
        self.assertNotIn("espresso-buyer-1", str(recommender))
        self.assertEqual(buyer["private_user_preferences"]["budget"]["maximum_equipment_total_cents"], 80000)

    def test_changed_record_is_detected(self):
        data = copy.deepcopy(scenario.read(scenario.ROOT / "recommendations/bing.json"))
        data["records"][0]["displayed_price_cents"] += 1
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            scenario.validate_dataset(data)

    def test_missing_record_is_detected(self):
        data = copy.deepcopy(scenario.read(scenario.ROOT / "recommendations/google.json"))
        data["records"].pop()
        with self.assertRaisesRegex(ValueError, "missing record"):
            scenario.validate_dataset(data)

if __name__ == "__main__":
    unittest.main()
