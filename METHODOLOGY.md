# Continuum FactConsolidation — live replay methodology and verification

This publication updates the headline to the September 28 full replication. Existing artifacts were verified offline on October 1, 2026; no new live or paid run was launched for this update. The previous September 27 result files are preserved in `results/archive/2026-09-27/`.

## 1. What this evaluation measures

FactConsolidation tests whether a memory system answers from an ordered history containing updates and contradictions. The official fixture has two 100-question subsets:

- **Single-Hop (SH):** direct lookups from the fact history.
- **Multi-Hop (MH):** questions requiring connections across facts.

“32K” is the upstream subset label; it is not the number of facts written in this run.

## 2. Run identity and scope

- **System:** Continuum through the public Syntarus production API; Continuum only.
- **Run:** retained-corpus full replication, started 2026-09-28 10:19:45 UTC.
- **Recorded target build:** `cb093372018957b672cd5d08f34d60a33ae3fe00`.
- **Dataset:** ai-hyz/MemoryAgentBench, split `Conflict_Resolution`, subsets `factconsolidation_sh_32k` and `factconsolidation_mh_32k`.
- **Dataset revision:** `7ea066982b140a19337e17e60d45d4076e042faf`.
- **Upstream code revision recorded in the benchmark lock:** `fe1735de8cf8b9908e1e3d3b5612afc815698062`.
- **Fixture SHA-256:** `f67d02515da0eb4311b029aa50e1d85340c3ba664c0ecefcba9186eb8a3152fc`.
- **Official answer-prompt SHA-256:** `ca4ea130355adab357ce8cd00bb11c1cdbe7cb945454764a66f1ac7f692f501d`.
- **Answer model:** Sarvam `glm5.3@v2`, temperature 0, 512-token output budget, one answer attempt per question.
- **Shared-context SHA-256:** `2a44d6ad3264a775596fe6de01994d6b348280303fdd964f82288e2c476a7409`.
- **Answer settings in the audited harness:** `reasoning_effort="low"` and a nested request for `enable_thinking=false`. Some calls recorded nonzero reasoning lengths; this is not independent attestation of how the provider applied the switch.

This is not an A/B or vendor-neutral leaderboard run. It does not compare Continuum against search-only, Mem0, Zep, or another memory system.

## 3. Corpus and execution protocol

The SH and MH fixture contexts are byte-identical and contain 2,310 ordered, numbered facts. Those facts had already been ingested through the public API in a prior run. This replay reused the retained namespace and made **zero new fact-write requests**; it then ran all 200 official questions through `POST /v1/memories/resolve`.

The reuse is material to interpretation: this was not a freshly isolated namespace or a new 2,310-write ingestion trial. The run verified that the namespace had retrievable resolver evidence, but it did not perform a complete point-by-point corpus inventory during the replay. It did not delete the retained namespace. The namespace identifier, project key, event IDs, raw API responses, and state cards are intentionally not published.

For each question:

1. The dataset question alone was sent as the retrieval query.
2. The resolver was configured with `top_k=10` and `max_claims=8`; the deployed resolver's internal candidate limit was 50.
3. The answerer received the official FactCon instructions plus the returned Continuum state card. It did not receive the gold answer.
4. The model was called once, with temperature 0. Gold-answer variants were used only after the response for SubEM scoring.

The replication contains 200 unique question records, 0 failed question requests, 200 recorded answer attempts, and 0 recorded answer retries. All recorded answers have `finish_reason="stop"`. Both newer artifacts are marked as resumed; retained attempt counts cannot reconstruct every preflight or discarded/incomplete invocation and are not total paid-call accounting.

The recorded **693.6-second** timer belongs to the final scoring invocation, excluding earlier invocations, pauses, preflights and prior ingestion. No full ingest-plus-answer wall-clock duration is claimed. The runtime fingerprint inherits older-build metadata; the published build is the replay's recorded target, not a new independent runtime attestation.

The replay requested candidate diagnostics for all 100 MH questions. Gold-answer and source-fact checks were performed after answering and are diagnostic only; they were not sent to the resolver or answerer.

## 4. Scoring

The reported measure is normalized substring exact match (SubEM), implemented in [`score_factconsolidation.py`](scripts/score_factconsolidation.py):

1. Lowercase text.
2. Remove ASCII punctuation.
3. Remove the articles “a”, “an”, and “the”.
4. Collapse whitespace.
5. Count a prediction correct if any normalized gold-answer variant is a substring of the normalized prediction.

The denominator stays fixed at 100 SH, 100 MH, and 200 overall. Empty answers, failed requests and non-matches score zero. The scorer loads gold from the checksum-locked fixture and ignores embedded gold. It rejects incomplete sets, duplicates, unknown/boolean indices and non-text predictions. The live harness now treats truncated/non-`stop` answers as failures instead of accepting partial output through a coincidental match.

### Offline verification performed for this update

- Fixture checksum, upstream revisions, shared-context hash and official prompt hash checked without changing the dataset lock.
- Every question identity and exact question/retrieval text checked against the locked fixture; no duplicates or missing questions.
- Official scores recomputed without trusting embedded gold or correctness flags; subset/overall/failure counts checked.
- Retained answer attempts, output budgets, visible lengths and finish reasons checked.
- Latency distributions recomputed from individual question timings and compared with the stored summaries.
- Public data exported through a field allowlist; private namespace/event identifiers checked for absence; common credential patterns scanned.

`scripts/verify_result_artifacts.py` checks all five published prediction sets and their summary/hash consistency against `results/RESULTS_MANIFEST.json`. New summaries include private source-artifact SHA-256 values; raw files are not published. Hashes and these checks establish artifact consistency, not independent execution authenticity, absence of all contamination, backend behavior, causality or customer reliability. `.gitattributes` prevents Windows newline conversion from breaking the fixture checksum.

