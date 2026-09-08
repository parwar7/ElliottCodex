# Implemented evidence boundary and unimplemented attachment proposal

## Additive Runtime contract

`src/elliott_runtime/market_data/aggregate_extremum.py` adds `find_extremum_occurrences(...)`, `ExtremumOccurrenceEvidence`, `interval(...)`, and `occurrence_envelope(...)`. No Kernel file or shared contract changes.

Input: exact saved `TradingViewSnapshot`, original aggregate `Bar` identity, high or low field, explicitly selected finer snapshot; optionally a genuine original `NormalImpulsePartialEvaluationResult`, role index and start/end side. The current optional parent context supports the single evaluation issued by the existing scope factory; no general multi-evaluation selector or authority is implied.

Output keeps the aggregate bar label, civil/session envelope, examined original finer bars, **all** corresponding exact represented-price matches, status and coverage/snapshot limitations. Unknown interval, missing finer rows, no observed match, one match and multiple matches remain distinct. Forming/revised/non-synchronous/partial states are orthogonal flags, not silently absorbed into a no-match claim.

The native monthly label (within the first seven calendar days at the declared regular opening time) selects its calendar month. This conservative adapter supports the saved TradingView timestamp convention only, not an exchange holiday proof. Month membership uses exchange-local civil boundaries and DST, never nominal 30-day seconds or an unchecked next bar. Daily and intraday intervals are envelopes under the declared 09:30–16:00 regular session; holidays, early closes and completeness remain unverified. A unique match means unique in supplied rows only.

Metadata checks separate resolution from degree and compare exact symbol/feed/listing/currency/session/timezone and available adjustment fields. Boolean values cannot alias numeric settings. Unknown split adjustment and differing capture times remain explicit. Source revision metadata is recorded but not applied to either immutable snapshot.

An issuance snapshot pins original aggregate/finer snapshots, observation and bar tuples, examined/matching tuples, parent hypothesis/view/binding/subject/children and endpoint identities. Revalidation checks identities plus a content digest and re-derives the row set; failed validation does not update the snapshot. Copies/deserialization of JSON have no authority. Pickle of live evidence is prohibited. This is in-process mutation detection, not protection against arbitrary hostile code rewriting private Python memory.

The local geometry cache separately pins exact snapshot/config/scoped bar/discovery/pivot identities and content. It caches geometry only; every contextual candidate subject and result is freshly issued. Operational windows, first/last eligible selection and budgets are not source rules.

Independent candidate-search date windows are half-open UTC-date selections of the original regular-session bars (`start <= timestamp_utc.date() < end`). They are not aggregate membership envelopes or assertions that a hypothetical child covers an entire calendar/session interval. In this US regular-session capture these date labels identify the same local trading day; no overnight or extended session is silently included.

## Why no old-parent child attachment was made

Existing `normal_component_exploration.ComponentSearch._check_values` defines child bar membership using the original role's `start_boundary.timestamp_utc <= bar.timestamp_utc <= end_boundary.timestamp_utc`. `ComponentEvaluation.__post_init__` also enforces candidate containment and exact original child-subject identity. Recursive composition consumes this issued ancestry, not a later observational correspondence.

For M1, the original end boundary is the native Monthly bar timestamp May 1. A matched finer bar on May 14 cannot be inserted into that same issued timestamp window without changing its meaning. A bar containing an equal high is not a newly authorized orthodox endpoint and does not grant permission to widen that existing role. A September match likewise does not resolve the original forming Monthly endpoint.

Implemented solution: preserve the original M1/M2 objects and endpoints unchanged. Create independent exact finer candidates through existing public factories, with fresh subjects and bindings. Store occurrence evidence IDs as **observational context only**, `parent_node_id = null` and `old_parent_id = null`; run own P004/P005 evaluations. No old outcome or certificate is transferred. Rejected independent alternatives do not reject the original parent or other siblings.

## Proposed future change — NOT APPLIED

If genuine attachment across aggregate-bar labels is later required, review a separate additive observation-window transport rather than editing existing endpoint timestamps:

- Original parent result, exact evaluation/role, original role subject and original five-slot binding.
- Exact start/end occurrence evidence objects, with all ambiguous alternatives retained.
- Explicit observation envelope and snapshot/session compatibility status, separately typed from the parent's existing candidate endpoint timestamps.
- A separately issued candidate subject/binding and an explicit relationship kind such as observational refinement, not equivalence to an orthodox endpoint.
- A validator that must reject missing/multiple/partial/forming authority where attachment requires uniqueness or completion; it must not silently manufacture that authority from a match.
- A separate decision on whether any such observational refinement can enter the existing recursive composition. Its present contract would not accept the widened timestamp relation. This decision is not solved here, and no change is proposed to the meaning of existing `ComponentSearch`, `OrderedChildBinding` or Kernel composition.

Potential Runtime integration points would be `normal_component_exploration.py` and a new transport adapter; **none changed**. Any future Kernel contract need requires its own approval. No protected file amendment is necessary for the observation-only implementation delivered here.

The earlier timestamp-window limitation is narrowed only for **observational examination**, not superseded for ancestry. Terminal family proof, P006 and unrelated freezes remain blocked independently.
