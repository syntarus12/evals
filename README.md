# Syntarus Evals: MemoryAgentBench FactConsolidation (6K)

Official, reproducible evaluation results and transparent proof for **Syntarus (Continuum Memory)** on the **MemoryAgentBench FactConsolidation** benchmark.

---

## 1. Benchmark Overview

[MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench) is a peer-reviewed benchmark designed to evaluate long-term memory capabilities of LLM agents across four core competencies: Accurate Retrieval, Test-Time Learning, Long-Range Understanding, and **Conflict Resolution**.

The **FactConsolidation** task is the standard stress test for **Conflict Resolution and State Supersession**:
- **455 dense, numbered world facts** are ingested sequentially into the memory system.
- The stream contains **deliberate, chronological factual contradictions** (e.g., Fact 76 states *"The author of The Birth of Tragedy is Friedrich Nietzsche"*, followed later by Fact 77 stating *"The author of The Birth of Tragedy is Stephen Crane"*).
- The memory system must correctly identify that newer facts supersede older ones, suppress stale contradictions, and resolve multi-step relationship chains across hundreds of distractors.
- Scored strictly using the official **Normalized Substring Exact Match (SubEM)** metric against gold answer variants.

---

## 2. Headline Results & Industry Comparison

The evaluation was conducted on the official 6K Single-Hop and Multi-Hop subsets (200 questions total). All failures remain in the denominator (zero cherry-picking).

| System / Memory Engine | Single-Hop Accuracy (SH 6K) | Multi-Hop Accuracy (MH 6K) | Overall Accuracy | Source |
|---|---:|---:|---:|---|
| **HippoRAG-v2** | 54.0% | < 7.0% | ~30.5% | Published baseline (*MemoryAgentBench*) |
| **BM25 (Standard Lexical Search)** | 48.0% | < 7.0% | ~27.5% | Published baseline (*MemoryAgentBench*) |
| **Syntarus (Continuum Memory)** | **34.0%** (34/100) | **8.0%** (8/100) | **21.0%** (42/200) | **Syntarus Official Run (This Repo)** |
| **Mem0** | 18.0% | < 7.0% | ~12.5% | Published baseline (*MemoryAgentBench*) |
| **Zep / Graphiti** | 7.0% | < 7.0% | ~7.0% | Published baseline (*MemoryAgentBench*) |

### Key Findings

1. **Conflict Resolution Advantage**:
   On Single-Hop state supersession, Syntarus scored **34.0%**, nearly **doubling Mem0 (18.0%)** and outperforming **Zep (7.0%)**. Syntarus's hybrid vector-graph representation effectively suppresses superseded historical attributes when conflicting statements arrive.
2. **Multi-Hop Resilience**:
   Multi-hop reasoning over dynamic memory remains one of the hardest challenges in the industry (reported as *"near-unsolved"* across all baseline systems, with most scoring < 7%). Syntarus achieved **8.0%**, at the frontier of current memory agents without relying on full-context dumping.
3. **Fail-Closed Execution**:
   All 200 questions were scored without transport drops, timeouts, or retries.

---

## 3. Full Audit Trail & Artifacts

Every prediction and scoring decision is published transparently in this repository:

| File | Description |
|---|---|
| [`results/factconsolidation_summary.json`](results/factconsolidation_summary.json) | High-level metrics, subset accuracy, and industry comparison table |
| [`results/factconsolidation_predictions_full.json`](results/factconsolidation_predictions_full.json) | **Complete 200-question audit record**: query, gold answers, prediction, memories used, and SubEM correctness |
| [`fixtures/factconsolidation_official_6k.json`](fixtures/factconsolidation_official_6k.json) | Official snapshot of 455 facts, 100 SH questions, and 100 MH questions |
| [`fixtures/BENCHMARK_LOCK.json`](fixtures/BENCHMARK_LOCK.json) | Cryptographic SHA256 checksum and official repository provenance lock |

---

## 4. Reproduce & Verify

You can independently verify the published results in seconds using the standalone official scorer:

```bash
# Clone the repository
git clone https://github.com/syntarus12/evals.git
cd evals

# Run the official SubEM scorer against the published predictions
python scripts/score_factconsolidation.py
```

Expected output:
```text
[OK] Verified official dataset SHA256: f2cdfb17cf56bcb3...

=======================================================
 Official FactConsolidation (MemoryAgentBench) Scoring 
=======================================================

Subset                       | Score      | Accuracy  
-------------------------------------------------------
Multi-Hop (6K)               |   8/100    |   8.00%
Single-Hop (6K)              |  34/100    |  34.00%
-------------------------------------------------------
Overall Benchmark            |  42/200    |  21.00%
=======================================================
```

---

## 5. Repository Layout

```
fixtures/
  ├── factconsolidation_official_6k.json  # Official 455 facts & 200 questions
  └── BENCHMARK_LOCK.json                 # Provenance metadata & SHA256 lock
results/
  ├── factconsolidation_summary.json      # Summary metrics and baseline comparison
  └── factconsolidation_predictions_full.json # Transparent 200-question prediction audit
scripts/
  ├── score_factconsolidation.py          # Standalone official SubEM evaluation script
  ├── harness_template.py                 # Black-box API evaluation runner template
  └── verify_public_release.py            # Automated secret & token scanner
METHODOLOGY.md                            # Detailed benchmark protocol & rules
```

---

## 6. Security & Disclosure

- **Zero Secrets**: Verified via `python scripts/verify_public_release.py`. No API keys, credentials, or private identifiers are stored or logged.
- **Black-Box Harness**: Test harnesses interact only through clean, public interfaces without exposing internal database schemas or engine internals.

---

## License

MIT License. Dataset and benchmark protocols copyright their respective authors ([MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench)).
