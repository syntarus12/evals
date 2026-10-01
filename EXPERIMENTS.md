# Experimental resolver result — September 29, 2026

This appendix discloses a **negative result**, separately from the headline SH+MH replication. It is a paired MH-only experiment, not a competitor evaluation or evidence that the canary is ready for production.

| Arm | Correct | Official questions | Accuracy | Failed questions |
|---|---:|---:|---:|---:|
| Default resolver control | 57 | 100 | **57%** | 0 |
| Opt-in bounded chain canary | 34 | 100 | **34%** | 1 |

The canary regressed by 23 correct answers. Its failed question stays in the 100-question denominator; 99 answered cases do not replace the official denominator. The headline remains the full replication's 95% SH / 57% MH. This is a selected disclosed experiment, not an exhaustive log of every development attempt.

## Recorded configuration

- Target build: `2bd676e8028a19e3025ea0b81f1f9daf52063cfd`.
- Same retained corpus and 100 official MH questions in both arms; alternating arm order; no ingestion/deletion between arms.
- Answerer: Sarvam `glm5.3@v2`, temperature 0, recorded 512-token budgets, zero answer transport retries.
- Public resolver in both arms: `top_k=10`, `max_claims=8`. The canary opted into bounded chain retrieval with a second-hop cap of 5.
- Resolver retry policy: up to 2 retries for transient failures, identical across arms.
- Recorded status: `complete_with_failures`; harness certification flag: false.

Every question identity, prediction and correctness flag was verified offline against locked official gold. This comparison has within-run controls but remains one benchmark-specific retained-corpus experiment, not proof of generalization, safety or vendor rank.

## Complete artifacts

- [Paired summary and private-source checksum](results/experiments/2026-09-29_chain_canary_summary.json).
- [All 100 control predictions](results/experiments/2026-09-29_control_predictions.json).
- [All 100 canary predictions, including its failure](results/experiments/2026-09-29_chain_canary_predictions.json).

Run `python -B scripts/verify_result_artifacts.py` to check both arms and the three full-run publications. No API call or paid experiment is needed.
