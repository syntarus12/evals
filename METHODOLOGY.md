# Continuum FactConsolidation — live replay methodology

## 1. What this evaluation measures

FactConsolidation tests whether a memory system answers from an ordered history containing updates and contradictions. The official fixture has two 100-question subsets:

- **Single-Hop (SH):** direct lookups from the fact history.
- **Multi-Hop (MH):** questions requiring connections across facts.

“32K” is the upstream subset label; it is not the number of facts written in this run.

## 2. Run identity and scope

- **System:** Continuum through the public Syntarus production API; Continuum only.
- **Run:** retained-corpus replay, started 2026-09-27 14:07:03 UTC.
- **Production build:** `10930cca71055a9a9e9cb83b45e25fe8a1903a63`.
- **Dataset:** ai-hyz/MemoryAgentBench, split `Conflict_Resolution`, subsets `factconsolidation_sh_32k` and `factconsolidation_mh_32k`.
- **Dataset revision:** `7ea066982b140a19337e17e60d45d4076e042faf`.
- **Upstream code revision recorded in the benchmark lock:** `fe1735de8cf8b9908e1e3d3b5612afc815698062`.
- **Fixture SHA-256:** `f67d02515da0eb4311b029aa50e1d85340c3ba664c0ecefcba9186eb8a3152fc`.
- **Official answer-prompt SHA-256:** `ca4ea130355adab357ce8cd00bb11c1cdbe7cb945454764a66f1ac7f692f501d`.
- **Answer model:** Sarvam `glm5.3@v2`, temperature 0, 512-token output budget, one answer attempt per question.

This is not an A/B or vendor-neutral leaderboard run. It does not compare Continuum against search-only, Mem0, Zep, or another memory system.

## 3. Corpus and execution protocol

The SH and MH fixture contexts are byte-identical and contain 2,310 ordered, numbered facts. Those facts had already been ingested through the public API in a prior run. This replay reused the retained namespace and made **zero new fact-write requests**; it then ran all 200 official questions through `POST /v1/memories/resolve`.

The reuse is material to interpretation: this was not a freshly isolated namespace or a new 2,310-write ingestion trial. The run verified that the namespace had retrievable resolver evidence, but it did not perform a complete point-by-point corpus inventory during the replay. It did not delete the retained namespace. The namespace identifier, project key, event IDs, raw API responses, and state cards are intentionally not published.

For each question:

1. The dataset question alone was sent as the retrieval query.
2. The resolver was configured with `top_k=10` and `max_claims=8`; the deployed resolver's internal candidate limit was 50.
3. The answerer received the official FactCon instructions plus the returned Continuum state card. It did not receive the gold answer.
4. The model was called once, with temperature 0. Gold-answer variants were used only after the response for SubEM scoring.

The public artifact records 200 scored questions, 0 failed question requests, 200 scored answer attempts, 0 scored-answer retries, and one separate non-scored model connectivity preflight. The question/answer replay took **581.3 seconds**; this does not include the earlier ingestion time.

The replay requested candidate diagnostics for all 100 MH questions. Gold-answer and source-fact checks were performed after answering and are diagnostic only; they were not sent to the resolver or answerer.

## 4. Scoring

The reported measure is normalized substring exact match (SubEM), implemented in [`score_factconsolidation.py`](scripts/score_factconsolidation.py):

1. Lowercase text.
2. Remove ASCII punctuation.
3. Remove the articles “a”, “an”, and “the”.
4. Collapse whitespace.
5. Count a prediction correct if any normalized gold-answer variant is a substring of the normalized prediction.

The denominator stays fixed at 100 SH, 100 MH, and 200 overall. Empty answers and non-matches count as incorrect. The scorer loads gold answers from the checksum-locked fixture and ignores embedded gold fields in the result artifact.

## 5. Results

| Subset | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Single-Hop (SH) | 97 | 100 | 97% |
| Multi-Hop (MH) | 43 | 100 | 43% |
| Overall | 140 | 200 | 70% |

