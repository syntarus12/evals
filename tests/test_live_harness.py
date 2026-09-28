import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "live_factcon", ROOT / "scripts" / "run_live_factconsolidation.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LiveHarnessTests(unittest.TestCase):
    def test_ordered_fact_parser_rejects_gaps(self):
        with self.assertRaises(ValueError):
            MODULE.parse_numbered_facts("1. first\n3. third")

    def test_subem_normalization_matches_public_scorer(self):
        self.assertTrue(MODULE.score_subem("The City of Taipei.", ["Taipei"]))
        self.assertTrue(MODULE.score_subem("Taipei City", ["Taipei City."]))
        self.assertFalse(MODULE.score_subem("Taipei", ["Taipei City."]))

    def test_locked_fixture_has_full_shared_context(self):
        cases, digest = MODULE.load_cases(
            ROOT / "fixtures" / "factconsolidation_official_32k.json",
            ROOT / "fixtures" / "BENCHMARK_LOCK.json",
        )
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0].context, cases[1].context)
        self.assertEqual(len(cases[0].facts), 2310)
        self.assertEqual(len(cases[0].questions), 100)
        self.assertEqual(len(cases[1].questions), 100)
        self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
