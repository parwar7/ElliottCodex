# NVDA historical hypotheses

## Technical summary

Bounded candidate exploration only: no complete validated Elliott count, current-wave claim or directional forecast is established.

586 hypotheses were retained. Hierarchy levels are operational, never Elliott degrees. Current position remains unresolved for every context.

## Four distinct capabilities

- A. Bounded search across all three historical regions, not exhaustive full-history search.
- B. Coarsened full-range endpoint proposals exist; they are not a coherent full-history Elliott count. Prefix/tail observations and unexamined interiors remain unresolved.
- C. The run retained exact links through 3 child level(s). Unvisited branches are not reviewed or terminal.
- D. No defensible current-position hypothesis is established. Final pivots do not authorize current or next-wave labels.

## Data and definitions

Reuses the preserved Yahoo capture from 6 September 2026. Latest bars are dated 4 September 2026. No fresh retrieval or resampling. Root resolution is Monthly; explicit finer selections are Weekly, Daily and 1H. Resolution is not degree.

A window is a search scope, a hypothesis is an unconfirmed proposed structure, and a linked row is an exact parent-requirement evaluation context. Repeated endpoints are not independent confirmations.

## Historical coverage and exclusions

Regions retain scheduled and unvisited six-pivot windows separately. One additional coarsened proposal samples six source indices evenly across the full pivot range; this is an operational sampling policy, not important-wave selection.

| Region | Years | Pivots | Examined windows | Unvisited windows |
|---|---|---:|---:|---:|
| 1 | 1999–2007 | 24 | 2 | 17 |
| 2 | 2008–2016 | 25 | 2 | 18 |
| 3 | 2017–2026 | 22 | 2 | 15 |

Cross-region six-pivot windows excluded by the regional policy: 10. Their exact start indices remain in JSON.

## Linked hypothesis lookup

Each row below identifies a generated hypothesis and its exact parent requirement. The compact view shows the first hypothesis of each family per root and level, without ranking. JSON/CSV retain every executed context.

