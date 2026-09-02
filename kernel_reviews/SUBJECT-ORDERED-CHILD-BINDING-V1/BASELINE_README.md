# SUBJECT-ORDERED-CHILD-BINDING-V1 Shared Contract Logical Baseline

SUBJECT-ORDERED-CHILD-BINDING-V1 is an additive, non-authoritative Kernel-infrastructure checkpoint built on the unchanged nine earlier baselines through VALIDATED-INTERNAL-FAMILY-CONTRACT-V1.

The checkpoint adds two public input types: `AnalyzedWaveSubject` and `OrderedChildBinding`. An analyzed subject contains only an opaque caller-supplied subject ID and observation-provenance reference. A binding contains only an opaque caller-supplied binding ID, one exact parent-subject object, and an exact tuple of child-subject objects whose tuple order is the sole ordinal position model.

Both types are frozen, slotted, weak-referenceable, and identity-based rather than value-equal. Copy and deepcopy preserve the same immutable object. Pickle is rejected. JSON-compatible dataclass records are audit data only; explicitly reconstructed objects are new untrusted identities.

Zero and one child are allowed because this shared input contract makes no cardinality or completeness claim. Within one binding, the parent cannot also be a child, one exact child object cannot occupy multiple positions, and parent/child subject IDs must be unique. Child or parent objects may participate in separate untrusted bindings; each such object remains a separate caller assertion with no proof authority.

The contract does not establish parentage, Wave 1–5 legitimacy, temporal continuity, anchors, pivots, timeframe, degree, completion, pattern, family, validity, fatality, source classification, or evidence. It creates no certificate, issuer, attestation, registry, producer, behavior, or protected principle ID.

The protected Wave 1–5 references were not converted into shared binding vocabulary. Tuple order is purely ordinal. A future reviewed methodology validator must establish its own scope, cardinality, slot meaning, provenance authenticity, rule results, child-family proofs, and exact identity checks before any family result can issue.

Both existing certification algorithms remain byte-identical. The validated-family producer registry remains sealed against `()` with zero producers and zero issuances. No family certificate can currently be issued. Executable methodology remains exactly the six previously approved behaviors.

This is a development logical baseline. It does not claim physical immutability, global identity uniqueness, provenance authenticity, hostile same-process isolation, cryptographic signing, or durable cross-process identity.
