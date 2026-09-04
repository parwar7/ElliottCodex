# COMPETING-CANDIDATE-SET-CONTAINER-V1

This additive Runtime baseline records a neutral immutable container for every
candidate produced by one exact `CandidateGenerationResult`.

The contract preserves three boundaries:

- candidate membership is not Elliott validity;
- container order is deterministic source order, not rank;
- the active view is an operational filter, not confirmation or preference.

The full ordered membership always retains structurally invalid, unresolved,
and current-supplied-scope-reviewed candidates. The active view excludes only
candidates already carrying genuine structural invalidity from the existing
methodology path. It does not alter candidate state or create a certificate.

This stage adds no Elliott methodology, family validation, degree assignment,
ranking, evidence, indicators, forecasting, TradingView, alerts, or trading.

Next approved design target: `ELLIOTT-FAMILY-HYPOTHESIS-BRIDGE-RESEARCH-AND-BOUNDARY-V1`.
