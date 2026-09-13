import copy
import importlib.util
import unittest
import tempfile
import shutil
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
        self.assertNotIn("$800", str(recommender))
        self.assertNotIn("espresso-buyer-1", str(recommender))
        self.assertEqual(recommender["public_context"], (scenario.ROOT / "public_context.md").read_text())
        self.assertEqual(buyer["private_user_preferences"], (scenario.ROOT / "private/user_preferences.md").read_text())
        self.assertIn("$800", buyer["private_user_preferences"])

    def test_changed_preference_brief_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "scenario"
            shutil.copytree(scenario.ROOT, root)
            brief = root / "private/user_preferences.md"
            brief.write_text(brief.read_text().replace("$800", "$900"))
            with self.assertRaisesRegex(ValueError, "File checksum mismatch"):
                scenario.validate(root)

    def test_revised_actor_views_and_inherited_records(self):
        self.assertEqual([r['records'] for r in scenario.validate_version('1.2.0')], [279, 186])
        public = scenario.load_context('recommender', version='1.2.0')
        self.assertEqual(public, scenario.load_context('recommender'))
        self.assertNotIn('$800', str(public))
        private = scenario.load_context('buyer', version='1.2.0')['private_user_preferences']
        self.assertIn('greatest expected satisfaction', private)
        self.assertIn('$800', private)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'scenario'
            shutil.copytree(scenario.ROOT, root)
            brief = root / 'versions/1.2.0/private/user_preferences.md'
            brief.write_text(brief.read_text().replace('$800', '$900'))
            with self.assertRaisesRegex(ValueError, 'Version file checksum mismatch'):
                scenario.validate_version('1.2.0', root)

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
