import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_result_artifacts as verifier
from score_factconsolidation import load_locked_gold, score_records


class PublishedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gold = load_locked_gold(ROOT / "fixtures/BENCHMARK_LOCK.json")
        cls.rows = json.loads((ROOT / "results/factconsolidation_predictions_full.json").read_text(encoding="utf-8"))

    def test_every_published_result_recomputes(self):
        results = verifier.verify_all()
        self.assertEqual([(r["correct"], r["total"], r["failed_requests"]) for r in results],
                         [(152, 200, 0), (153, 200, 1), (140, 200, 0), (57, 100, 0), (34, 100, 1)])

    def test_failure_cannot_be_rescued_by_gold_answer(self):
        rows = copy.deepcopy(self.rows)
        row = next(row for row in rows if row["correct"])
        baseline = score_records(rows, self.gold)
        row["failure"] = "TimeoutError"
        recomputed = score_records(rows, self.gold)
        self.assertEqual(recomputed[row["subset"]]["correct"], baseline[row["subset"]]["correct"] - 1)

    def test_boolean_index_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["index"] = False
        with self.assertRaises(ValueError):
            score_records(rows, self.gold)

    def test_nontext_prediction_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["prediction"] = None
        with self.assertRaises(ValueError):
            score_records(rows, self.gold)

    def test_manifest_path_escape_is_rejected(self):
        with self.assertRaises(ValueError):
            verifier.public_path(ROOT, "../AGENTS.md")

    def test_current_fixture_has_canonical_lf_bytes(self):
        fixture = (ROOT / "fixtures/factconsolidation_official_32k.json").read_bytes()
        self.assertNotIn(b"\r\n", fixture)
        lock = json.loads((ROOT / "fixtures/BENCHMARK_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(fixture).hexdigest(), lock["dataset_sha256"])

    def test_latest_diagnostics_agree_with_prediction_scores(self):
        audit = json.loads((ROOT / "results/factconsolidation_mh_stage_audit.json").read_text(encoding="utf-8"))
        rows = {row["index"]: row for row in self.rows if "_mh_" in row["subset"]}
        self.assertEqual(set(rows), {case["index"] for case in audit["cases"]})
        self.assertEqual(sum(s["total"] for s in audit["counts_by_stage"].values()), 100)
        self.assertEqual(sum(s["correct"] for s in audit["counts_by_stage"].values()), 57)
        for case in audit["cases"]:
            self.assertEqual(case["scored_correct"], rows[case["index"]]["correct"])

    def test_summary_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = copy.deepcopy(self.rows)
            prediction_path = root / "predictions.json"
            prediction_path.write_text(json.dumps(rows), encoding="utf-8")
            summary = json.loads((ROOT / "results/factconsolidation_summary.json").read_text(encoding="utf-8"))
            summary["results"]["continuum"]["overall"]["correct"] += 1
            summary_path = root / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            entry = {"predictions": "predictions.json", "summary": "summary.json", "questions": 200,
                     "arm": "continuum", "label": "tampered",
                     "sha256": hashlib.sha256(prediction_path.read_bytes()).hexdigest(),
                     "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest()}
            questions = {(row["subset"], row["index"]): row["question"] for row in rows}
            with self.assertRaisesRegex(ValueError, "aggregate/failure"):
                verifier.verify_entry(root, entry, self.gold, questions)


if __name__ == "__main__":
    unittest.main()
