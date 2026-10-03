# 32K FactCon chart: data and provenance

Our system's display name is **Continuum**. Its bars and headline are generated from the verified replication summary, not manually entered scores.

| System | Single-hop (%) | Multi-hop (%) | Source |
|---|---:|---:|---|
| Continuum | 95 | 57 | [Verified replication](../results/factconsolidation_summary.json) |
| GPT-4o | 88 | 10 | Table 10 |
| o4-mini | 61 | 14 | Table 5 |
| GPT-4o-mini | 63 | 10 | Table 10 |
| GPT-4.1-mini | 82 | 7 | Table 10 |
| Gemini-2.0-Flash | 49 | 7 | Table 10 |
| Claude-3.7-Sonnet | 46 | 2 | Table 10 |
| Mem0 (paper setup) | 22 | 3 | Table 10 |
| Cognee (paper setup) | 39 | 4 | Table 10 |

Paper source: [MemoryAgentBench, arXiv 2507.05257v3](https://arxiv.org/html/2507.05257v3), **32K FactCon-SH and FactCon-MH columns only**, Tables 5 and 10. GPT-4o is present in both tables and included once. These are all eight distinct reference systems in those two 32K tables; this is not an exhaustive leaderboard of later research.

Paper-reference values were checked against the primary source on October 3, 2026. Mem0 and Cognee use the paper's GPT-4o-mini-backed setups (Appendix F.2), not current commercial APIs. Continuum uses GLM 5.3 through Sarvam v2. Different answerers and construction protocols mean this is a **cross-study reference comparison**, not a controlled A/B or proof that the memory layer alone explains the differences.

The benchmark tests ordered counterfactual fact updates: SH asks for a current fact; MH combines facts across an updated relationship chain. Each Continuum subset contains 100 questions. Scoring uses official normalized substring exact match, not an LLM judge. Continuum's September 28 retained-corpus replay scored 152/200 (76%) with zero failed question requests. It is not a fresh-ingestion or unseen-customer test; see [methodology](../METHODOLOGY.md).

No 6K, 64K or 262K scores are plotted. Zep and other systems without a reported 32K pair in these tables are omitted, not assigned zero. No confidence intervals or significance claims are inferred from these cross-study numbers.

Reproduction: `python -B scripts/render_factcon_32k.py`. Matplotlib dependencies are optional in `requirements-figures.txt`. Public chart data: [JSON](factcon_32k_comparison.json). No API calls or credentials are used to render the image.
