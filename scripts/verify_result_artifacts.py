"""Independently rescore every published result and check summaries and hashes.

Offline and dependency-free. No credentials, network requests, or engine imports.
Verification establishes artifact consistency, not independent execution attestation.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from score_factconsolidation import load_locked_gold, score_records, score_subem

ROOT = Path(__file__).resolve().parents[1]
PREDICTION_KEYS = {
    "subset", "index", "question", "prediction", "correct", "failure", "gold_answers",
    "answer_attempts", "answer_latency_ms", "resolver_latency_ms", "retrieval_server_latency_ms",
    "server_latency_ms", "client_latency_ms", "question_end_to_end_ms", "finish_reason", "max_output_tokens",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def public_path(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Manifest path must name a file inside this repository")
    return path


def verify_entry(root, entry, gold, questions):
    path = public_path(root, entry["predictions"])
    summary_path = public_path(root, entry["summary"])
    for file, expected in ((path, entry["sha256"]), (summary_path, entry["summary_sha256"])):
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Result SHA-256 mismatch: {file.name}")
    selected_gold = gold if entry["questions"] == 200 else {
        key: value for key, value in gold.items() if key[0] == "factconsolidation_mh_32k"
    }
    if entry["questions"] not in (100, 200):
        raise ValueError("Unexpected result denominator")
    rows = load(path)
    scores = score_records(rows, selected_gold)
    for row in rows:
        key = (row["subset"], row["index"])
        if set(row) - PREDICTION_KEYS:
            raise ValueError("Prediction contains a non-public field")
        if row.get("question") != questions[key] or row.get("gold_answers") != list(gold[key]):
            raise ValueError("Published question/gold display differs from locked fixture")
        correct = not row.get("failure") and score_subem(row["prediction"], gold[key])
        if type(row.get("correct")) is not bool or row["correct"] != correct:
            raise ValueError("Published correctness flag disagrees with locked-gold rescore")
    computed = {"correct": sum(stats["correct"] for stats in scores.values()),
                "total": len(rows), "failed_requests": sum(bool(row.get("failure")) for row in rows)}
    summary = load(summary_path)
    result = summary["results"][entry["arm"]]
    if "overall" in result:
        aggregate = result["overall"]
        for label, subset in (("single_hop", "factconsolidation_sh_32k"),
                              ("multi_hop", "factconsolidation_mh_32k")):
            if result[label]["correct"] != scores[subset]["correct"] or result[label]["total"] != scores[subset]["total"]:
                raise ValueError("Published subset summary disagrees with rescore")
            if result[label]["accuracy"] != scores[subset]["correct"] / scores[subset]["total"]:
                raise ValueError("Published subset percentage disagrees with rescore")
    else:
        aggregate = result
    if any(aggregate[name] != count for name, count in computed.items()):
        raise ValueError("Published aggregate/failure summary disagrees with rescore")
    if aggregate["accuracy"] != computed["correct"] / computed["total"]:
        raise ValueError("Published aggregate percentage disagrees with rescore")
    return {"label": entry["label"], **computed}


def verify_publication(root=ROOT):
    """Prevent the current README and chart configuration drifting from the result."""
    result = load(root / "results/factconsolidation_summary.json")["results"]["continuum"]
    readme = (root / "README.md").read_text(encoding="utf-8")
    headline = readme.split("## Latest verified full replication", 1)[1].split("###", 1)[0]
    for label, key in (("Single-Hop (SH)", "single_hop"), ("Multi-Hop (MH)", "multi_hop"), ("Overall", "overall")):
        matches = re.findall(r"^\| " + re.escape(label) + r" \| (\d+) \| (\d+) \| \*\*([\d.]+)%\*\* \|$", headline, re.M)
        stats = result[key]
        expected = (str(stats["correct"]), str(stats["total"]), f"{stats['accuracy'] * 100:g}")
        if matches != [expected]:
            raise ValueError("Current README headline disagrees with verified scores")
    chart = load(root / "assets/factcon_32k_comparison.json")
    if chart["context"] != "32K" or chart["continuum_summary"] != "results/factconsolidation_summary.json":
        raise ValueError("Chart must use 32K and the verified replication summary")
    expected = [("GPT-4o", 88, 10, 10), ("o4-mini", 61, 14, 5), ("GPT-4o-mini", 63, 10, 10),
                ("GPT-4.1-mini", 82, 7, 10), ("Gemini-2.0-Flash", 49, 7, 10),
                ("Claude-3.7-Sonnet", 46, 2, 10), ("Mem0 (paper setup)", 22, 3, 10),
                ("Cognee (paper setup)", 39, 4, 10)]
    actual = [(r["name"], r["sh"], r["mh"], r["table"]) for r in chart["baselines"]]
    if actual != expected or chart["paper"] != "https://arxiv.org/html/2507.05257v3":
        raise ValueError("Chart references disagree with the checked 32K paper values")


def verify_all(root=ROOT):
    lock_path = root / "fixtures/BENCHMARK_LOCK.json"
    gold = load_locked_gold(lock_path)
    lock = load(lock_path)
    fixture = load(lock_path.parent / lock["dataset_file"])
    questions = {(record["metadata"]["source"], index): question
                 for record in fixture["data"] for index, question in enumerate(record["questions"])}
    manifest = load(root / "results/RESULTS_MANIFEST.json")
    if manifest.get("schema") != "verified-results-v1":
        raise ValueError("Unknown results manifest schema")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != 5:
        raise ValueError("Manifest must cover the five published result sets")
    if len({entry["predictions"] for entry in entries}) != len(entries):
        raise ValueError("Duplicate manifest result file")
    results = [verify_entry(root, entry, gold, questions) for entry in entries]
    verify_publication(root)
    return results


if __name__ == "__main__":
    for result in verify_all():
        print(f"[OK] {result['label']}: {result['correct']}/{result['total']}; "
              f"failed questions={result['failed_requests']}")