The previous public run reported 98/100 SH and 15/100 MH (113/200 overall, 56.5%) on build `33e2b8a613226818b31d35568d84d1ef8fd74f9d`. The new replay is +28 MH answers and -1 SH answer versus that result. Because the production build changed and this replay reused a retained namespace rather than repeating a fresh isolated ingestion, the comparison is **cross-run and observational**, not a controlled ablation. It cannot identify which individual code change caused the difference.

### Measured latency

These are observed measurements for this run, not an SLA:

| Operation | Count | Mean | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| Resolver compute | 200 | 7 ms | 5 ms | 19 ms | 31 ms |
| Sarvam answer attempt | 200 | 896 ms | 761 ms | 1,726 ms | 2,118 ms |
| Question end-to-end | 200 | 2,159 ms | 1,724 ms | 4,441 ms | 5,555 ms |
| Durable fact writes during this replay | 0 | n/a | n/a | n/a | n/a |

End-to-end time includes API/network and external model time. Resolver compute is only one part of the response path; these numbers are not a service-level objective or capacity guarantee.

## 6. Multi-hop evidence-stage diagnostic

The supplementary [MH stage audit](results/factconsolidation_mh_stage_audit.json) classifies 100 MH questions as follows:

| Stage classification | Questions | Correct SubEM answers |
|---|---:|---:|
| Answer text not found in initial retrieval candidates | 47 | 12 |
| Answer text lost at candidate selection | 3 | 0 |
| Answer text lost during resolution | 17 | 1 |
| Literal answer text visible in final state card | 33 | 30 |

This is a **literal normalized answer-text** diagnostic, not a full source-to-answer chain proof. Source-fact-ID provenance was unavailable for these rows, and the classifier can miss paraphrases. A literal answer string in the card does not prove the whole chain was present; a correct answer without that literal string may be a paraphrase or may come from model prior knowledge. Treat the stage counts as triage evidence, not as definitive causal attribution.

## 7. Limitations and interpretation

- One model/configuration, one deployed build, one benchmark split, and one replay; no confidence interval or future-behavior guarantee.
- No competitor arm ran. The results do not establish industry rank or superiority.
- SubEM is reproducible string matching, not a semantic judge or proof that an answer was grounded in the displayed evidence.
- The live build's retrieval/resolution behavior, including any benchmark-adapted relation cues deployed at that build, is part of the measured configuration. That is a disclosed configuration choice, not evidence of generalization to customer-support data.
- Reusing a retained namespace avoids duplicate writes but is not interchangeable with a fresh, clean-room ingestion run. This replay had no full corpus inventory readback and no cleanup.
- External model/network latencies are run-specific and not an SLA.

## 8. Reproducing a fresh run

The standalone live harness is [`scripts/run_live_factconsolidation.py`](scripts/run_live_factconsolidation.py). It verifies the locked fixture hash and expected production build, requires a fresh empty synthetic user namespace, ingests facts sequentially through the public API and waits for durable worker completion, then scores all 200 questions. API and Sarvam keys are read only from environment variables; no key is written to result files.

Install `requirements-live.txt`, set `SYNTARUS_API_KEY` and `SARVAM_API_KEY`, and run the command shown in the README. The default full run may take several hours because it performs 2,310 durable writes plus 200 answer calls. The harness intentionally does not delete the test namespace. If interrupted, use a new synthetic user ID rather than blindly replaying writes into a partially populated namespace.

## 9. Public artifacts and privacy

- [Locked official fixture](fixtures/factconsolidation_official_32k.json)
- [Run summary](results/factconsolidation_summary.json)
- [Sanitized question-level predictions](results/factconsolidation_predictions_full.json)
- [MH evidence-stage audit](results/factconsolidation_mh_stage_audit.json)

Published outputs include question text, official answer variants, predictions, aggregate scores, safe timings, and the index/stage labels needed to review the diagnostic. They omit API keys, user/namespace IDs, event IDs, raw state cards, and raw API responses.
