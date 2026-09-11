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
[summary](results/direct_api_hardcases_2026-09-10.summary.json) and full
[methodology](METHODOLOGY.md).

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
