import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


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


class AnswerCompletenessTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def client(content, finish_reason):
        async def create(**kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content=content), finish_reason=finish_reason
            )])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    async def test_truncated_visible_answer_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete or truncated"):
            await MODULE.answer_question(self.client("Taipei", "length"), "glm5.3", "Question", "Evidence")

    async def test_missing_visible_answer_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "no visible"):
            await MODULE.answer_question(self.client("", "stop"), "glm5.3", "Question", "Evidence")

    async def test_complete_answer_is_accepted(self):
        answer, elapsed = await MODULE.answer_question(self.client("Taipei", "stop"), "glm5.3", "Question", "Evidence")
        self.assertEqual(answer, "Taipei")
        self.assertGreaterEqual(elapsed, 0)


if __name__ == "__main__":
    unittest.main()
