# Continuum FactConsolidation — live run methodology

## 1. What this evaluation measures

FactConsolidation tests whether a memory system can answer questions from a sequence of facts that include updates and contradictions. The official split used here contains two 100-question subsets:

- **Single-Hop (SH):** answer a direct lookup from the fact history.
- **Multi-Hop (MH):** combine facts across links while respecting updates.

The “32K” text is the upstream subset label. It is **not** the number of facts written in this run.

## 2. Run identity and scope

- **System under test:** Continuum, through the public Syntarus production API.
- **Scope:** Continuum only. This was not an A/B or vendor-neutral leaderboard run; no search-only or other vendor arm was evaluated.
- **Production build:** 33e2b8a613226818b31d35568d84d1ef8fd74f9d.
- **Dataset:** ai-hyz/MemoryAgentBench, split Conflict_Resolution, subsets factconsolidation_sh_32k and factconsolidation_mh_32k.
- **Dataset revision:** 7ea066982b140a19337e17e60d45d4076e042faf.
- **Upstream code revision:** fe1735de8cf8b9908e1e3d3b5612afc815698062.
- **Published fixture SHA-256:** f67d02515da0eb4311b029aa50e1d85340c3ba664c0ecefcba9186eb8a3152fc.
- **Official prompt SHA-256 recorded by the harness:** ca4ea130355adab357ce8cd00bb11c1cdbe7cb945454764a66f1ac7f692f501d.
- **Configured answer model:** glm5.3@v2, temperature 0.

The checksum and source revisions are also recorded in [BENCHMARK_LOCK.json](fixtures/BENCHMARK_LOCK.json). The run summary contains the aggregate scores and non-sensitive configuration.

## 3. Live production procedure

1. The harness validated the expected production build and public HTTP path before the evaluation.
2. It created a fresh, isolated temporary user namespace. The namespace identifier and credentials are intentionally not published.
3. It sent the benchmark facts as **2,310 ordered, numbered, durable writes** through POST /v1/memories. The run used the public write path and waited for durable worker checkpoints; there was one outstanding ordered submission, preserving fact order.
4. The official SH and MH fixture contexts were byte-identical. To avoid writing the same context twice, the facts were ingested once and shared by the two question subsets.
5. It evaluated all 100 SH and all 100 MH questions using the public /memories/resolve Continuum path. The retrieval query was the dataset question only; the answerer received the official task instructions and the returned Continuum context. The configured retrieval limit was top 10, with resolver limits of 8 claims and 50 internal candidates.
6. Gold answers were kept out of ingestion and answering. After predictions were produced, every question was scored against the official answer variants from the pinned fixture.
7. The harness checked the complete denominator and result integrity, deleted the temporary namespace, and verified that a post-delete resolve returned zero results.

The run completed in **10,825.9 seconds (about 3 hours)**. All 2,310 writes completed, all 200 question requests were scored, there were zero failed Continuum requests, and namespace cleanup was verified. No API key, raw state card, temporary namespace identifier, or provider event identifier is included in this repository.

## 4. Scoring

The reported metric is the official normalized substring exact match (SubEM) implementation in [score_factconsolidation.py](scripts/score_factconsolidation.py):

1. Lowercase the text.
2. Remove ASCII punctuation (without replacing punctuation with spaces).
3. Remove the articles a, an, and the.
4. Collapse whitespace.
5. Count a prediction correct when any normalized gold-answer variant is a substring of the normalized prediction.

Every question remains in the fixed denominator: 100 SH, 100 MH, 200 overall. Empty or non-matching answers count as incorrect. The scorer reads gold answers from the locked fixture rather than trusting gold fields in the prediction artifact.

## 5. Results

| Subset | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Single-Hop | 98 | 100 | 98% |
| Multi-Hop | 15 | 100 | 15% |
| Overall | 113 | 200 | 56.5% |

This pattern is the main finding: direct retrieval was strong in this run, but multi-hop performance was poor. The overall average does not remove that weakness.

### Measured latency

Latency is from this specific production run, not a capacity guarantee:

| Operation | Count | Mean | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| Answer attempt | 200 | 1,074 ms | 849 ms | 2,158 ms | 3,648 ms |
| Question end-to-end | 200 | 1,791 ms | 1,586 ms | 3,052 ms | 4,341 ms |
| Durable write end-to-end | 2,310 | 4,527 ms | 4,393 ms | 10,449 ms | 12,680 ms |

## 6. Limits and interpretation

- This is one run against one production build, one API configuration, and one benchmark split. It is not a confidence interval or a guarantee of future behavior.
- There is no same-run baseline, so these scores do not support a claim that Continuum is better or worse than another system.
- SubEM is an automatic string-matching metric. It is reproducible, but does not judge explanation quality or semantic equivalence beyond the official accepted answer variants.
- SH and MH use shared ingested context; they are two question subsets over one memory stream, not two independent ingestion trials.
- Production latency includes external service and network conditions observed at run time and should not be read as an SLA.

## 7. Public artifacts and privacy

- [Locked official fixture](fixtures/factconsolidation_official_32k.json)
- [Run summary](results/factconsolidation_summary.json)
- [Sanitized question-level predictions](results/factconsolidation_predictions_full.json)

The published records contain only subset, question index, question text, official answer variants, prediction, and correctness. Temporary account/user IDs, API keys, event IDs, raw retrieved state cards, and raw API responses were excluded. The fresh namespace was verified empty after the run.
