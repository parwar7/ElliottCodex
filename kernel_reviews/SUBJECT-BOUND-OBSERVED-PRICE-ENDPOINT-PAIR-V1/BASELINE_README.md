# SUBJECT-BOUND-OBSERVED-PRICE-ENDPOINT-PAIR-V1 Infrastructure Logical Baseline

SUBJECT-BOUND-OBSERVED-PRICE-ENDPOINT-PAIR-V1 is an additive, non-authoritative Kernel-infrastructure checkpoint built on the unchanged eleven earlier baselines through NORMAL-IMPULSE-FIVE-SLOT-CANDIDATE-VIEW-V1.

The checkpoint adds `SubjectBoundObservedPriceObservation` and `SubjectBoundObservedPriceEndpointPair`. An observation retains one exact `AnalyzedWaveSubject`, one caller-supplied finite `int` or `float` under the approved P004-style numeric domain, and one exact non-blank opaque `observation_provenance_ref`. The value is retained without coercion. The provenance reference is metadata only and creates no identity, authenticity, market-data, or methodology authority.

An endpoint pair accepts only two exact observation objects whose `subject` references are the same live object. It retains the exact `proposed_start` and `proposed_end` observation identities and derives `pair.subject` directly from `proposed_start.subject`. Matching subject IDs cannot substitute for exact object identity. Proposed start/end are caller-designated Runtime operand roles only; they do not assert chronology, direction, a validated wave origin or end, pivot, extreme, orthodox end, or completion.

The contract performs no market or methodology arithmetic. It exposes no length, span, distance, delta, change, return, ratio, percentage, logarithm, overlap, or direction result. Equal prices and the same observation in both roles are allowed because no protected/runtime contract establishes methodology invalidity for those cases. Future P005/P006 semantics must decide whether such inputs are meaningful.

Both types are frozen, slotted, weak-referenceable, and identity-based rather than value-equal. Their explicit constructors validate before first assignment and reject reinitialization, preventing ordinary-API rebinding, endpoint replacement, reordering, and partial mutation after failed validation. Ordinary direct, dynamic, and multiple-inheritance subclass construction is sealed. Copy and deepcopy return the same immutable identity; dataclass replacement creates a distinct, revalidated, untrusted object; default pickle reconstruction is rejected. JSON-compatible reporting and explicit reconstruction create only untrusted new identities.

Neither type is a `StructuralValidatorResult` or `InternalFamilyValidatorResult`; both certifiers reject them. No producer, issuer, registry entry, certificate, validity, status, outcome, fatality, principle ID, source class, execution role, behavior ID, evidence, ranking, generation, or orchestration authority was added.

The subject-binding, five-slot view, existing methodology behaviors, certification algorithms, and Runtime domain/ingestion contracts remain byte-identical. The validated-family registry remains sealed against `()` with zero producers, behavior IDs, and issuances. No family certificate can issue, and executable methodology remains exactly the six previously approved behaviors.

No P005, P006, P010, motive-family validation, family producer, wave-length calculation, overlap test, completion rule, provider, TradingView, monitoring, alert, network, process, or execution behavior was added.

This is a writable development logical baseline. It does not claim physical immutability, hostile same-process isolation, cryptographic authenticity, provenance authentication, or durable cross-process identity. Future methodology validators must independently validate the endpoint operands under their separately approved source-locked contracts and must not treat construction as methodology proof.
