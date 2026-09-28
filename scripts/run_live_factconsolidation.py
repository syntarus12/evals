#!/usr/bin/env python3
"""Fresh-namespace Continuum-only live harness for MemoryAgentBench FactConsolidation.

This performs ordered durable writes and public resolver calls. It is a live,
potentially paid test; it never deletes the supplied namespace.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import string
import time
import uuid
from typing import Any

DEFAULT_API_BASE = "https://ai.syntarus.com/syntarus-api/v1"
DEFAULT_SARVAM_BASE = "https://api.sarvam.ai/v2"
DEFAULT_BUILD = "10930cca71055a9a9e9cb83b45e25fe8a1903a63"
MEMORY_ACK = "I'll make sure to add the content into the memory."
FIXED_CURRENT_TIME = "2024-01-01 00:00:00"
OFFICIAL_PROMPT = (
    "Pretend you are a knowledge management system. Each fact in the knowledge pool is provided with a serial number at the beginning, and the newer fact has larger serial number. \n"
    " You need to solve the conflicts of facts in the knowledge pool by finding the newest fact with larger serial number. You need to answer a question based on this rule. You should give a very concise answer without saying other words for the question **only** from the knowledge pool you have memorized rather than the real facts in real world. \n\n"
    "For example:\n\n [Knowledge Pool] \n\n Question: Based on the provided Knowledge Pool, what is the name of the current president of Russia? \nAnswer: Donald Trump \n\n Now Answer the Question: Based on the provided Knowledge Pool, {question} \nAnswer:"
)
_ARTICLES = re.compile(r"\b(a|an|the)\b")


@dataclass(frozen=True)
class Case:
    subset: str
    context: str
    facts: tuple[str, ...]
    questions: tuple[str, ...]
    answers: tuple[tuple[str, ...], ...]


def normalize(text: str) -> str:
    text = "".join(ch for ch in text.lower() if ch not in string.punctuation)
    return " ".join(_ARTICLES.sub(" ", text).split())


def score_subem(prediction: str, answers: tuple[str, ...] | list[str]) -> bool:
    normalized = normalize(prediction)
    return bool(normalized) and any(
        normalize(answer) in normalized for answer in answers
    )


def parse_numbered_facts(context: str) -> tuple[str, ...]:
    facts: list[str] = []
    for line in context.splitlines():
        match = re.match(r"^\s*(\d+)\.\s+(.*\S)\s*$", line)
        if not match:
            continue
        serial, fact = int(match.group(1)), match.group(2)
        if serial != len(facts):
            raise ValueError(f"Expected fact serial {len(facts)}, found {serial}")
        facts.append(fact)
    if len(facts) != 2310:
        raise ValueError(f"Expected exactly 2310 ordered facts, found {len(facts)}")
    return tuple(facts)


def load_cases(dataset_path: Path, lock_path: Path) -> tuple[list[Case], str]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    dataset_bytes = dataset_path.read_bytes()
    actual_sha = hashlib.sha256(dataset_bytes).hexdigest()
    if actual_sha != lock.get("dataset_sha256"):
        raise ValueError(f"Fixture SHA-256 mismatch: expected {lock.get('dataset_sha256')}, got {actual_sha}")
    snapshot = json.loads(dataset_bytes)
    expected_subsets = set(lock.get("subsets") or [])
    cases: list[Case] = []
    for row in snapshot.get("data", []):
        subset = (row.get("metadata") or {}).get("source")
        questions, raw_answers = row.get("questions") or [], row.get("answers") or []
        if subset not in expected_subsets or len(questions) != 100 or len(raw_answers) != 100:
            raise ValueError(f"Unexpected or incomplete fixture subset: {subset}")
        answers = tuple(
            tuple(str(v) for v in value) if isinstance(value, list) else (str(value),)
            for value in raw_answers
        )
        context = str(row["context"])
        cases.append(Case(subset, context, parse_numbered_facts(context), tuple(questions), answers))
    if {case.subset for case in cases} != expected_subsets or len(cases) != 2:
        raise ValueError("Fixture must contain exactly the two locked SH/MH subsets")
    if cases[0].context != cases[1].context:
        raise ValueError("SH and MH contexts differ; refusing to ingest only one context")
    return cases, actual_sha


class PublicMemoryApi:
    def __init__(self, base_url: str, api_key: str, timeout: float):
        if not api_key.startswith(("sk_mem_", "st_mem_")):
            raise ValueError("SYNTARUS_API_KEY must be a Syntarus project key or subject token")
        import httpx

        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": "evals-factcon-live/1"},
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        safe_path = "/events/{event_id}" if path.startswith("/events/") else path
        try:
            response = await self.client.request(method, path, **kwargs)
        except Exception as exc:
            raise RuntimeError(f"{method} {safe_path} transport error ({type(exc).__name__})") from None
        if not response.is_success:
            raise RuntimeError(f"{method} {safe_path} returned HTTP {response.status_code}")
        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            raise RuntimeError(f"{method} {path} returned non-object JSON")
        return payload

    async def runtime(self) -> dict[str, Any]:
        root = self.base_url.split("/v1", 1)[0]
        return await self.request("GET", f"{root}/ready")

    async def ensure_empty(self, user_id: str) -> None:
        result = await self.resolve("empty namespace preflight", user_id)
        if result.get("results"):
            raise RuntimeError("The supplied namespace is not empty; use a fresh synthetic user ID.")

    async def ingest_fact(self, user_id: str, run_id: str, index: int, fact: str, timeout_s: float) -> None:
        accepted = await self.request(
            "POST", "/memories",
            headers={"Idempotency-Key": f"{run_id}-fact-{index}"},
            json={
                "user_id": user_id,
                "run_id": run_id,
                "event_time": None,
                "messages": [
                    {"role": "user", "content": f"{index}. {fact}"},
                    {"role": "assistant", "content": MEMORY_ACK},
                ],
                "ingestion_mode": "hybrid",
            },
        )
        event_id = accepted.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise RuntimeError("POST /memories returned no event ID")
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            event = await self.request("GET", f"/events/{event_id}")
            status = event.get("status")
            if status == "succeeded":
                result = event.get("result") or {}
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        result = {}
                readiness = result.get("readiness") if isinstance(result, dict) else None
                if isinstance(readiness, dict) and readiness.get("retrievable") is False:
                    raise RuntimeError("Durable event completed but the fact is not retrievable")
                return
            if status in {"dead_letter", "cancelled"}:
                raise RuntimeError(f"Durable ingestion event ended with status {status}")
            await asyncio.sleep(0.5)
        raise TimeoutError("Timed out waiting for a durable ingestion event")

    async def resolve(self, query: str, user_id: str) -> dict[str, Any]:
        payload = await self.request(
            "POST", "/memories/resolve",
            json={"user_id": user_id, "query": query, "top_k": 10, "max_claims": 8},
        )
        if not isinstance(payload.get("context"), str) or not isinstance(payload.get("resolution"), dict):
            raise RuntimeError("Resolver returned no state card")
        return payload


def make_sarvam_client(api_key: str, base_url: str):
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is required for a live evaluation")
    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key="unused",
        base_url=base_url,
        default_headers={"api-subscription-key": api_key},
        max_retries=0,
    )


async def preflight_model(client: Any, model_name: str) -> float:
    started = time.perf_counter()
    response = await client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        temperature=0,
        max_tokens=8,
        timeout=30,
        reasoning_effort="low",
        extra_body={"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}},
    )
    choice = (response.choices or [None])[0]
    content = (getattr(getattr(choice, "message", None), "content", None) or "").strip()
    if not content:
        raise RuntimeError("Sarvam preflight returned no visible text")
    return (time.perf_counter() - started) * 1000


async def answer_question(client: Any, model_name: str, question: str, state_card: str) -> tuple[str, float]:
    messages = [
        {"role": "system", "content": f"You are a helpful AI. Answer the question based on query and memories.\n{state_card}\n"},
        {"role": "user", "content": f"{OFFICIAL_PROMPT.format(question=question)}\n\nCurrent Time: {FIXED_CURRENT_TIME}"},
    ]
    started = time.perf_counter()
    response = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0,
        max_tokens=512,
        timeout=180,
        reasoning_effort="low",
        extra_body={"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}},
    )
    choice = (response.choices or [None])[0]
    content = (getattr(getattr(choice, "message", None), "content", None) or "").strip()
    if not content:
        raise RuntimeError("Sarvam returned no visible answer text")
    return content, (time.perf_counter() - started) * 1000


def percentile(values: list[float], p: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, (len(ordered) * p + 99) // 100 - 1))
    return round(ordered[index], 2)


def latency_summary(values: list[float]) -> dict[str, Any]:
    import statistics

    return {
        "count": len(values),
        "mean_ms": round(statistics.fmean(values), 2) if values else None,
        "p50_ms": percentile(values, 50),
        "p95_ms": percentile(values, 95),
        "p99_ms": percentile(values, 99),
        "max_ms": round(max(values), 2) if values else None,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


async def run(args: argparse.Namespace) -> None:
    api_key = os.environ.get("SYNTARUS_API_KEY", "")
    sarvam_key = os.environ.get("SARVAM_API_KEY", "")
    if not args.user_id.strip():
        raise ValueError("--user-id must be a fresh synthetic user ID")
    cases, fixture_sha = load_cases(args.dataset, args.lock)
    api = PublicMemoryApi(args.api_base_url, api_key, args.http_timeout)
    model = make_sarvam_client(sarvam_key, args.sarvam_base_url)
    run_id = f"factcon-{uuid.uuid4().hex}"
    started = time.monotonic()
    ingest_latencies: list[float] = []
    model_preflight_ms: float | None = None
    answer_latencies: list[float] = []
    resolver_latencies: list[float] = []
    question_latencies: list[float] = []
    records: list[dict[str, Any]] = []
    stage = "preflight"
    try:
        ready = await api.runtime()
        runtime = ready.get("runtime") or {}
        if runtime.get("build_sha") != args.expected_build:
            raise RuntimeError(f"Production build mismatch (expected {args.expected_build})")
        for component in ("qdrant", "neo4j", "redis", "platform_db", "platform_worker"):
            if ready.get(component) != "ok":
                raise RuntimeError(f"Production readiness check failed: {component}")
        if (ready.get("reranker") or {}).get("state") != "active":
            raise RuntimeError("Production reranker is not active")
        await api.ensure_empty(args.user_id)
        model_preflight_ms = await preflight_model(model, args.model)

        stage = "ingest"
        expected_facts = len(cases[0].facts)
        for index, fact in enumerate(cases[0].facts):
            before = time.perf_counter()
            await api.ingest_fact(args.user_id, run_id, index, fact, args.event_timeout)
            ingest_latencies.append((time.perf_counter() - before) * 1000)
            if (index + 1) % 50 == 0 or index + 1 == expected_facts:
                print(f"Durable facts: {index + 1}/{expected_facts}", flush=True)

        stage = "answer"
        cap = args.max_questions_per_subset or 100
        for case in cases:
            for index, question in enumerate(case.questions[:cap]):
                q_started = time.perf_counter()
                row: dict[str, Any] = {
                    "subset": case.subset,
                    "index": index,
                    "question": question,
                    "gold_answers": list(case.answers[index]),
                    "prediction": "",
                    "correct": False,
                }
                try:
                    resolved = await api.resolve(question, args.user_id)
                    resolver_ms = float(resolved.get("resolution_latency_ms") or 0)
                    row["answer_attempted"] = True
                    answer, answer_ms = await answer_question(model, args.model, question, resolved["context"])
                    row.update({
                        "prediction": answer,
                        "correct": score_subem(answer, case.answers[index]),
                        "retrieval_server_latency_ms": int(resolved.get("latency_ms") or 0),
                        "resolver_compute_ms": resolver_ms,
                        "server_total_ms": float(resolved.get("total_server_latency_ms") or 0),
                        "answer_attempt_ms": round(answer_ms, 2),
                    })
                    resolver_latencies.append(resolver_ms)
                    answer_latencies.append(answer_ms)
                except Exception as exc:
                    row["failure"] = type(exc).__name__
                row["question_end_to_end_ms"] = round((time.perf_counter() - q_started) * 1000, 2)
                question_latencies.append(row["question_end_to_end_ms"])
                records.append(row)
                print(f"{case.subset}: {index + 1}/{cap}", flush=True)

        expected_questions = 200 if cap == 100 else 2 * cap
        complete = len(records) == expected_questions
        full_benchmark = cap == 100 and len(records) == 200
        failures = sum(bool(row.get("failure")) for row in records)
        result_summary: dict[str, Any] = {}
        for case in cases:
            subset_rows = [row for row in records if row["subset"] == case.subset]
            result_summary[case.subset] = {
                "correct": sum(bool(row["correct"]) for row in subset_rows),
                "total": len(subset_rows),
                "accuracy": sum(bool(row["correct"]) for row in subset_rows) / len(subset_rows) if subset_rows else 0.0,
                "failed_requests": sum(bool(row.get("failure")) for row in subset_rows),
            }
        all_correct = sum(bool(row["correct"]) for row in records)
        out_summary = {
            "benchmark": "MemoryAgentBench FactConsolidation official 32K SH + MH",
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "complete" if complete else "partial",
            "full_benchmark": full_benchmark,
            "protocol_complete": full_benchmark and failures == 0 and len(ingest_latencies) == expected_facts,
            "certified": full_benchmark and failures == 0 and len(ingest_latencies) == expected_facts,
            "certification_semantics": "Harness completeness only; not an accuracy guarantee or vendor-neutral ranking.",
            "scope": "Continuum-only public Syntarus API",
            "production_build": runtime.get("build_sha"),
            "fixture_sha256": fixture_sha,
            "facts_expected": expected_facts,
            "facts_durably_ingested": len(ingest_latencies),
            "new_fact_write_retries": 0,
            "questions_expected": expected_questions,
            "questions_scored": len(records),
            "failed_question_requests": failures,
            "scored_answer_attempts": sum(bool(row.get("answer_attempted")) for row in records),
            "model_preflight_calls": 1,
            "model_preflight_latency_ms": round(model_preflight_ms, 2) if model_preflight_ms is not None else None,
            "total_model_calls_including_preflight": 1 + sum(bool(row.get("answer_attempted")) for row in records),
            "answer_retries": 0,
            "results": result_summary,
            "overall": {"correct": all_correct, "total": len(records), "accuracy": all_correct / len(records) if records else 0.0},
            "latency_ms": {
                "durable_ingest": latency_summary(ingest_latencies),
                "resolver_compute": latency_summary(resolver_latencies),
                "answer_attempt": latency_summary(answer_latencies),
                "question_end_to_end": latency_summary(question_latencies),
            },
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "privacy": "Output omits API keys, user ID, event IDs, raw state cards, and raw API responses.",
            "cleanup": "Not attempted; harness never deletes the supplied namespace.",
        }
        write_json(args.output, records)
        summary_path = args.output.with_name(args.output.stem + "_summary.json")
        write_json(summary_path, out_summary)
        print(json.dumps(out_summary, sort_keys=True), flush=True)
    finally:
        await api.close()
        await model.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("fixtures/factconsolidation_official_32k.json"))
    parser.add_argument("--lock", type=Path, default=Path("fixtures/BENCHMARK_LOCK.json"))
    parser.add_argument("--output", type=Path, default=Path("local_runs/factcon_predictions.json"))
    parser.add_argument("--user-id", required=True, help="Fresh synthetic namespace; never use a real customer ID.")
    parser.add_argument("--expected-build", default=DEFAULT_BUILD)
    parser.add_argument("--api-base-url", default=os.getenv("SYNTARUS_API_BASE_URL", DEFAULT_API_BASE))
    parser.add_argument("--sarvam-base-url", default=os.getenv("SARVAM_API_BASE_URL", DEFAULT_SARVAM_BASE))
    parser.add_argument("--model", default=os.getenv("SARVAM_MODEL", "glm5.3"))
    parser.add_argument("--http-timeout", type=float, default=30)
    parser.add_argument("--event-timeout", type=float, default=3600)
    parser.add_argument("--max-questions-per-subset", type=int, default=100,
                        help="Use 1-99 only for smoke runs; partial runs are not full-benchmark results.")
    args = parser.parse_args()
    if not 1 <= args.max_questions_per_subset <= 100:
        raise SystemExit("--max-questions-per-subset must be between 1 and 100")
    if args.output.exists() or args.output.with_name(args.output.stem + "_summary.json").exists():
        raise SystemExit("Output exists; choose a new --output path to avoid overwriting results.")
    try:
        asyncio.run(run(args))
    except Exception as exc:
        raise SystemExit(f"Live FactCon run stopped at {type(exc).__name__}: {exc}") from None


if __name__ == "__main__":
    main()
