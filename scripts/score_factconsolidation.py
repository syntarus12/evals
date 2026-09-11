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
        return
    actual_sha256 = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Dataset SHA256 mismatch!\nExpected: {expected_sha256}\nActual:   {actual_sha256}"
        )
    print(f"[OK] Verified official dataset SHA256: {actual_sha256[:16]}...")


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

    if args.lock.exists():
        try:
            lock_data = json.loads(args.lock.read_text(encoding="utf-8"))
            dataset_file = args.lock.parent / lock_data.get("dataset_file", "factconsolidation_official_6k.json")
            if dataset_file.exists():
                verify_dataset_sha256(dataset_file, lock_data.get("dataset_sha256"))
        except Exception as e:
            print(f"[WARN] Benchmark lock check skipped: {e}")

    records = json.loads(args.predictions.read_text(encoding="utf-8"))

    subsets: dict[str, dict] = {}
    for entry in records:
        subset = entry.get("subset", "unknown")
        if subset not in subsets:
            subsets[subset] = {"total": 0, "correct": 0}
        subsets[subset]["total"] += 1

        pred = entry.get("prediction", "")
        gold = entry.get("gold_answers", [])
        is_correct = score_subem(pred, gold)
        if is_correct:
            subsets[subset]["correct"] += 1

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