| Ref | Root | Level | Family hypothesis | Parent | Requirement | P004 | P005 | Unassigned trailing bars |
|---|---|---:|---|---|---|---|---|---:|
| H0001 | region-1-1 | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 319 |
| H0002 | region-1-1 | 0 | FLAT | — | — | not executed | not executed | 319 |
| H0007 | region-1-1 | 0 | TRIANGLE | — | — | not executed | not executed | 312 |
| H0008 | region-1-1 | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 312 |
| H0009 | region-1-1 | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_SATISFIED | UNRESOLVED | 312 |
| H0010 | region-1-1 | 1 | SINGLE_ZIGZAG | H0002 | R0004 | not executed | not executed | 1421 |
| H0011 | region-1-1 | 1 | FLAT | H0002 | R0004 | not executed | not executed | 1421 |
| H0044 | region-1-1 | 1 | TRIANGLE | H0007 | R0019 | not executed | not executed | 1415 |
| H0061 | region-1-1 | 1 | NORMAL_IMPULSE_PARTIAL | H0001 | R0001 | RULE_SATISFIED | UNRESOLVED | 1415 |
| H0067 | region-1-1 | 2 | SINGLE_ZIGZAG | H0010 | R0030 | not executed | not executed | 6857 |
| H0068 | region-1-1 | 2 | FLAT | H0010 | R0030 | not executed | not executed | 6857 |
| H0089 | region-1-2 | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 238 |
| H0090 | region-1-2 | 0 | FLAT | — | — | not executed | not executed | 238 |
| H0095 | region-1-2 | 0 | TRIANGLE | — | — | not executed | not executed | 228 |
| H0096 | region-1-2 | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 228 |
| H0097 | region-1-2 | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_SATISFIED | SUFFICIENT_CONDITION_ESTABLISHED | 228 |
| H0098 | region-1-2 | 1 | SINGLE_ZIGZAG | H0090 | R0062 | not executed | not executed | 1097 |
| H0099 | region-1-2 | 1 | FLAT | H0090 | R0062 | not executed | not executed | 1097 |
| H0114 | region-1-2 | 1 | TRIANGLE | H0095 | R0077 | not executed | not executed | 1090 |
| H0119 | region-1-2 | 1 | NORMAL_IMPULSE_PARTIAL | H0089 | R0059 | RULE_SATISFIED | UNRESOLVED | 1090 |
| H0120 | region-1-2 | 2 | SINGLE_ZIGZAG | H0099 | R0090 | not executed | not executed | 5352 |
| H0121 | region-1-2 | 2 | FLAT | H0099 | R0090 | not executed | not executed | 5352 |
| H0156 | region-1-2 | 2 | NORMAL_IMPULSE_PARTIAL | H0098 | R0087 | RULE_SATISFIED | SUFFICIENT_CONDITION_ESTABLISHED | 5347 |
| H0162 | region-2-1 | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 205 |
| H0163 | region-2-1 | 0 | FLAT | — | — | not executed | not executed | 205 |
| H0168 | region-2-1 | 0 | TRIANGLE | — | — | not executed | not executed | 201 |
| H0169 | region-2-1 | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 201 |
| H0170 | region-2-1 | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_VIOLATED | SUFFICIENT_CONDITION_ESTABLISHED | 201 |
| H0171 | region-2-1 | 1 | SINGLE_ZIGZAG | H0162 | R0124 | not executed | not executed | 933 |
| H0172 | region-2-1 | 1 | FLAT | H0162 | R0124 | not executed | not executed | 933 |
| H0215 | region-2-1 | 1 | TRIANGLE | H0168 | R0143 | not executed | not executed | 917 |
| H0216 | region-2-1 | 1 | NORMAL_IMPULSE_PARTIAL | H0162 | R0125 | RULE_SATISFIED | UNRESOLVED | 917 |
| H0219 | region-2-1 | 2 | SINGLE_ZIGZAG | H0173 | R0158 | not executed | not executed | 4511 |
| H0220 | region-2-1 | 2 | FLAT | H0173 | R0158 | not executed | not executed | 4511 |
| H0231 | region-2-1 | 2 | NORMAL_IMPULSE_PARTIAL | H0171 | R0153 | RULE_VIOLATED | UNRESOLVED | 4500 |
| H0233 | region-2-2 | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 135 |
| H0234 | region-2-2 | 0 | FLAT | — | — | not executed | not executed | 135 |
| H0239 | region-2-2 | 0 | TRIANGLE | — | — | not executed | not executed | 128 |
| H0240 | region-2-2 | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 128 |
| H0241 | region-2-2 | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_SATISFIED | UNRESOLVED | 128 |
| H0242 | region-2-2 | 1 | SINGLE_ZIGZAG | H0234 | R0184 | not executed | not executed | 609 |
| H0243 | region-2-2 | 1 | FLAT | H0234 | R0184 | not executed | not executed | 609 |
| H0280 | region-2-2 | 1 | TRIANGLE | H0239 | R0199 | not executed | not executed | 606 |
| H0292 | region-2-2 | 1 | NORMAL_IMPULSE_PARTIAL | H0233 | R0181 | RULE_VIOLATED | UNRESOLVED | 606 |
| H0296 | region-2-2 | 2 | SINGLE_ZIGZAG | H0243 | R0212 | not executed | not executed | 2954 |
| H0297 | region-2-2 | 2 | FLAT | H0243 | R0212 | not executed | not executed | 2954 |
| H0298 | region-3-1 | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 94 |
| H0299 | region-3-1 | 0 | FLAT | — | — | not executed | not executed | 94 |
| H0304 | region-3-1 | 0 | TRIANGLE | — | — | not executed | not executed | 88 |
| H0305 | region-3-1 | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 88 |
| H0306 | region-3-1 | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_VIOLATED | SUFFICIENT_CONDITION_ESTABLISHED | 88 |
| H0307 | region-3-1 | 1 | SINGLE_ZIGZAG | H0298 | R0234 | not executed | not executed | 479 |
| H0308 | region-3-1 | 1 | FLAT | H0298 | R0234 | not executed | not executed | 479 |
| H0339 | region-3-1 | 1 | TRIANGLE | H0304 | R0252 | not executed | not executed | 461 |
| H0344 | region-3-1 | 1 | NORMAL_IMPULSE_PARTIAL | H0300 | R0239 | RULE_VIOLATED | UNRESOLVED | 461 |
| H0345 | region-3-1 | 2 | SINGLE_ZIGZAG | H0307 | R0262 | not executed | not executed | 2345 |
| H0346 | region-3-1 | 2 | FLAT | H0307 | R0262 | not executed | not executed | 2345 |
| H0381 | region-3-1 | 2 | NORMAL_IMPULSE_PARTIAL | H0309 | R0267 | RULE_SATISFIED | UNRESOLVED | 2337 |
| H0386 | region-3-2 | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 7 |
| H0387 | region-3-2 | 0 | FLAT | — | — | not executed | not executed | 7 |
| H0392 | region-3-2 | 0 | TRIANGLE | — | — | not executed | not executed | 0 |
| H0393 | region-3-2 | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 0 |
| H0394 | region-3-2 | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_VIOLATED | UNRESOLVED | 0 |
| H0395 | region-3-2 | 1 | SINGLE_ZIGZAG | H0387 | R0300 | not executed | not executed | 75 |
| H0396 | region-3-2 | 1 | FLAT | H0387 | R0300 | not executed | not executed | 75 |
| H0423 | region-3-2 | 1 | TRIANGLE | H0392 | R0317 | not executed | not executed | 32 |
| H0431 | region-3-2 | 1 | NORMAL_IMPULSE_PARTIAL | H0386 | R0299 | RULE_VIOLATED | SUFFICIENT_CONDITION_ESTABLISHED | 32 |
| H0436 | region-3-2 | 2 | SINGLE_ZIGZAG | H0395 | R0326 | not executed | not executed | 376 |
| H0437 | region-3-2 | 2 | FLAT | H0395 | R0326 | not executed | not executed | 376 |
| H0440 | region-3-2 | 3 | SINGLE_ZIGZAG | H0436 | R0332 | not executed | not executed | 2662 |
| H0441 | region-3-2 | 3 | FLAT | H0436 | R0332 | not executed | not executed | 2662 |
| H0458 | region-3-2 | 3 | NORMAL_IMPULSE_PARTIAL | H0436 | R0331 | RULE_SATISFIED | UNRESOLVED | 2678 |
| H0459 | full-range-coarsened | 0 | SINGLE_ZIGZAG | — | — | not executed | not executed | 148 |
| H0460 | full-range-coarsened | 0 | FLAT | — | — | not executed | not executed | 148 |
| H0465 | full-range-coarsened | 0 | TRIANGLE | — | — | not executed | not executed | 0 |
| H0466 | full-range-coarsened | 0 | ENDING_DIAGONAL | — | — | not executed | not executed | 0 |
| H0467 | full-range-coarsened | 0 | NORMAL_IMPULSE_PARTIAL | — | — | RULE_SATISFIED | UNRESOLVED | 0 |
| H0468 | full-range-coarsened | 1 | SINGLE_ZIGZAG | H0459 | R0338 | not executed | not executed | 1188 |
| H0469 | full-range-coarsened | 1 | FLAT | H0459 | R0338 | not executed | not executed | 1188 |
| H0528 | full-range-coarsened | 1 | TRIANGLE | H0465 | R0355 | not executed | not executed | 1415 |
| H0557 | full-range-coarsened | 1 | NORMAL_IMPULSE_PARTIAL | H0459 | R0337 | RULE_SATISFIED | UNRESOLVED | 1415 |
| H0566 | full-range-coarsened | 2 | SINGLE_ZIGZAG | H0468 | R0366 | not executed | not executed | 5755 |
| H0567 | full-range-coarsened | 2 | FLAT | H0468 | R0366 | not executed | not executed | 5755 |
| H0584 | full-range-coarsened | 2 | NORMAL_IMPULSE_PARTIAL | H0470 | R0371 | RULE_VIOLATED | SUFFICIENT_CONDITION_ESTABLISHED | 5751 |

