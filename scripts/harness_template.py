#!/usr/bin/env python3
"""Vendor-Neutral Black-Box Evaluation Harness for MemoryAgentBench FactConsolidation.

This script demonstrates how any memory system can be evaluated against the
FactConsolidation benchmark without exposing internal engine implementation details.
"""
from __future__ import annotations

import abc
import argparse
import asyncio
import json
import os
from pathlib import Path


class MemoryEngineAdapter(abc.ABC):
    """Abstract interface that any memory engine or HTTP API client implements."""

    @abc.abstractmethod
    async def reset_session(self, session_id: str) -> None:
        """Reset or clear memory for this isolated test session."""
        pass

    @abc.abstractmethod
    async def ingest_fact(self, session_id: str, fact: str, fact_index: int) -> None:
        """Ingest a single fact sequentially."""
        pass

    @abc.abstractmethod
    async def search_and_answer(self, session_id: str, question: str) -> str:
        """Retrieve relevant memory and produce the final answer string."""
        pass


class MockExampleAdapter(MemoryEngineAdapter):
    """Example dummy adapter for testing harness connectivity."""

    async def reset_session(self, session_id: str) -> None:
        pass

    async def ingest_fact(self, session_id: str, fact: str, fact_index: int) -> None:
        pass

    async def search_and_answer(self, session_id: str, question: str) -> str:
        return "Unknown"


async def run_benchmark(
    adapter: MemoryEngineAdapter,
    dataset_path: Path,
    output_path: Path,
    max_questions_per_subset: int | None = None,
) -> None:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))

    results = []
    for row in data["data"]:
        subset = (row.get("metadata") or {}).get("source", "unknown")
        context = row["context"]
        questions = row["questions"]
        answers = [
            [str(v) for v in a] if isinstance(a, list) else [str(a)]
            for a in row["answers"]
        ]

        # Parse numbered facts: "0. Fact...", "1. Fact..."
        facts = [line.split(". ", 1)[-1].strip() for line in context.strip().split("\n") if ". " in line]

        session_id = f"eval_factcon_{subset}"
        print(f"\n--- Running subset: {subset} ({len(facts)} facts, {len(questions)} questions) ---")

        await adapter.reset_session(session_id)

        print(f"Ingesting {len(facts)} facts sequentially...")
        for idx, fact in enumerate(facts):
            await adapter.ingest_fact(session_id, fact, idx)

        limit = max_questions_per_subset or len(questions)
        print(f"Evaluating {limit} questions...")
        for q_idx in range(limit):
            question = questions[q_idx]
            gold = answers[q_idx]
            prediction = await adapter.search_and_answer(session_id, question)
            results.append({
                "subset": subset,
                "index": q_idx,
                "question": question,
                "gold_answers": gold,
                "prediction": prediction,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote predictions to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run FactConsolidation benchmark harness.")
    parser.add_argument("--dataset", type=Path, default=Path("fixtures/factconsolidation_official_6k.json"))
    parser.add_argument("--output", type=Path, default=Path("results/my_predictions.json"))
    args = parser.parse_args()

    adapter = MockExampleAdapter()
    asyncio.run(run_benchmark(adapter, args.dataset, args.output, max_questions_per_subset=5))


if __name__ == "__main__":
    main()
