#!/usr/bin/env python3
"""Example adapter scaffold for the MemoryAgentBench FactConsolidation 32K fixture.

This is a template for a separate run, not the harness that produced the
published Continuum live API results.
"""
from __future__ import annotations

import abc
import argparse
import asyncio
import json
import os
import re
import uuid
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
    if max_questions_per_subset is not None and not 1 <= max_questions_per_subset <= 100:
        raise ValueError("max_questions_per_subset must be between 1 and 100")
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

        # Parse and validate the official numbered source.  A loose ". " split
        # can silently drop/reorder facts and produce an inflated benchmark.
        facts: list[str] = []
        for line in context.splitlines():
            match = re.match(r"^\s*(\d+)\.\s+(.*\S)\s*$", line)
            if match:
                serial, fact = int(match.group(1)), match.group(2)
                if serial != len(facts):
                    raise ValueError(f"{subset}: expected serial {len(facts)}, found {serial}")
                facts.append(fact)
        if len(facts) != 2310:
            raise ValueError(f"{subset}: expected 2310 numbered facts, found {len(facts)}")
        if len(questions) != 100 or len(answers) != 100:
            raise ValueError(f"{subset}: expected 100 aligned questions and answers")

        session_id = f"eval_factcon_{subset}_{uuid.uuid4().hex[:12]}"
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
            try:
                prediction = await adapter.search_and_answer(session_id, question)
                prediction = "" if prediction is None else str(prediction)
                error = None
            except Exception as exc:
                # Keep the fixed denominator while making transport failures
                # visible to the caller and result artifact.
                prediction = ""
                error = f"{type(exc).__name__}: {exc}"
            results.append({
                "subset": subset,
                "index": q_idx,
                "question": question,
                "gold_answers": gold,
                "prediction": prediction,
                "error": error,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote predictions to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run FactConsolidation benchmark harness.")
    parser.add_argument("--dataset", type=Path, default=Path("fixtures/factconsolidation_official_32k.json"))
    parser.add_argument("--output", type=Path, default=Path("results/my_predictions.json"))
    parser.add_argument("--max-questions", type=int, default=None,
                        help="Optional smoke-test limit per subset; default runs all 100.")
    args = parser.parse_args()

    adapter = MockExampleAdapter()
    asyncio.run(run_benchmark(adapter, args.dataset, args.output, max_questions_per_subset=args.max_questions))


if __name__ == "__main__":
    main()
