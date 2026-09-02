# P023-V1 Methodology Logical Baseline

P023-V1 is the fourth executable methodology checkpoint. P004-V1, DEGREE-PEER-V1, and PARENT-CHILD-DEGREE-V1 remain unchanged.

P023 is a caller-supplied resolution and visibility guard. It prevents the Kernel from treating unseen required internals as confirmed or inventing hidden pivots or waves. `VISIBLE` means only that inspection is available; it does not confirm or validate internals. `NOT_VISIBLE` leaves internals unresolved and requests finer data without invalidating the candidate.

P023 does not select an exact finer timeframe and is not connected to orchestration, providers, TradingView, or data fetching. Exact-case input handling and malformed-input diagnostics are Runtime policy rather than additional protected Elliott methodology.

The behavior-local and shared `INTERNALS_UNRESOLVED` statuses remain distinct enum types but serialize individually to the same scalar text. A complete P023 result remains distinguishable through `behavior_id = P023_INTERNAL_VISIBILITY_GUARD`; no current consumer ambiguity exists.

Any future change to P023 must be reported explicitly as a P023-V1 delta and undergo separate review.

This is a development logical baseline. It does not claim physical immutability, ACL protection, cryptographic signing, or process isolation.
