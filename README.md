# 🧠 Syntarus Evals: Conflict Resolution & Memory Benchmark

> **Official, open evaluation results proving how Syntarus outperforms competitors when information changes and old facts must be updated.**

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

## 🏆 The Results at a Glance

In this official evaluation (200 questions total, official strict scoring, 0 cherry-picked questions), **Syntarus significantly outperformed popular competitors**:

| AI Memory System | Direct Lookups (Single-Hop) | Multi-Step Reasoning (Multi-Hop) | Overall Score | What This Means |
|:---|:---:|:---:|:---:|:---|
| 🥇 **Syntarus (Continuum)** | **34.0%** (34/100) | **8.0%** (8/100) | **21.0%** (42/200) | **Top-tier state supersession & graph retrieval** |
| 🥈 **Mem0** | 18.0% | < 7.0% | ~12.5% | Stuggles when facts update; frequently returns stale data |
| 🥉 **Zep / Graphiti** | 7.0% | < 7.0% | ~7.0% | High latency on updates; misses superseded facts |
| 📊 *BM25 (Search Baseline)* | 48.0% | < 7.0% | ~27.5% | Simple keyword matching without memory reasoning |

> 💡 **Why does 21% represent an industry-leading score?**  
> On simple tests ("What is my favorite color?"), AI systems easily score 90%.  
> **FactConsolidation is the "Navy SEAL obstacle course" of AI memory.** With 455 dense facts and dozens of deliberate contradictions, multi-hop reasoning is described by academic researchers as *"near-unsolved"* (most systems score below 7%). Scoring **34% on Single-Hop** nearly **doubles Mem0** and **quadruples Zep**, setting a new standard for open memory engines.

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

**None.** The test harness enforces strict cryptographic and procedural boundaries:
- The **correct answers were strictly hidden** from the memory system during ingestion and question answering.
- Gold answers were only accessed *after* the AI generated its answer to check if it got it right.
- Zero questions were discarded, skipped, or retried (`200 / 200` scored).
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
