# X thread — Continuum / FactCon 32K

Attach `assets/continuum-factcon-32k.png` to post 1. Each numbered block is a separate post, within the standard 280-character limit. Draft only; not automatically published.

## 1

An agent can remember a fact—and still act on an outdated one.

We tested Continuum on FactConsolidation 32K:

95% single-hop
57% multi-hop
76% overall: 152/200 questions

Zero failed question requests in the verified replication.

Here's what the test actually measures. 🧵

## 2

FactCon isn't just “find this sentence.” Facts change over time.

Single-hop: retrieve the current fact after updates.
Multi-hop: connect several updated facts to answer a question.

Remembering history is useful. Knowing which parts still apply is the harder problem.

## 3

Think of a support agent: the account owner changes, an entitlement changes, then a ticket arrives.

It needs the current owner AND current entitlement—not a convincing answer assembled from stale history.

That's the kind of failure this benchmark helps us investigate.

## 4

The chart includes published 32K reference scores from MemoryAgentBench, Tables 5 & 10.

These are paper configurations, not fresh competitor API tests. Different models were used; this is not a same-model A/B.

Continuum: GLM 5.3 answerer, retained-corpus API replay.

## 5

We rescored all 200 predictions against locked official answers using SubEM—not an LLM judge.

95/100 single-hop. 57/100 multi-hop.

Older 97%/43% figures belong to a previous run. The latest verified headline is 95%/57%.

57% also tells us there's more work to do.

## 6

Full questions, predictions, scoring code, methodology and chart sources:
https://github.com/syntarus12/evals

Building a support or workflow agent that loses track of changing customer context? We'd love to test on a real use case.

Try Continuum: https://syntarus.com

## Image alt text

FactConsolidation 32K cross-study reference comparison. Continuum: 95% single-hop, 57% multi-hop, 76% overall (152/200). Two bar panels use a 0–100% axis. Published paper baselines SH/MH: GPT-4o 88/10; o4-mini 61/14; GPT-4o-mini 63/10; GPT-4.1-mini 82/7; Gemini-2.0-Flash 49/7; Claude-3.7-Sonnet 46/2; Mem0 paper setup 22/3; Cognee paper setup 39/4. Different models and protocols; not a same-run A/B. Sources: MemoryAgentBench v3 Tables 5 and 10 and Continuum's verified replication.
