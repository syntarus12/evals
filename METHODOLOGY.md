# FactConsolidation Evaluation Methodology

This document details the exact protocol, scoring rules, and constraints applied in the **MemoryAgentBench FactConsolidation** evaluation.

---

## 1. Task Definition

**FactConsolidation** measures how a memory system resolves factual conflicts and tracks canonical state across an ongoing stream of updates.

### Conflict Resolution Dynamics
- The memory system is presented with **455 numbered statements** (e.g., historical facts, entity associations, sports positions, birthplaces, citizenships).
- Several statements deliberately contradict earlier statements in the sequence:
  - *Statement A (earlier)*: Entity $X$ has attribute $Y_1$.
  - *Statement B (later)*: Entity $X$ has attribute $Y_2$.
- The governing rule of the benchmark: **newer facts supersede older facts**.
- The evaluation tests whether the memory engine retrieves the updated canonical value $Y_2$ or mistakenly returns the superseded value $Y_1$.

### Subsets
1. **Single-Hop (SH 6K)**: 100 questions requiring retrieval of a single entity attribute under direct conflict resolution.
2. **Multi-Hop (MH 6K)**: 100 questions requiring connecting two or more entities across different statements while respecting supersession along the relation chain.

---

## 2. Evaluation Protocol

1. **Dataset Pinning**:
   - Snapshot: `fixtures/factconsolidation_official_6k.json`
   - Revision: `7ea066982b140a19337e17e60d45d4076e042faf` from `ai-hyz/MemoryAgentBench`.
   - Verified against `fixtures/BENCHMARK_LOCK.json` with SHA256: `f2cdfb17cf56bcb3f5448a86f23a7931a72548bb8a8e1d3b307d0a62526e2d32`.

2. **Sequential Ingestion**:
   - Facts 0 through 454 are ingested sequentially in strict numerical order.
   - Batching or out-of-order reordering is prohibited.
   - Gold answers are completely withheld during ingestion and retrieval.

3. **Retrieval & Answering**:
   - For each of the 200 questions, the engine retrieves relevant context (fixed budget of 40 memories).
   - An answering LLM is prompted with:
     ```text
     You are a knowledge management system. Facts may conflict; newer facts supersede older facts.
     Answer using only the retrieved facts. Return exactly one concise line: ANSWER: <answer>.
     
     RETRIEVED FACTS:
     {facts}
     
     QUESTION: {question}
     ```
   - Temperature is set to `0` for deterministic reproducibility.

4. **Fail-Closed Denominator**:
   - All 200 questions are scored.
   - Any transport error, timeout, or missing prediction is treated as an explicit failure (`correct = False`).
   - No queries are dropped or re-sampled.

---

## 3. Official Scoring Function: Normalized Substring Exact Match (SubEM)

The official MemoryAgentBench scoring function is implemented in [`scripts/score_factconsolidation.py`](scripts/score_factconsolidation.py):

1. **Normalization**:
   - Convert text to lowercase.
   - Strip all ASCII punctuation without whitespace substitution (`string.punctuation`).
   - Remove English articles (`a`, `an`, `the`).
   - Normalize multi-whitespace sequences to a single space.

2. **Match Rule**:
   - A prediction is scored as **Correct (`1`)** if and only if any of the normalized gold answer variants appears as a substring within the normalized prediction.
   - Empty predictions or failures to extract are scored as **Incorrect (`0`)**.

---

## 4. Integrity and Fairness Controls

- **No Data Contamination**: Gold answers are strictly decoupled from the memory store and only consulted post-hoc during scoring.
- **Failures Included in Denominator**: The denominator is fixed at 200 (100 SH, 100 MH).
- **Zero Cherry-Picking**: The entire official test split was evaluated in a single continuous session.
- **Open Reproducibility**: Complete question-by-question prediction outputs and reference answers are provided in `results/factconsolidation_predictions_full.json`.
