import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fc_scorer", ROOT / "scripts" / "score_factconsolidation.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScoreIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gold = MODULE.load_locked_gold(ROOT / "fixtures" / "BENCHMARK_LOCK.json")
        cls.predictions = json.loads(
            (ROOT / "results" / "factconsolidation_predictions_full.json").read_text(encoding="utf-8")
        )

    def test_embedded_gold_is_ignored(self):
        altered = [dict(row, gold_answers=["fabricated answer"]) for row in self.predictions]
        self.assertEqual(MODULE.score_records(altered, self.gold), MODULE.score_records(self.predictions, self.gold))

    def test_missing_question_is_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.score_records(self.predictions[:-1], self.gold)

    def test_duplicate_question_is_rejected(self):
        duplicated = list(self.predictions)
        duplicated[-1] = dict(duplicated[0])
        with self.assertRaises(ValueError):
            MODULE.score_records(duplicated, self.gold)


if __name__ == "__main__":
    unittest.main()