## Proposed components

Prices below are exact transported HIGH/LOW observations rounded only for readable display; JSON/CSV preserve represented values. Labels are hypothesis slots, not orthodox endpoints. Direction for generic families is unassigned. No row is a forecast.

### H0001 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-01 | 0.033333 | 1999-08-01 | 0.059115 |
| child_2 | 1999-08-01 | 0.059115 | 1999-09-01 | 0.034896 |
| child_3 | 1999-09-01 | 0.034896 | 2000-03-01 | 0.3125 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0007 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-01 | 0.033333 | 1999-08-01 | 0.059115 |
| child_2 | 1999-08-01 | 0.059115 | 1999-09-01 | 0.034896 |
| child_3 | 1999-09-01 | 0.034896 | 2000-03-01 | 0.3125 |
| child_4 | 2000-03-01 | 0.3125 | 2000-06-01 | 0.366667 |
| child_5 | 2000-06-01 | 0.366667 | 2000-10-01 | 0.359375 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0009 — NORMAL_IMPULSE_PARTIAL (1mo, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 1999-04-01 | 0.033333 | 1999-08-01 | 0.059115 |
| 2 | 1999-08-01 | 0.059115 | 1999-09-01 | 0.034896 |
| 3 | 1999-09-01 | 0.034896 | 2000-03-01 | 0.3125 |
| 4 | 2000-03-01 | 0.3125 | 2000-06-01 | 0.366667 |
| 5 | 2000-06-01 | 0.366667 | 2000-10-01 | 0.359375 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0010 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-26 | 0.033333 | 1999-05-17 | 0.044531 |
| child_2 | 1999-05-17 | 0.044531 | 1999-06-07 | 0.038281 |
| child_3 | 1999-06-07 | 0.038281 | 1999-06-14 | 0.034115 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0044 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-26 | 0.033333 | 1999-05-17 | 0.044531 |
| child_2 | 1999-05-17 | 0.044531 | 1999-06-07 | 0.038281 |
| child_3 | 1999-06-07 | 0.038281 | 1999-06-14 | 0.034115 |
| child_4 | 1999-06-14 | 0.034115 | 1999-07-12 | 0.048177 |
| child_5 | 1999-07-12 | 0.048177 | 1999-07-26 | 0.040104 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0061 — NORMAL_IMPULSE_PARTIAL (1wk, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 1999-04-26 | 0.033333 | 1999-05-17 | 0.044531 |
| 2 | 1999-05-17 | 0.044531 | 1999-06-07 | 0.038281 |
| 3 | 1999-06-07 | 0.038281 | 1999-06-14 | 0.034115 |
| 4 | 1999-06-14 | 0.034115 | 1999-07-12 | 0.048177 |
| 5 | 1999-07-12 | 0.048177 | 1999-07-26 | 0.040104 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0067 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-05-19 | 0.044531 | 1999-05-21 | 0.034375 |
| child_2 | 1999-05-21 | 0.034375 | 1999-05-26 | 0.03724 |
| child_3 | 1999-05-26 | 0.03724 | 1999-06-02 | 0.034375 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0089 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2005-04-01 | 0.174333 | 2006-05-01 | 0.531333 |
| child_2 | 2006-05-01 | 0.531333 | 2006-07-01 | 0.286167 |
| child_3 | 2006-07-01 | 0.286167 | 2006-12-01 | 0.649333 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0095 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2005-04-01 | 0.174333 | 2006-05-01 | 0.531333 |
| child_2 | 2006-05-01 | 0.531333 | 2006-07-01 | 0.286167 |
| child_3 | 2006-07-01 | 0.286167 | 2006-12-01 | 0.649333 |
| child_4 | 2006-12-01 | 0.649333 | 2007-03-01 | 0.467333 |
| child_5 | 2007-03-01 | 0.467333 | 2007-10-01 | 0.99175 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0097 — NORMAL_IMPULSE_PARTIAL (1mo, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2005-04-01 | 0.174333 | 2006-05-01 | 0.531333 |
| 2 | 2006-05-01 | 0.531333 | 2006-07-01 | 0.286167 |
| 3 | 2006-07-01 | 0.286167 | 2006-12-01 | 0.649333 |
| 4 | 2006-12-01 | 0.649333 | 2007-03-01 | 0.467333 |
| 5 | 2007-03-01 | 0.467333 | 2007-10-01 | 0.99175 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0098 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2005-04-25 | 0.174333 | 2005-07-11 | 0.244167 |
| child_2 | 2005-07-11 | 0.244167 | 2005-07-25 | 0.211833 |
| child_3 | 2005-07-25 | 0.211833 | 2005-08-29 | 0.236833 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0114 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2005-04-25 | 0.174333 | 2005-07-11 | 0.244167 |
| child_2 | 2005-07-11 | 0.244167 | 2005-07-25 | 0.211833 |
| child_3 | 2005-07-25 | 0.211833 | 2005-08-29 | 0.236833 |
| child_4 | 2005-08-29 | 0.236833 | 2005-10-03 | 0.299583 |
| child_5 | 2005-10-03 | 0.299583 | 2005-10-17 | 0.25425 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0119 — NORMAL_IMPULSE_PARTIAL (1wk, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2005-04-25 | 0.174333 | 2005-07-11 | 0.244167 |
| 2 | 2005-07-11 | 0.244167 | 2005-07-25 | 0.211833 |
| 3 | 2005-07-25 | 0.211833 | 2005-08-29 | 0.236833 |
| 4 | 2005-08-29 | 0.236833 | 2005-10-03 | 0.299583 |
| 5 | 2005-10-03 | 0.299583 | 2005-10-17 | 0.25425 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0120 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2005-04-29 | 0.174333 | 2005-05-09 | 0.198 |
| child_2 | 2005-05-09 | 0.198 | 2005-05-11 | 0.1855 |
| child_3 | 2005-05-11 | 0.1855 | 2005-05-26 | 0.232583 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0156 — NORMAL_IMPULSE_PARTIAL (1d, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2005-04-29 | 0.174333 | 2005-05-09 | 0.198 |
| 2 | 2005-05-09 | 0.198 | 2005-05-11 | 0.1855 |
| 3 | 2005-05-11 | 0.1855 | 2005-05-26 | 0.232583 |
| 4 | 2005-05-26 | 0.232583 | 2005-06-01 | 0.221667 |
| 5 | 2005-06-01 | 0.221667 | 2005-06-03 | 0.23775 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0162 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2008-03-01 | 0.43275 | 2008-06-01 | 0.63375 |
| child_2 | 2008-06-01 | 0.63375 | 2008-11-01 | 0.14375 |
| child_3 | 2008-11-01 | 0.14375 | 2009-09-01 | 0.4145 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0168 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2008-03-01 | 0.43275 | 2008-06-01 | 0.63375 |
| child_2 | 2008-06-01 | 0.63375 | 2008-11-01 | 0.14375 |
| child_3 | 2008-11-01 | 0.14375 | 2009-09-01 | 0.4145 |
| child_4 | 2009-09-01 | 0.4145 | 2009-11-01 | 0.289 |
| child_5 | 2009-11-01 | 0.289 | 2010-01-01 | 0.474 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0170 — NORMAL_IMPULSE_PARTIAL (1mo, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2008-03-01 | 0.43275 | 2008-06-01 | 0.63375 |
| 2 | 2008-06-01 | 0.63375 | 2008-11-01 | 0.14375 |
| 3 | 2008-11-01 | 0.14375 | 2009-09-01 | 0.4145 |
| 4 | 2009-09-01 | 0.4145 | 2009-11-01 | 0.289 |
| 5 | 2009-11-01 | 0.289 | 2010-01-01 | 0.474 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT, EXACT_HYPOTHESIS_REJECTED_P004.

### H0171 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2008-08-04 | 0.26375 | 2008-08-18 | 0.353 |
| child_2 | 2008-08-18 | 0.353 | 2008-09-15 | 0.22 |
| child_3 | 2008-09-15 | 0.22 | 2008-10-20 | 0.14925 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0215 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2008-11-17 | 0.14375 | 2008-12-15 | 0.23625 |
| child_2 | 2008-12-15 | 0.23625 | 2008-12-29 | 0.178 |
| child_3 | 2008-12-29 | 0.178 | 2009-01-05 | 0.23575 |
| child_4 | 2009-01-05 | 0.23575 | 2009-01-19 | 0.177 |
| child_5 | 2009-01-19 | 0.177 | 2009-02-09 | 0.24925 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0216 — NORMAL_IMPULSE_PARTIAL (1wk, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2008-11-17 | 0.14375 | 2008-12-15 | 0.23625 |
| 2 | 2008-12-15 | 0.23625 | 2008-12-29 | 0.178 |
| 3 | 2008-12-29 | 0.178 | 2009-01-05 | 0.23575 |
| 4 | 2009-01-05 | 0.23575 | 2009-01-19 | 0.177 |
| 5 | 2009-01-19 | 0.177 | 2009-02-09 | 0.24925 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0219 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2008-09-22 | 0.29125 | 2008-09-24 | 0.26625 |
| child_2 | 2008-09-24 | 0.26625 | 2008-09-26 | 0.29425 |
| child_3 | 2008-09-26 | 0.29425 | 2008-09-29 | 0.25 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0231 — NORMAL_IMPULSE_PARTIAL (1d, DOWN)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2008-09-22 | 0.29125 | 2008-09-24 | 0.26625 |
| 2 | 2008-09-24 | 0.26625 | 2008-09-26 | 0.29425 |
| 3 | 2008-09-26 | 0.29425 | 2008-09-29 | 0.25 |
| 4 | 2008-09-29 | 0.25 | 2008-10-10 | 0.157 |
| 5 | 2008-10-10 | 0.157 | 2008-10-14 | 0.21 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, EXACT_HYPOTHESIS_REJECTED_P004.

### H0233 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2014-10-01 | 0.41925 | 2015-02-01 | 0.4735 |
| child_2 | 2015-02-01 | 0.4735 | 2015-03-01 | 0.59025 |
| child_3 | 2015-03-01 | 0.59025 | 2015-07-01 | 0.47725 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0239 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2014-10-01 | 0.41925 | 2015-02-01 | 0.4735 |
| child_2 | 2015-02-01 | 0.4735 | 2015-03-01 | 0.59025 |
| child_3 | 2015-03-01 | 0.59025 | 2015-07-01 | 0.47725 |
| child_4 | 2015-07-01 | 0.47725 | 2015-12-01 | 0.8485 |
| child_5 | 2015-12-01 | 0.8485 | 2016-02-01 | 0.61875 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0241 — NORMAL_IMPULSE_PARTIAL (1mo, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2014-10-01 | 0.41925 | 2015-02-01 | 0.4735 |
| 2 | 2015-02-01 | 0.4735 | 2015-03-01 | 0.59025 |
| 3 | 2015-03-01 | 0.59025 | 2015-07-01 | 0.47725 |
| 4 | 2015-07-01 | 0.47725 | 2015-12-01 | 0.8485 |
| 5 | 2015-12-01 | 0.8485 | 2016-02-01 | 0.61875 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0242 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2014-11-03 | 0.51725 | 2014-12-08 | 0.53125 |
| child_2 | 2014-12-08 | 0.53125 | 2014-12-15 | 0.4775 |
| child_3 | 2014-12-15 | 0.4775 | 2015-01-05 | 0.477 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0280 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2014-11-03 | 0.51725 | 2014-12-08 | 0.53125 |
| child_2 | 2014-12-08 | 0.53125 | 2014-12-15 | 0.4775 |
| child_3 | 2014-12-15 | 0.4775 | 2015-01-05 | 0.477 |
| child_4 | 2015-01-05 | 0.477 | 2015-01-19 | 0.51875 |
| child_5 | 2015-01-19 | 0.51875 | 2015-01-26 | 0.47925 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0292 — NORMAL_IMPULSE_PARTIAL (1wk, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2014-11-03 | 0.51725 | 2014-12-08 | 0.53125 |
| 2 | 2014-12-08 | 0.53125 | 2014-12-15 | 0.4775 |
| 3 | 2014-12-15 | 0.4775 | 2015-01-05 | 0.477 |
| 4 | 2015-01-05 | 0.477 | 2015-01-19 | 0.51875 |
| 5 | 2015-01-19 | 0.51875 | 2015-01-26 | 0.47925 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, EXACT_HYPOTHESIS_REJECTED_P004.

### H0296 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2014-11-14 | 0.4845 | 2014-11-28 | 0.52725 |
| child_2 | 2014-11-28 | 0.52725 | 2014-12-02 | 0.50925 |
| child_3 | 2014-12-02 | 0.50925 | 2014-12-04 | 0.52975 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0298 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2017-02-01 | 3.023 | 2017-03-01 | 2.37925 |
| child_2 | 2017-03-01 | 2.37925 | 2018-10-01 | 7.319 |
| child_3 | 2018-10-01 | 7.319 | 2018-12-01 | 3.1115 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0304 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2017-02-01 | 3.023 | 2017-03-01 | 2.37925 |
| child_2 | 2017-03-01 | 2.37925 | 2018-10-01 | 7.319 |
| child_3 | 2018-10-01 | 7.319 | 2018-12-01 | 3.1115 |
| child_4 | 2018-12-01 | 3.1115 | 2019-04-01 | 4.83675 |
| child_5 | 2019-04-01 | 4.83675 | 2019-06-01 | 3.315 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0306 — NORMAL_IMPULSE_PARTIAL (1mo, DOWN)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2017-02-01 | 3.023 | 2017-03-01 | 2.37925 |
| 2 | 2017-03-01 | 2.37925 | 2018-10-01 | 7.319 |
| 3 | 2018-10-01 | 7.319 | 2018-12-01 | 3.1115 |
| 4 | 2018-12-01 | 3.1115 | 2019-04-01 | 4.83675 |
| 5 | 2019-04-01 | 4.83675 | 2019-06-01 | 3.315 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT, EXACT_HYPOTHESIS_REJECTED_P004.

### H0307 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2017-03-27 | 2.75 | 2017-04-10 | 2.38725 |
| child_2 | 2017-04-10 | 2.38725 | 2017-06-05 | 4.2125 |
| child_3 | 2017-06-05 | 4.2125 | 2017-07-03 | 3.4645 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0339 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2017-03-27 | 2.75 | 2017-04-10 | 2.38725 |
| child_2 | 2017-04-10 | 2.38725 | 2017-06-05 | 4.2125 |
| child_3 | 2017-06-05 | 4.2125 | 2017-07-03 | 3.4645 |
| child_4 | 2017-07-03 | 3.4645 | 2017-09-18 | 4.78 |
| child_5 | 2017-09-18 | 4.78 | 2017-11-06 | 5.46675 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0344 — NORMAL_IMPULSE_PARTIAL (1wk, DOWN)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2017-03-27 | 2.75 | 2017-04-10 | 2.38725 |
| 2 | 2017-04-10 | 2.38725 | 2017-06-05 | 4.2125 |
| 3 | 2017-06-05 | 4.2125 | 2017-07-03 | 3.4645 |
| 4 | 2017-07-03 | 3.4645 | 2017-09-18 | 4.78 |
| 5 | 2017-09-18 | 4.78 | 2017-11-06 | 5.46675 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, EXACT_HYPOTHESIS_REJECTED_P004.

### H0345 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2017-04-13 | 2.38725 | 2017-05-01 | 2.67125 |
| child_2 | 2017-05-01 | 2.67125 | 2017-05-02 | 2.564 |
| child_3 | 2017-05-02 | 2.564 | 2017-05-08 | 2.55775 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0381 — NORMAL_IMPULSE_PARTIAL (1d, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2017-04-13 | 2.38725 | 2017-05-01 | 2.67125 |
| 2 | 2017-05-01 | 2.67125 | 2017-05-02 | 2.564 |
| 3 | 2017-05-02 | 2.564 | 2017-05-08 | 2.55775 |
| 4 | 2017-05-08 | 2.55775 | 2017-05-16 | 3.436 |
| 5 | 2017-05-16 | 3.436 | 2017-05-18 | 3.17625 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0386 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2025-01-01 | 153.13 | 2025-04-01 | 86.62 |
| child_2 | 2025-04-01 | 86.62 | 2025-10-01 | 212.19 |
| child_3 | 2025-10-01 | 212.19 | 2026-03-01 | 164.27 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0392 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2025-01-01 | 153.13 | 2025-04-01 | 86.62 |
| child_2 | 2025-04-01 | 86.62 | 2025-10-01 | 212.19 |
| child_3 | 2025-10-01 | 212.19 | 2026-03-01 | 164.27 |
| child_4 | 2026-03-01 | 164.27 | 2026-05-01 | 236.54 |
| child_5 | 2026-05-01 | 236.54 | 2026-09-04 | 234.76 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, NO_LINKED_PARENT_REQUIREMENT.

### H0394 — NORMAL_IMPULSE_PARTIAL (1mo, DOWN)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2025-01-01 | 153.13 | 2025-04-01 | 86.62 |
| 2 | 2025-04-01 | 86.62 | 2025-10-01 | 212.19 |
| 3 | 2025-10-01 | 212.19 | 2026-03-01 | 164.27 |
| 4 | 2026-03-01 | 164.27 | 2026-05-01 | 236.54 |
| 5 | 2026-05-01 | 236.54 | 2026-09-04 | 234.76 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, NO_LINKED_PARENT_REQUIREMENT, EXACT_HYPOTHESIS_REJECTED_P004.

### H0395 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2025-02-03 | 113.01 | 2025-02-17 | 143.44 |
| child_2 | 2025-02-17 | 143.44 | 2025-03-10 | 104.77 |
| child_3 | 2025-03-10 | 104.77 | 2025-03-31 | 92.11 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0423 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2025-10-20 | 176.76 | 2025-10-27 | 212.19 |
| child_2 | 2025-10-27 | 212.19 | 2025-11-24 | 169.55 |
| child_3 | 2025-11-24 | 169.55 | 2025-12-15 | 170.31 |
| child_4 | 2025-12-15 | 170.31 | 2026-01-05 | 193.63 |
| child_5 | 2026-01-05 | 193.63 | 2026-01-26 | 194.49 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0431 — NORMAL_IMPULSE_PARTIAL (1wk, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2025-10-20 | 176.76 | 2025-10-27 | 212.19 |
| 2 | 2025-10-27 | 212.19 | 2025-11-24 | 169.55 |
| 3 | 2025-11-24 | 169.55 | 2025-12-15 | 170.31 |
| 4 | 2025-12-15 | 170.31 | 2026-01-05 | 193.63 |
| 5 | 2026-01-05 | 193.63 | 2026-01-26 | 194.49 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, EXACT_HYPOTHESIS_REJECTED_P004.

### H0436 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2025-02-21 | 141.46 | 2025-02-27 | 135.01 |
| child_2 | 2025-02-27 | 135.01 | 2025-03-04 | 110.11 |
| child_3 | 2025-03-04 | 110.11 | 2025-03-07 | 107.56 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0440 — SINGLE_ZIGZAG (1h, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2025-02-27 | 128.45 | 2025-02-28 | 116.41 |
| child_2 | 2025-02-28 | 116.41 | 2025-02-28 | 123.7 |
| child_3 | 2025-02-28 | 123.7 | 2025-02-28 | 118.845 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0458 — NORMAL_IMPULSE_PARTIAL (1h, DOWN)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2025-02-24 | 138.59 | 2025-02-24 | 130.61 |
| 2 | 2025-02-24 | 130.61 | 2025-02-25 | 124.44 |
| 3 | 2025-02-25 | 124.44 | 2025-02-25 | 129.89 |
| 4 | 2025-02-25 | 129.89 | 2025-02-25 | 126.19 |
| 5 | 2025-02-25 | 126.19 | 2025-02-26 | 133.73 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0459 — SINGLE_ZIGZAG (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-01 | 0.033333 | 2003-08-01 | 0.127167 |
| child_2 | 2003-08-01 | 0.127167 | 2009-11-01 | 0.289 |
| child_3 | 2009-11-01 | 0.289 | 2014-06-01 | 0.49325 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, NO_LINKED_PARENT_REQUIREMENT.

### H0465 — TRIANGLE (1mo, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-01 | 0.033333 | 2003-08-01 | 0.127167 |
| child_2 | 2003-08-01 | 0.127167 | 2009-11-01 | 0.289 |
| child_3 | 2009-11-01 | 0.289 | 2014-06-01 | 0.49325 |
| child_4 | 2014-06-01 | 0.49325 | 2020-03-01 | 4.517 |
| child_5 | 2020-03-01 | 4.517 | 2026-09-04 | 234.76 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, NO_LINKED_PARENT_REQUIREMENT.

### H0467 — NORMAL_IMPULSE_PARTIAL (1mo, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 1999-04-01 | 0.033333 | 2003-08-01 | 0.127167 |
| 2 | 2003-08-01 | 0.127167 | 2009-11-01 | 0.289 |
| 3 | 2009-11-01 | 0.289 | 2014-06-01 | 0.49325 |
| 4 | 2014-06-01 | 0.49325 | 2020-03-01 | 4.517 |
| 5 | 2020-03-01 | 4.517 | 2026-09-04 | 234.76 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, NO_LINKED_PARENT_REQUIREMENT.

### H0468 — SINGLE_ZIGZAG (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2003-09-08 | 0.178917 | 2003-09-29 | 0.130833 |
| child_2 | 2003-09-29 | 0.130833 | 2003-11-10 | 0.184333 |
| child_3 | 2003-11-10 | 0.184333 | 2003-12-01 | 0.185 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0528 — TRIANGLE (1wk, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 1999-04-26 | 0.033333 | 1999-05-17 | 0.044531 |
| child_2 | 1999-05-17 | 0.044531 | 1999-06-07 | 0.038281 |
| child_3 | 1999-06-07 | 0.038281 | 1999-06-14 | 0.034115 |
| child_4 | 1999-06-14 | 0.034115 | 1999-07-12 | 0.048177 |
| child_5 | 1999-07-12 | 0.048177 | 1999-07-26 | 0.040104 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0557 — NORMAL_IMPULSE_PARTIAL (1wk, UP)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 1999-04-26 | 0.033333 | 1999-05-17 | 0.044531 |
| 2 | 1999-05-17 | 0.044531 | 1999-06-07 | 0.038281 |
| 3 | 1999-06-07 | 0.038281 | 1999-06-14 | 0.034115 |
| 4 | 1999-06-14 | 0.034115 | 1999-07-12 | 0.048177 |
| 5 | 1999-07-12 | 0.048177 | 1999-07-26 | 0.040104 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0566 — SINGLE_ZIGZAG (1d, NOT_ASSIGNED)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| child_1 | 2003-10-03 | 0.143333 | 2003-10-08 | 0.13425 |
| child_2 | 2003-10-08 | 0.13425 | 2003-10-15 | 0.14775 |
| child_3 | 2003-10-15 | 0.14775 | 2003-10-20 | 0.138083 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS.

### H0584 — NORMAL_IMPULSE_PARTIAL (1d, DOWN)

| Slot | Start UTC | Price | End UTC | Price |
|---|---|---:|---|---:|
| 1 | 2003-10-03 | 0.143333 | 2003-10-08 | 0.13425 |
| 2 | 2003-10-08 | 0.13425 | 2003-10-15 | 0.14775 |
| 3 | 2003-10-15 | 0.14775 | 2003-10-20 | 0.138083 |
| 4 | 2003-10-20 | 0.138083 | 2003-10-21 | 0.149 |
| 5 | 2003-10-21 | 0.149 | 2003-10-24 | 0.140333 |

Current position: unresolved. NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE, FAMILY_PROOF_UNRESOLVED, TRAILING_UNASSIGNED_OBSERVATIONS, EXACT_HYPOTHESIS_REJECTED_P004.

## Limits and unresolved dependencies

Every P004 rejection remains local and fatal even if P005 establishes sufficiency. All internal requirements remain unsatisfied; cardinality and partial checks cannot supply a family certificate.

- P006 remains frozen/unresolved/conflicted: orthodox endpoints, scope, equality and timing are not resolved.
- P005 establishes percentage sufficiency only, not full P005 or impulse validity.
- SOURCE_DERIVED_BASE_CASE_NOT_FOUND: reviewed children do not supply positive family proof.
- Flat/Triangle geometry freezes remain intact; cardinality is not subtype or full-family validation.

Branch budgets, no-child cases and missing finer history are listed below. An unvisited branch is not an impossible family. Exact unvisited requirement IDs remain in JSON.

| Root | Level | Child bundles | Expanded onward | Unvisited | Coverage | Stop |
|---|---:|---:|---:|---:|---|---|
| region-1-1 | 1 | 10 | 1 | 9 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| region-1-1 | 2 | 6 | 1 | 5 | {'FULL_WINDOW_COVERAGE': 18} | BRANCH_BUDGET |
| region-1-1 | 3 | 0 | 0 | 0 | {'NO_WINDOW_COVERAGE': 12} | NO_COMPATIBLE_CHILD_BUNDLE |
| region-1-2 | 1 | 6 | 1 | 5 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| region-1-2 | 2 | 6 | 1 | 5 | {'FULL_WINDOW_COVERAGE': 18} | BRANCH_BUDGET |
| region-1-2 | 3 | 0 | 0 | 0 | {'NO_WINDOW_COVERAGE': 18} | NO_COMPATIBLE_CHILD_BUNDLE |
| region-2-1 | 1 | 10 | 1 | 9 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| region-2-1 | 2 | 2 | 1 | 1 | {'FULL_WINDOW_COVERAGE': 12} | BRANCH_BUDGET |
| region-2-1 | 3 | 0 | 0 | 0 | {'NO_WINDOW_COVERAGE': 18} | NO_COMPATIBLE_CHILD_BUNDLE |
| region-2-2 | 1 | 9 | 1 | 8 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| region-2-2 | 2 | 1 | 1 | 0 | {'FULL_WINDOW_COVERAGE': 18} | BRANCH_BUDGET |
| region-2-2 | 3 | 0 | 0 | 0 | {'NO_WINDOW_COVERAGE': 6} | NO_COMPATIBLE_CHILD_BUNDLE |
| region-3-1 | 1 | 7 | 1 | 6 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| region-3-1 | 2 | 8 | 1 | 7 | {'FULL_WINDOW_COVERAGE': 18} | BRANCH_BUDGET |
| region-3-1 | 3 | 0 | 0 | 0 | {'NO_WINDOW_COVERAGE': 18} | NO_COMPATIBLE_CHILD_BUNDLE |
| region-3-2 | 1 | 7 | 1 | 6 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| region-3-2 | 2 | 2 | 1 | 1 | {'FULL_WINDOW_COVERAGE': 6} | BRANCH_BUDGET |
| region-3-2 | 3 | 3 | 0 | 3 | {'FULL_WINDOW_COVERAGE': 6} | LEVEL_BUDGET |
| full-range-coarsened | 1 | 14 | 1 | 13 | {'FULL_WINDOW_COVERAGE': 28} | BRANCH_BUDGET |
| full-range-coarsened | 2 | 3 | 1 | 2 | {'FULL_WINDOW_COVERAGE': 18} | BRANCH_BUDGET |
| full-range-coarsened | 3 | 0 | 0 | 0 | {'NO_WINDOW_COVERAGE': 18} | NO_COMPATIBLE_CHILD_BUNDLE |

## Reproducibility and next decision

Use the baseline README command and unchanged preserved inputs. Review the unvisited historical regions and branch budgets before authorizing broader computation. Exact-family proof and a developing-position contract require separate authority; this run does not resolve those gates.