## 5. Results

| Subset | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Single-Hop (SH) | 95 | 100 | 95% |
| Multi-Hop (MH) | 57 | 100 | 57% |
| Overall | 152 | 200 | 76% |

The previous publication scored 97 SH and 43 MH (140/200, 70%) on build `10930cca71055a9a9e9cb83b45e25fe8a1903a63`. The replication answered 14 more MH questions and 2 fewer SH questions (+12 overall). Different builds and retained/resumed-run conditions make this an observational cross-run comparison, not a controlled ablation of one change.

The preceding September 28 replay scored 95 SH and 58 MH (153/200, 76.5%) with one failed MH question retained in the denominator. The headline uses the subsequent full replication, not the highest-scoring replay. Both September 28 runs target the same build and share corpus/questions, so they are not independent holdouts. A later MH-only paired experiment regressed from 57/100 control to 34/100 canary and is disclosed in [EXPERIMENTS.md](EXPERIMENTS.md).

### Measured latency

These are observed measurements for this run, not an SLA:

| Operation | Count | Mean | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| Reported retrieval server time | 200 | 586.03 ms | 530 ms | 1,009 ms | 1,188 ms |
| Resolver compute | 200 | 27.25 ms | 21.51 ms | 67.40 ms | 108.64 ms |
| Reported memory server total | 200 | 1,057.48 ms | 644.72 ms | 2,533.68 ms | 3,164.27 ms |
| Complete memory API round trip | 200 | 1,351.58 ms | 959 ms | 2,865 ms | 3,486 ms |
| Sarvam answer attempt | 200 | 1,592.93 ms | 933 ms | 4,937 ms | 9,981 ms |
| Question end-to-end | 200 | 2,944.61 ms | 2,565 ms | 6,385 ms | 10,822 ms |
| Durable fact writes during this replay | 0 | n/a | n/a | n/a | n/a |

Percentiles use nearest rank. Server fields are API-reported; round-trip/model times are harness-measured. These describe nested/different portions and must not all be added together. They are not an SLA or capacity guarantee.

## 6. Multi-hop evidence-stage diagnostic

The supplementary [MH stage audit](results/factconsolidation_mh_stage_audit.json) classifies 100 MH questions as follows:

| Stage classification | Questions | Correct SubEM answers |
|---|---:|---:|
| Answer text absent from all recorded retrieval hops | 21 | 1 |
| Answer text lost at candidate selection | 4 | 0 |
| Answer text lost during resolution | 13 | 0 |
| Literal answer text visible in final state card | 62 | 56 |

This diagnostic was recomputed across all recorded retrieval hops. It uses literal normalized answer text, not complete source-to-answer chain proof. A literal match does not establish the correct relationship path; absence can miss paraphrases, and answers may use model priors. No source-fact-ID chain proof is published. These are triage counts, not definitive causal attribution.

## 7. Limitations and interpretation

- One model/configuration, one deployed build, one benchmark split, and one replay; no confidence interval or future-behavior guarantee.
- No competitor arm ran. The results do not establish industry rank or superiority.
- SubEM is reproducible string matching, not a semantic judge or proof that an answer was grounded in the displayed evidence.
- The live build's retrieval/resolution behavior, including any benchmark-adapted relation cues deployed at that build, is part of the measured configuration. That is a disclosed configuration choice, not evidence of generalization to customer-support data.
- Reusing a retained namespace avoids duplicate writes but is not interchangeable with a fresh, clean-room ingestion run. This replay had no full corpus inventory readback and no cleanup.
- External model/network latencies are run-specific and not an SLA.
- The same corpus/questions were used during development and replay; there is no unseen customer holdout. The replication still missed 5 SH and 43 MH questions.
- Retained/resumed corpus, limited reuse readback, inherited runtime fingerprint and incomplete invocation-level paid-call accounting limit interpretation.
- No independent evaluator, confidence interval, sustained load test or customer reliability assessment was performed. The harness certification flag denotes recorded completeness only.

## 8. Reproducing a fresh run

The standalone live harness is [`scripts/run_live_factconsolidation.py`](scripts/run_live_factconsolidation.py). It verifies the locked fixture hash and expected production build, requires a fresh empty synthetic user namespace, ingests facts sequentially through the public API and waits for durable worker completion, then scores all 200 questions. API and Sarvam keys are read only from environment variables; no key is written to result files.

Install `requirements-live.txt`, set `SYNTARUS_API_KEY` and `SARVAM_API_KEY`, and run the command shown in the README. The default full run may take several hours because it performs 2,310 durable writes plus 200 answer calls. The harness intentionally does not delete the test namespace. If interrupted, use a new synthetic user ID rather than blindly replaying writes into a partially populated namespace.

Budget and cap costs first. Verify the approved deployment and pass its build explicitly; a current deployment can differ from this historical snapshot. The standalone harness checks the deployment at preflight; it does not independently audit the private engine or recreate the retained-corpus service snapshot.

## 9. Public artifacts and privacy

- [Locked official fixture](fixtures/factconsolidation_official_32k.json)
- [Run summary](results/factconsolidation_summary.json)
- [Sanitized question-level predictions](results/factconsolidation_predictions_full.json)
- [MH evidence-stage audit](results/factconsolidation_mh_stage_audit.json)

Published outputs include question text, official answer variants, predictions, aggregate scores, safe timings, and the index/stage labels needed to review the diagnostic. They omit API keys, user/namespace IDs, event IDs, raw state cards, and raw API responses.

Safe attempt metadata, file hashes, previous publications and the negative experiment are also included. The private engine implementation is not published. Automated scanning supplements review and cannot detect every possible secret format.
