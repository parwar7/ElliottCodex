# MULTI-TIMEFRAME-OBSERVATION-TRANSPORT-V1

This additive logical baseline records same-process transport of exact existing
`NormalizedMarketObservations` objects alongside one exact live
`RecursiveCandidateCompositionResult`. It is project analysis infrastructure,
its associations are caller-supplied observation associations, and its workflow
rules are project operational policy.

`MultiTimeframeObservationBundle` retains a caller-selected `SymbolIdentity`,
the exact caller-ordered observation tuple, and provenance references. Every
observation must use the exact existing normalized type. Symbol consistency is
exact value equivalence over the existing symbol, market type, exchange, and
provider-symbol fields. Distinct observation sets must have unique positive
`Timeframe.resolution_seconds`; datasets are never merged or selected silently.

Caller order remains unchanged. A separate deterministic resolution inventory
orders the same live observation objects from finer to coarser sampling by
`resolution_seconds`. This ordering is only chart-resolution metadata.
Timeframe is not Elliott degree.

`SubjectObservationAttachment` binds one exact recursive-tree subject to one
exact bundle observation with an operational-only association role. Foreign
subjects, foreign observations, duplicate subject/observation identity pairs,
mappings, ducks, subclasses, serialized lookalikes, and low-level mutation fail
closed. Subjects may have zero, one, or several attached resolutions.

Finer/coarser queries answer only whether an explicitly attached sampling
resolution exists. They do not change P023, create visibility, validate family,
infer degree, confirm another timeframe, create recursive children, or issue a
methodology result.

The transport retains exact bars, data provenance, resampling metadata, data
quality, volume availability, and differing date coverage without interpreting
them. It performs no fetching, resampling, indicators, pivot/wave/pattern logic,
ranking, alerts, or trading logic.

