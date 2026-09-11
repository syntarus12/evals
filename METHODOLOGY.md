# Direct API hard-case methodology

## Goal

Measure what a memory API makes available to a downstream agent when the agent
faces facts that are easy to store but difficult to use safely: ordered
procedures, implied access constraints, corrected medical facts, and changed
canonical state.

The benchmark evaluates retrieval evidence, not the prose quality of an answer
model. A separate answer model can hide a retrieval failure—or create a correct
answer for the wrong reason—so it is intentionally out of scope here.

## Protocol

1. Create an isolated synthetic user namespace for each provider and case.
2. Write the same short facts serially, in the same order.
3. Wait for documented asynchronous ingestion where the API exposes an event.
4. Run the same two natural-language probes with a maximum of 20 returned
   records/edges.
5. Poll retrieval until every required evidence group is present, or until the
   120-second visibility deadline expires.
6. Score returned evidence deterministically against required anchors and
   stale-state rules.
7. Delete only the synthetic namespaces created by the run.

## API modes

| Provider | Write path | Retrieval path | Completion handling |
|---|---|---|---|
| Syntarus | Memory write | Memory search | Event-status polling |
| Mem0 | V3 memory add | V3 memory search with user filter | Event-status polling |
| Zep | Graph text episode | Graph edge search | Retrieval visibility polling |

No provider received custom extraction instructions, a special query rewrite,
or a provider-only filtering advantage. The selected modes are important:
this comparison is about these public API paths, not every feature each product
offers.

## Primary cases

### 1. Procedural sequence and runbook gotcha

The evidence must preserve ordering across six steps and retain a safety
constraint: a particular service must not restart before the migration is
complete.

### 2. Implicit constraint disconnect

The user asks for a pleasant route, while relevant stored facts describe a
wheelchair user, stairs, slopes, cobblestones, rest intervals, and a walking
limit. Correct retrieval must connect the implicit request to these constraints.

### 3. Medical allergy clearance

The evidence must retain a current peanut-anaphylaxis restriction while
recognising that dairy is not an allergy. Distractor facts include another
person's shellfish allergy.

### 4. Canonical-state supersession

The evidence must retrieve the current configuration value and retain enough
history to show why older values must not be used.

## Extended diagnostic checks

These checks are informative but are not treated as product-security
certifications.

- **Poisoning exposure:** an untrusted ticket attempts to inject a harmful
  instruction. We inspect whether it is stored, how it is represented, and
  whether governing policy is retrieved with it.
- **Temporal anchors:** dated facts must support a “past, not upcoming” answer
  from a later reference date.
- **Namespace isolation:** an owner must retrieve its own synthetic markers;
  another synthetic user is repeatedly searched for those markers for 20
  seconds. This tests data separation by `user_id`, not end-user
  authentication. Applications must still authorize who may select a user ID.

## Scoring

Each probe has required evidence groups. A group passes if at least one of its
allowed phrases appears in the normalized returned evidence. Coverage is the
fraction of groups that pass. A strict pass requires complete coverage and no
unexplained stale context.

This deliberately favours auditability over semantic generosity. Phrase-based
scoring can undercount valid paraphrases, so raw outputs should be privately
reviewed before making a high-stakes claim. The public release contains only
sanitized aggregates.

## Fairness safeguards

- Synthetic data only; no customer conversations, production identifiers, or
  real credentials.
- Separate namespaces per provider, case, and diagnostic user.
- Identical fact order and natural-language probes.
- Same top-k budget and visibility deadline.
- Provider write, event, retrieval, and cleanup failures recorded separately.
- A failed API call is never converted into a retrieval miss or a pass.

## Limitations

One run measures one time, one public API configuration, and one small fixture.
It cannot establish general quality, security, latency, price, availability,
or medical safety. In particular, no memory API alone can prevent an agent
from obeying malicious retrieved text. Production agents need source trust
boundaries, authorization, output validation, and tool-level policy checks.
