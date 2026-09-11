# Syntarus Evals

Open evaluation protocols and sanitized results for Syntarus memory retrieval.

This repository is deliberately small. It publishes the test design, synthetic
fixtures, scoring rules, and aggregate outcomes needed to inspect a claim—while
excluding credentials, customer data, raw provider responses, deployment
configuration, and model-provider secrets.

## Direct API hard-case snapshot

On **2026-09-10**, we ran the same synthetic facts and retrieval probes through
the public APIs of Syntarus, Mem0, and Zep. The comparison measures **retrieval
evidence**, not a downstream chat model's answer quality.

| Provider / mode | Strict probes | Mean evidence coverage | Notes |
|---|---:|---:|---|
| Syntarus API | 8 / 8 | 1.000 | Full evidence was visible inside the 120-second window for every primary hard-case probe. |
| Mem0 API | 5 / 8 | 0.975 | Fast retrieval in this sample, with a missed procedure constraint and unsafe unrelated medical context. |
| Zep graph edge search | 0 / 8 | 0.285 | Graph writes succeeded; complete connected evidence was not visible within the same window. |

The primary cases were procedural sequencing, implicit constraints, medical
allergy clearance, and canonical-state supersession. See the sanitized
[summary](results/direct_api_hardcases_2026-09-10.summary.json), the
[per-case breakdown](results/direct_api_hardcases_2026-09-10.case_breakdown.json),
the complete primary synthetic [fixture](fixtures/hard_cases.json), and full
[methodology](METHODOLOGY.md).

### Per-case strict-probe results

| Case | Syntarus API | Mem0 API | Zep graph edge search |
|---|---:|---:|---:|
| Procedural sequence | 2 / 2 | 1 / 2 | 0 / 2 |
| Implicit constraint | 2 / 2 | 2 / 2 | 0 / 2 |
| Medical allergy clearance | 2 / 2 | 0 / 2 | 0 / 2 |
| Canonical state supersession | 2 / 2 | 2 / 2 | 0 / 2 |

## Extended security, temporal anchor & namespace snapshot

In addition to the primary cases, we evaluated 3 extended diagnostic scenarios (6 probes total) testing security boundary behavior, complex temporal reasoning, and multi-tenant isolation on **2026-09-10**:

| Provider / mode | Strict probes | Mean evidence coverage | Key observations |
|---|---:|---:|---|
| Syntarus API | 5 / 6 | 0.944 | Transformed malicious injection ticket into an attack record + surfaced export policy; full temporal date/past-state anchors; zero cross-user leakage. |
| Mem0 API | 2 / 6 | 0.833 | Stored prompt-injection ticket as valid user request without trust labels; partial temporal evidence; zero cross-user leakage. |
| Zep graph edge search | 1 / 6 | 0.556 | Surfaced policy edges but did not expose injection context in 120s; incomplete temporal anchors in 120s; zero cross-user leakage. |

See the sanitized [extended summary](results/direct_api_security_temporal_2026-09-10.summary.json) and [extended case breakdown](results/direct_api_security_temporal_2026-09-10.case_breakdown.json).

### Extended per-case breakdown

| Diagnostic Case | Syntarus API | Mem0 API | Zep graph edge search | Critical finding |
|---|---:|---:|---:|---|
| Poisoning exposure | 2 / 2 | 0 / 2 | 0 / 2 | Syntarus reframed injection as an attack record with governing policy; Mem0 stored it as an active user command; Zep did not retrieve the injection episode. |
| Complex temporal anchors | 2 / 2 | 1 / 2 | 0 / 2 | Syntarus anchored event date (2026-01-31) and past status relative to 2026-03-05; Mem0 returned partial anchors; Zep was incomplete within 120s. |
| Multi-tenant namespace isolation | 1 / 2 | 1 / 2 | 1 / 2 | All three providers demonstrated **zero cross-user leakage** across 20s of adversarial probing. Owner retrieval succeeded across providers. |

The primary and extended fixtures include every synthetic fact, probe, allowed evidence
group, and stale-context rule. We publish scores and interpretation, rather than raw
provider payloads, because raw payloads include volatile request metadata and
are not a safe or stable reproduction surface.

## What this does—and does not—claim

- It is a reproducible snapshot of specific public API modes, dates, and
  settings—not a universal ranking of memory products.
- Every provider received serial writes in the same order and a 20-result
  retrieval budget. No custom extraction prompts or provider-specific reranker
  settings were used.
- The test does **not** benchmark answer-model reasoning, customer workloads,
  cost, availability SLAs, or clinical safety.
- Security checks distinguish retrieval behavior from application security:
  safe agents must enforce trust, authorization, and tool policies outside the
  memory store.

## Repository layout

```
fixtures/   Synthetic facts, probes, and expected evidence anchors
results/    Sanitized aggregate measurements only
scripts/    Release-safety checks for accidental secret publication
METHODOLOGY.md
```

## Reproduce responsibly

Use fresh API keys stored only in environment variables. Never place a key in
source, fixtures, result files, shell history, screenshots, issue comments, or
commit messages. Run tests only against isolated synthetic user namespaces and
delete them at the end of the run.

Before publishing a change, run:

```bash
python scripts/verify_public_release.py
```

This is a release guard, not a substitute for human review.

## Related links

- [Syntarus](https://syntarus.com)
- [Developer console](https://syntarus.com/pages/developers)
- [Continuum memory overview](https://syntarus.com/pages/resources)

## License

The methodology, fixtures, and sanitized result summaries are available under
[MIT](LICENSE).
