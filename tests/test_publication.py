import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_result_artifacts import verify_publication


class PublicationTests(unittest.TestCase):
    def test_current_publication_matches(self):
        verify_publication(ROOT)

    def snapshot(self, root):
        for name in ("README.md", "results/factconsolidation_summary.json", "assets/factcon_32k_comparison.json"):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_old_headline_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.snapshot(root)
            file = root / "README.md"
            file.write_text(file.read_text(encoding="utf-8").replace("| 95 | 100 | **95%** |", "| 97 | 100 | **97%** |"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "README headline"):
                verify_publication(root)

    def test_wrong_chart_context_and_score_are_rejected(self):
        for field in ("context", "score"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.snapshot(root)
                file = root / "assets/factcon_32k_comparison.json"
                data = json.loads(file.read_text(encoding="utf-8"))
                if field == "context":
                    data["context"] = "262K"
                else:
                    data["baselines"][0]["sh"] = 60
                file.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Chart"):
                    verify_publication(root)


if __name__ == "__main__":
    unittest.main()
