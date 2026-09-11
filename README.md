# 🧠 Syntarus Evals: Conflict Resolution & Memory Benchmark

> **Open, reproducible benchmark results for Continuum's memory engine.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Benchmark: MemoryAgentBench](https://img.shields.io/badge/Benchmark-MemoryAgentBench-green.svg)](https://github.com/HUST-AI-HYZ/MemoryAgentBench)
[![Dataset Checksum](https://img.shields.io/badge/SHA256-Verified-brightgreen.svg)](fixtures/BENCHMARK_LOCK.json)
[![Official Metric](https://img.shields.io/badge/Metric-SubEM%20Exact%20Match-orange.svg)](scripts/score_factconsolidation.py)

---

## ⚡ What is this test? (In Plain English)

Imagine you tell your AI assistant:
> *"I live in Seattle."*  

Three months later, you update it:
> *"I just moved to Austin."*  

Most AI memory systems today **fail at this simple task**. When you ask *"Where do I live?"*, they get confused, bring up Seattle again, or say *"You live in Seattle and Austin."*

The **FactConsolidation** benchmark (published in the peer-reviewed research suite [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench)) is the industry's toughest test for this exact problem. It feeds **455 rapidly changing facts** into an AI memory system, deliberately throwing in contradictions to see if the AI can:
1. **Forget outdated information** automatically.
2. **Remember the new, correct fact**.
3. **Connect facts across multiple steps** without hallucinating.

---

## 🏆 The Results

The following table reports the 6K FactConsolidation results using the official Normalized Substring Exact Match (SubEM) metric. The Continuum row is the run published in this repository; the other rows are the published MemoryAgentBench baselines.

| AI Memory System | Direct Lookups (Single-Hop) | Multi-Step Reasoning (Multi-Hop) | Overall Score | What This Means |
|:---|:---:|:---:|:---:|:---|
| **Continuum (this run)** | **34.0%** (34/100) | **8.0%** (8/100) | **21.0%** (42/200) | Continuum memory engine result |
| **HippoRAG-v2** | 54.0% | < 7.0% | < 30.5%* | Published MemoryAgentBench baseline |
| **BM25 (standard lexical search)** | 48.0% | < 7.0% | < 27.5%* | Published MemoryAgentBench baseline |
| **Mem0** | 18.0% | < 7.0% | < 12.5%* | Published MemoryAgentBench baseline |
| **Zep / Graphiti** | 7.0% | < 7.0% | < 7.0%* | Published MemoryAgentBench baseline |

\* Overall values for baseline rows are upper bounds derived from the published `< 7%` multi-hop figures; the source reports the two subset scores rather than an exact pooled total. Continuum used sequential ingestion, retrieval `k=40`, GLM 5.3 Flash at temperature 0, and the official 200-question split.

### Published baseline source

The comparison rows are taken from the [MemoryAgentBench FactConsolidation results and metric definitions](https://github.com/HUST-AI-HYZ/MemoryAgentBench). The complete Continuum predictions and the locked fixture are included in this repository for reproduction.

---

## 🚀 How to Run & Verify in 60 Seconds (No Coding Required)

You do **not** need any specialized programming environment. All you need is standard **Python** (which comes pre-installed on most computers).

### Step 1: Open your Terminal / Command Prompt
- **Windows**: Press `Win + R`, type `cmd`, and press Enter.
- **Mac / Linux**: Open the `Terminal` app.

### Step 2: Copy and Paste These Commands

```bash
# 1. Download this repository
git clone https://github.com/syntarus12/evals.git

# 2. Enter the directory
cd evals

# 3. Run the official automated verification
python scripts/score_factconsolidation.py
```

### What You Will See on Your Screen:

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

That's it! In under 5 seconds, the script checks the cryptographic checksum of the official dataset and recalculates the scores for all 200 questions.

---

## 🔍 Total Transparency: Inspect Any Question Yourself

Unlike benchmarks that only show high-level numbers, **every single question, prediction, and gold answer is open for public audit**:

👉 **[Click here to view all 200 questions & answers (factconsolidation_predictions_full.json)](results/factconsolidation_predictions_full.json)**

Each entry looks like this:
```json
{
  "subset": "factconsolidation_sh_6k",
  "index": 4,
  "question": "What is the educational institution where Joan Didion was educated?",
  "gold_answers": ["University of California, Berkeley", "UC Berkeley"],
  "prediction": "University of California, Berkeley",
  "correct": true
}
```

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>1. Was there any cheating or data leakage?</b></summary>

**None were intentionally introduced.** The run enforces strict data boundaries:
- The **correct answers were strictly hidden** from the memory system during ingestion and question answering.
- Gold answers were only accessed *after* the AI generated its answer to check if it got it right.
- Zero questions were discarded or skipped (`200 / 200` scored). Provider retries, if any, are disclosed by the runner.
</details>

<details>
<summary><b>2. What is the difference between Single-Hop and Multi-Hop?</b></summary>

- **Single-Hop (Direct Lookup)**: Asking about one direct fact that changed.  
  *Example*: *"Where was John born?"* (Fact 10 says London; Fact 80 says Leeds. The AI must answer Leeds).
- **Multi-Hop (Connecting the Dots)**: Asking a question that requires connecting two separate facts.  
  *Example*: *"What is the citizenship of the spouse of the author of Our Mutual Friend?"*  
  To solve this, the AI must first find the author (Charles Dickens), then find his spouse (Catherine Dickens), then find her citizenship.
</details>

<details>
<summary><b>3. How is the score calculated?</b></summary>

Scored using **Normalized Substring Exact Match (SubEM)**:
The computer strips punctuation and capital letters, and checks whether the official correct answer appears inside the AI's answer. No human bias, and no subjective "LLM-as-a-judge" grading.
</details>

<details>
<summary><b>4. Does this repository reveal proprietary engine code?</b></summary>

**No.** This repository contains only public test fixtures, sanitized predictions, and open client harnesses. Syntarus's internal database implementations, proprietary prompts, and infrastructure remain fully isolated.
</details>

---

## 📁 Repository Map

```text
├── fixtures/
│   ├── factconsolidation_official_6k.json   ← Official 455 facts & 200 questions
│   └── BENCHMARK_LOCK.json                  ← Official SHA256 checksum lock
├── results/
│   ├── factconsolidation_summary.json       ← Executive summary & competitor comparison
│   └── factconsolidation_predictions_full.json ← Full 200-question audit trail
├── scripts/
│   ├── score_factconsolidation.py           ← Standalone 1-click verification script
│   ├── harness_template.py                  ← Template to test any custom memory engine
│   └── verify_public_release.py             ← Security tool checking for zero leaked secrets
├── METHODOLOGY.md                           ← Full scientific specification & rules
└── README.md                                ← This guide
```

---

## 📄 License & Attribution

- Benchmark dataset and protocol copyright © 2025–2026 [MemoryAgentBench Team](https://github.com/HUST-AI-HYZ/MemoryAgentBench).
- Evaluation code and result data licensed under the [MIT License](LICENSE).
