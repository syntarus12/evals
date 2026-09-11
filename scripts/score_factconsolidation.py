#!/usr/bin/env python3
"""Official SubEM Scorer for MemoryAgentBench FactConsolidation.

Evaluates predictions using normalized substring-exact-match against
gold answer variants. Completely standalone with zero external dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import string
import sys
from pathlib import Path

_ARTICLES = re.compile(r"\b(a|an|the)\b")


def normalise(text: str) -> str:
    """Exact official MemoryAgentBench normalization:
    Strip ASCII punctuation (without space replacement), then articles, then normalize whitespace.
    """
    without_punc = "".join(ch for ch in text.lower() if ch not in string.punctuation)
    return " ".join(_ARTICLES.sub(" ", without_punc).split())


def score_subem(prediction: str, gold_variants: list[str]) -> bool:
    """Official SubEM: True if normalized prediction contains any normalized gold answer."""
    norm_pred = normalise(prediction)
    if not norm_pred:
        return False
    return any(normalise(ans) in norm_pred for ans in gold_variants)


def verify_dataset_sha256(dataset_path: Path, expected_sha256: str | None) -> None:
    if not expected_sha256:
        raise ValueError("Benchmark lock has no required dataset SHA256")
    actual_sha256 = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Dataset SHA256 mismatch!\nExpected: {expected_sha256}\nActual:   {actual_sha256}"
        )
    print(f"[OK] Verified official dataset SHA256: {actual_sha256[:16]}...")


def load_locked_gold(lock_path: Path) -> dict[tuple[str, int], tuple[str, ...]]:
    """Load gold only from the locked fixture, never from predictions.

    The predictions artifact may include gold answers for human audit, but the
    scorer deliberately ignores that field.  This prevents a modified result
    file from changing the denominator or manufacturing a passing score.
    """
    if not lock_path.exists():
        raise ValueError(f"required benchmark lock not found: {lock_path}")
    lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    dataset_file = lock_path.parent / lock_data.get("dataset_file", "")
    if not dataset_file.exists():
        raise ValueError(f"locked dataset not found: {dataset_file}")
    verify_dataset_sha256(dataset_file, lock_data.get("dataset_sha256"))
    dataset = json.loads(dataset_file.read_text(encoding="utf-8"))
    expected_subsets = tuple(lock_data.get("subsets") or ())
    if set(expected_subsets) != {"factconsolidation_sh_6k", "factconsolidation_mh_6k"}:
        raise ValueError("benchmark lock must name exactly the two FactConsolidation 6K subsets")
    gold: dict[tuple[str, int], tuple[str, ...]] = {}
    for row in dataset.get("data", []):
        subset = (row.get("metadata") or {}).get("source")
        if subset not in expected_subsets:
            raise ValueError(f"unexpected or missing subset in locked dataset: {subset!r}")
        if len(row.get("questions", [])) != 100 or len(row.get("answers", [])) != 100:
            raise ValueError(f"locked subset {subset} must contain exactly 100 aligned questions")
        for index, (question, answer) in enumerate(zip(row["questions"], row["answers"])):
            variants = tuple(str(value) for value in answer) if isinstance(answer, list) else (str(answer),)
            gold[(subset, index)] = variants
    if len(gold) != 200:
        raise ValueError(f"locked dataset must contain exactly 200 questions, found {len(gold)}")
    return gold


def score_records(
    records: object,
    locked_gold: dict[tuple[str, int], tuple[str, ...]],
) -> dict[str, dict[str, int]]:
    """Validate a complete prediction set and return per-subset counts."""
    if not isinstance(records, list):
        raise ValueError("predictions must be a JSON list")
    if len(records) != len(locked_gold):
        raise ValueError(f"predictions must contain exactly {len(locked_gold)} questions, found {len(records)}")
    subsets: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, int]] = set()
    for entry in records:
        if not isinstance(entry, dict):
            raise ValueError("each prediction record must be an object")
        subset = entry.get("subset", "unknown")
        index = entry.get("index")
        if not isinstance(index, int) or (subset, index) not in locked_gold:
            raise ValueError(f"prediction has unknown subset/index: {subset!r}/{index!r}")
        key = (subset, index)
        if key in seen:
            raise ValueError(f"duplicate prediction record: {subset}/{index}")
        seen.add(key)
        stats = subsets.setdefault(subset, {"total": 0, "correct": 0})
        stats["total"] += 1
        # Do not trust entry["gold_answers"]. It is informational only.
        if score_subem(str(entry.get("prediction", "")), locked_gold[key]):
            stats["correct"] += 1
    if seen != set(locked_gold):
        raise ValueError("prediction records do not cover every locked question")
    return subsets


def main():
    parser = argparse.ArgumentParser(description="Score FactConsolidation predictions with official SubEM.")
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("results/factconsolidation_predictions_full.json"),
        help="Path to predictions JSON file",
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("fixtures/BENCHMARK_LOCK.json"),
        help="Path to benchmark lock JSON file (optional)",
    )
    args = parser.parse_args()

    if not args.predictions.exists():
        print(f"Error: predictions file not found: {args.predictions}", file=sys.stderr)
        sys.exit(1)

    locked_gold = load_locked_gold(args.lock)

    records = json.loads(args.predictions.read_text(encoding="utf-8"))
    subsets = score_records(records, locked_gold)

    print("\n=======================================================")
    print(" Official FactConsolidation (MemoryAgentBench) Scoring ")
    print("=======================================================\n")
    print(f"{'Subset':<28} | {'Score':<10} | {'Accuracy':<10}")
    print("-" * 55)

    total_q = 0
    total_c = 0
    for subset, stats in sorted(subsets.items()):
        total_q += stats["total"]
        total_c += stats["correct"]
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0.0
        label = "Single-Hop (6K)" if "sh" in subset else "Multi-Hop (6K)" if "mh" in subset else subset
        print(f"{label:<28} | {stats['correct']:>3}/{stats['total']:<5}  | {acc:>6.2f}%")

    print("-" * 55)
    overall_acc = (total_c / total_q) * 100 if total_q else 0.0
    print(f"{'Overall Benchmark':<28} | {total_c:>3}/{total_q:<5}  | {overall_acc:>6.2f}%")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
