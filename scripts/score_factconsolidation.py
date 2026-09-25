#!/usr/bin/env python3
"""Standalone SubEM scorer for the locked MemoryAgentBench FactConsolidation fixture."""
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
    """Apply official normalization: lowercase, strip ASCII punctuation,
    remove articles, then collapse whitespace.
    """
    without_punc = "".join(ch for ch in text.lower() if ch not in string.punctuation)
    return " ".join(_ARTICLES.sub(" ", without_punc).split())


def score_subem(prediction: str, gold_variants: list[str] | tuple[str, ...]) -> bool:
    """True when a normalized gold variant is a substring of the prediction."""
    norm_pred = normalise(prediction)
    return bool(norm_pred) and any(normalise(answer) in norm_pred for answer in gold_variants)


def verify_dataset_sha256(dataset_path: Path, expected_sha256: str | None) -> None:
    if not expected_sha256:
        raise ValueError("benchmark lock has no required dataset SHA256")
    actual_sha256 = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Dataset SHA256 mismatch!\nExpected: {expected_sha256}\nActual:   {actual_sha256}"
        )
    print(f"[OK] Verified official dataset SHA256: {actual_sha256[:16]}...")


def load_locked_gold(lock_path: Path) -> dict[tuple[str, int], tuple[str, ...]]:
    """Load scoring truth only from the checksum-locked fixture."""
    if not lock_path.exists():
        raise ValueError(f"required benchmark lock not found: {lock_path}")
    lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    dataset_file = lock_path.parent / lock_data.get("dataset_file", "")
    if not dataset_file.exists():
        raise ValueError(f"locked dataset not found: {dataset_file}")
    verify_dataset_sha256(dataset_file, lock_data.get("dataset_sha256"))

    dataset = json.loads(dataset_file.read_text(encoding="utf-8"))
    expected_subsets = tuple(lock_data.get("subsets") or ())
    if len(expected_subsets) != 2 or len(set(expected_subsets)) != 2:
        raise ValueError("benchmark lock must name exactly two distinct FactConsolidation subsets")

    gold: dict[tuple[str, int], tuple[str, ...]] = {}
    for row in dataset.get("data", []):
        subset = (row.get("metadata") or {}).get("source")
        if subset not in expected_subsets:
            raise ValueError(f"unexpected or missing subset in locked dataset: {subset!r}")
        questions, answers = row.get("questions", []), row.get("answers", [])
        expected_per_subset = int(lock_data.get("questions_per_subset", 100))
        if len(questions) != expected_per_subset or len(answers) != expected_per_subset:
            raise ValueError(f"locked subset {subset} must contain exactly {expected_per_subset} aligned questions")
        for index, answer in enumerate(answers):
            variants = tuple(str(value) for value in answer) if isinstance(answer, list) else (str(answer),)
            gold[(subset, index)] = variants

    expected_questions = int(lock_data.get("expected_questions", 200))
    if len(gold) != expected_questions:
        raise ValueError(f"locked dataset must contain exactly {expected_questions} questions, found {len(gold)}")
    found_subsets = {subset for subset, _ in gold}
    if found_subsets != set(expected_subsets):
        raise ValueError("locked dataset does not contain every subset named in the lock")
    return gold


def score_records(
    records: object,
    locked_gold: dict[tuple[str, int], tuple[str, ...]],
) -> dict[str, dict[str, int]]:
    """Validate a complete, duplicate-free prediction set and return counts."""
    if not isinstance(records, list):
        raise ValueError("predictions must be a JSON list")
    if len(records) != len(locked_gold):
        raise ValueError(f"predictions must contain exactly {len(locked_gold)} questions, found {len(records)}")

    subsets: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, int]] = set()
    for entry in records:
        if not isinstance(entry, dict):
            raise ValueError("each prediction record must be an object")
        subset, index = entry.get("subset", "unknown"), entry.get("index")
        if not isinstance(index, int) or (subset, index) not in locked_gold:
            raise ValueError(f"prediction has unknown subset/index: {subset!r}/{index!r}")
        key = (subset, index)
        if key in seen:
            raise ValueError(f"duplicate prediction record: {subset}/{index}")
        seen.add(key)
        stats = subsets.setdefault(subset, {"total": 0, "correct": 0})
        stats["total"] += 1
        # Embedded gold_answers are informational only and never used for scoring.
        if score_subem(str(entry.get("prediction", "")), locked_gold[key]):
            stats["correct"] += 1

    if seen != set(locked_gold):
        raise ValueError("prediction records do not cover every locked question")
    return subsets


def main() -> None:
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
        help="Path to benchmark lock JSON file",
    )
    args = parser.parse_args()

    if not args.predictions.exists():
        print(f"Error: predictions file not found: {args.predictions}", file=sys.stderr)
        raise SystemExit(1)

    locked_gold = load_locked_gold(args.lock)
    records = json.loads(args.predictions.read_text(encoding="utf-8"))
    subsets = score_records(records, locked_gold)

    print("\n=======================================================")
    print(" Official FactConsolidation (MemoryAgentBench) Scoring ")
    print("=======================================================\n")
    print(f"{'Subset':<32} | {'Score':<10} | {'Accuracy':<10}")
    print("-" * 60)

    total_questions = total_correct = 0
    for subset, stats in sorted(subsets.items()):
        total_questions += stats["total"]
        total_correct += stats["correct"]
        accuracy = 100 * stats["correct"] / stats["total"] if stats["total"] else 0.0
        if "_sh_" in subset.lower():
            label = "Single-Hop (SH)"
        elif "_mh_" in subset.lower():
            label = "Multi-Hop (MH)"
        else:
            label = subset
        print(f"{label:<32} | {stats['correct']:>3}/{stats['total']:<5}  | {accuracy:>6.2f}%")

    accuracy = 100 * total_correct / total_questions if total_questions else 0.0
    print("-" * 60)
    print(f"{'Overall Benchmark':<32} | {total_correct:>3}/{total_questions:<5}  | {accuracy:>6.2f}%")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
