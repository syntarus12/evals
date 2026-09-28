# Syntarus Continuum — FactConsolidation evaluation

This repository publishes an auditable Continuum-only live production API evaluation on the official FactConsolidation 32K Single-Hop (SH) and Multi-Hop (MH) subsets from [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench).

## Latest run

| Subset | Correct | Questions | Accuracy |
|---|---:|---:|---:|
| Single-Hop (SH) | 97 | 100 | **97%** |
| Multi-Hop (MH) | 43 | 100 | **43%** |
| Overall | 140 | 200 | **70%** |

All 200 questions were scored; the run recorded no failed question requests and one scored answer attempt per question, plus a separate non-scored model connectivity preflight. This is a substantial multi-hop improvement over the previously published run, while single-hop remained strong.

**Important scope:** this was a Continuum-only replay through the public Syntarus API, not an A/B test or vendor-neutral leaderboard result. The prior published run scored 113/200 (56.5%; 98 SH, 15 MH). That comparison spans different production builds and run/namespace conditions; it is not a controlled ablation, so the score change cannot be attributed to one code change.

The replay used a retained namespace previously loaded with the official 2,310-fact stream. It did not re-ingest or delete facts during this scoring run, and the full corpus was not independently inventoried during replay. The run completed in 581.3 seconds for the 200 question/answer pass; this excludes the earlier corpus ingestion. End-to-end latency was mean 2,159 ms, p50 1,724 ms, p95 4,441 ms, and p99 5,555 ms. These are observed run measurements, not an SLA.

See [METHODOLOGY.md](METHODOLOGY.md) for the full protocol, latency breakdown, evidence-stage diagnostic, comparison caveats, and limits.

## Inspect and reproduce

The published results are sanitized: no API credentials, user/namespace identifier, provider event IDs, raw state cards, or raw API responses are included.

To score the published predictions and run the repository checks:

```bash
python scripts/score_factconsolidation.py
python -m unittest discover -s tests
python scripts/verify_public_release.py
```

A fresh live run uses a new empty test namespace and writes 2,310 facts sequentially, then makes 200 Sarvam answer calls. It can take several hours. Install live-run dependencies and supply your own credentials through environment variables; never commit them:

```bash
python -m pip install -r requirements-live.txt
export SYNTARUS_API_KEY="your-project-key"
export SARVAM_API_KEY="your-Sarvam-key"
python scripts/run_live_factconsolidation.py \
  --user-id "factcon_eval_use-a-new-random-id" \
  --expected-build 10930cca71055a9a9e9cb83b45e25fe8a1903a63 \
  --output local_runs/my_run_predictions.json
```

On PowerShell, set credentials with `$env:SYNTARUS_API_KEY` and `$env:SARVAM_API_KEY` in the current terminal before running the script. The harness refuses a non-empty namespace and does not delete data. Choose a fresh synthetic user ID, keep local outputs private, and use a new ID if an interrupted run left partial data.

## Repository map

- `fixtures/factconsolidation_official_32k.json` — checksum-locked upstream fixture.
- `fixtures/BENCHMARK_LOCK.json` — upstream revision, fixture hash, subsets, and scoring contract.
- `results/factconsolidation_summary.json` — latest run configuration, score, latency, and reuse disclosures.
- `results/factconsolidation_predictions_full.json` — 200 sanitized question/prediction/gold-answer/score records.
- `results/factconsolidation_mh_stage_audit.json` — 100-question MH evidence-stage classification and its limitations.
- `scripts/run_live_factconsolidation.py` — standalone live public-API harness for fresh runs.
- `scripts/score_factconsolidation.py` — dependency-free SubEM scorer.
- `scripts/harness_template.py` — adapter scaffold for evaluating another system under a separately documented protocol.
- `scripts/verify_public_release.py` — checks common secret patterns and prohibited artifact paths.
- `METHODOLOGY.md` — detailed run methodology and interpretation.

## Dataset attribution

FactConsolidation is from [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench), dataset card [ai-hyz/MemoryAgentBench](https://huggingface.co/datasets/ai-hyz/MemoryAgentBench). Refer to the upstream project and dataset card for their terms and citation requirements. Repository code and authored result summaries are licensed under [MIT](LICENSE).
