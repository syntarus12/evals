# Syntarus Continuum — FactConsolidation evaluation

This repository publishes an auditable **Continuum-only live production API run** on the official FactConsolidation 32K Single-Hop (SH) and Multi-Hop (MH) subsets from [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench).

## Latest run

| Subset | Correct | Questions | Accuracy |
|---|---:|---:|---:|
| Single-Hop (SH) | 98 | 100 | **98%** |
| Multi-Hop (MH) | 15 | 100 | **15%** |
| Overall | 113 | 200 | **56.5%** |

All 200 questions received a prediction; there were no failed API attempts. The result is notably mixed: Continuum performed strongly on direct lookups, while multi-hop reasoning remains a substantial weakness. The MH result should not be hidden behind the overall score.

**This is not an A/B test and does not establish superiority over another memory system.** Only Continuum was evaluated in this run; no search-only or competitor baseline ran alongside it. “32K” identifies the official dataset subset variant; it does not mean 32,000 facts were ingested. The official SH and MH examples share the same context, so the run ingested that context once: **2,310 ordered durable fact writes**, then evaluated both sets of 100 questions.

See [METHODOLOGY.md](METHODOLOGY.md) for the protocol, configuration, integrity checks, latency, and limitations.

## Inspect and reproduce the scoring

The public artifacts contain the locked official fixture, an aggregate summary, and all 200 sanitized question/prediction/gold-answer records. They do not contain API credentials, the temporary user namespace, provider event IDs, or raw state-card contents.

```bash
python scripts/score_factconsolidation.py
python -m unittest discover -s tests
python scripts/verify_public_release.py
```

The scorer loads gold answers only from the checksum-locked fixture; embedded gold fields in the prediction file are for review and are not trusted for scoring.

## Repository map

- fixtures/factconsolidation_official_32k.json — official benchmark snapshot used for this run.
- fixtures/BENCHMARK_LOCK.json — source revisions, SHA-256, subsets, and scoring contract.
- results/factconsolidation_summary.json — sanitized run metadata, scores, timings, and cleanup verification.
- results/factconsolidation_predictions_full.json — question-level audit data for all 200 questions.
- METHODOLOGY.md — complete live-run procedure and interpretation notes.
- scripts/score_factconsolidation.py — dependency-free SubEM scorer.
- scripts/harness_template.py — starting point for evaluating another system under a separately documented protocol.
- scripts/verify_public_release.py — checks common secret patterns and prohibited artifact paths.

## Dataset attribution

FactConsolidation is from [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench), dataset card [ai-hyz/MemoryAgentBench](https://huggingface.co/datasets/ai-hyz/MemoryAgentBench). Refer to the upstream project and dataset card for their terms and citation requirements. Repository code and authored result summaries are licensed under [MIT](LICENSE).
