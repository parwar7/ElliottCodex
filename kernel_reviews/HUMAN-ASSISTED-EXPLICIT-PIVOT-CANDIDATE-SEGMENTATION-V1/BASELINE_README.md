# HUMAN-ASSISTED-EXPLICIT-PIVOT-CANDIDATE-SEGMENTATION-V1

This additive logical baseline records `PROJECT_ANALYSIS_INFRASTRUCTURE` and
`PROJECT_OPERATIONAL_POLICY`. It adds no Elliott methodology behavior.

`ExplicitPivotObservation` records a caller-supplied opaque pivot ID, explicit
validated UTC timestamp, finite observed price, and optional provenance. It is
classified `CALLER_SUPPLIED_PIVOT_OBSERVATION`; it is not a discovered pivot,
wave endpoint, orthodox endpoint, source rule, result, proof, or certificate.

`ExplicitPivotChildGroup` records exact caller-selected start/end pivot
identities and an explicitly supplied child subject. Groups preserve supplied
order, may share one boundary pivot, and may leave caller-explicit gaps. They
cannot overlap beyond a shared boundary, run backward, reference foreign
pivots, or silently create children. Grouping is classified
`CALLER_SUPPLIED_STRUCTURE_DECLARATION` and is not family proof.

`ExplicitPivotCandidateRequest` enforces strictly increasing pivot timestamps,
unique pivot IDs and identities, exact group boundaries, explicit parent/child
subjects, and an explicit binding ID whenever groups exist. The existing
`OrderedChildBinding` is constructed from those exact subjects without wave
positions, family, degree, completion, or required-child claims.

Every parent pivot becomes one existing non-authoritative
`SubjectBoundObservedPriceObservation`. Each explicit child group produces one
existing proposed endpoint pair bound to its exact child subject. These objects
retain observed prices but create no structural or orthodox endpoint authority.

P004 is generated only from an `ExplicitP004PivotRole` that names the exact
origin and end pivot objects. Cardinality, P023 visibility, degree facts, and
P003 relation are accepted only as explicit existing manual declarations.
Pivot count, geometry, spacing, timing, price direction, or group count infer
nothing. P005/P006 and certificates are unavailable through this input layer.

`MethodologyKernel.analyze_explicit_pivot_candidate` delegates exactly to
`analyze_bounded_manual_chart` and retains the exact bounded request/result.
There is no methodology dispatch or direct validator execution in the pivot
module.

The existing CLI now recognizes the separate, unambiguous
`HUMAN_READABLE_EXPLICIT_PIVOT_CANDIDATE_V1` schema while preserving the prior
manual schema. Reports are marked `NON_AUTHORITATIVE_REPORTING_VIEW` and cannot
be loaded back as authority.
