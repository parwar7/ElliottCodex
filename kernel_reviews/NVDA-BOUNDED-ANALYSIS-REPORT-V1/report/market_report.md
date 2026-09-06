# NVDA bounded candidate analysis

Candidate analysis only: no complete validated Elliott count or directional forecast is established.

## Summary

This executed search retained 194 family/partial hypotheses across 45 endpoint-sequence groups. Repeated sequences are not independent market episodes. Rejection applies only to the named hypothesis; other interpretations are not thereby validated.

Of 17 Normal Impulse partial hypotheses, 7 are rejected by P004. P005 percentage sufficiency is established in 3; 3 of these still have a fatal P004 result. None establishes a complete family. The remaining family-bridge results concern supplied cardinality only.

P004 tests the supplied Wave 2/origin relationship. P005 reports only percentage sufficiency. Neither establishes a completed impulse, exact degree, or validated family. No preferred/alternative ranking is made.

## Data dates and scope

Data mode: **FRESH_CAPTURE**. Capture times below are actual retrieval times, not the time this report was replayed.

| View | Bars | First bar UTC | Latest bar UTC | Actual capture UTC |
| --- | ---: | --- | --- | --- |
| 1mo | 334 | 1999-01-01T05:00:00+00:00 | 2026-09-04T20:00:00+00:00 | 2026-09-06T23:20:10.981853+00:00 |
| 1wk | 1443 | 1999-01-18T05:00:00+00:00 | 2026-09-04T20:00:00+00:00 | 2026-09-06T23:20:11.217403+00:00 |
| 1d | 6948 | 1999-01-22T14:30:00+00:00 | 2026-09-04T13:30:00+00:00 | 2026-09-06T23:20:11.684827+00:00 |
| 1h | 3486 | 2024-09-09T13:30:00+00:00 | 2026-09-04T20:00:00+00:00 | 2026-09-06T23:20:12.282516+00:00 |

Instrument: NVIDIA (NVDA). Provider currency: USD. Prices retain Yahoo quote OHLC values, not adjusted-close substitutions. Timestamps locate provider bars, not necessarily the instant of an intrabar extreme or a completed Elliott endpoint.

Monthly→Weekly, Weekly→Daily and Daily→1H are explicitly selected observation pairs, not Elliott degrees. Exactly one child layer is searched. Latest six parent pivots and earliest six child pivots, zero skips, maximum ten candidates per window and 500 child candidates per scope. Complete limits and diagnostics are retained in JSON and configuration.json. The beginning of available data is not assigned a wave origin.

## Evaluated evidence

The family bridge tests direct-child cardinality only. Its supplied-scope result is not family validity. Normal Impulse partial evaluation is additional to the four-family bridge.

| Parent scope / path | Family | Hypotheses | P004 outcomes or cardinality scope | P005 sufficiency / unresolved |
| --- | --- | ---: | --- | --- |
| 1mo / parent | SINGLE_ZIGZAG | 3 | cardinality scope reviewed: 3 | Not applicable |
| 1mo / parent | FLAT | 3 | cardinality scope reviewed: 3 | Not applicable |
| 1mo / parent | TRIANGLE | 1 | cardinality scope reviewed: 1 | Not applicable |
| 1mo / parent | ENDING_DIAGONAL | 1 | cardinality scope reviewed: 1 | Not applicable |
| 1mo / parent | NORMAL_IMPULSE_PARTIAL | 1 | violated: 1 | unresolved: 1 |
| 1mo / child | SINGLE_ZIGZAG | 17 | cardinality scope reviewed: 17 | Not applicable |
| 1mo / child | FLAT | 17 | cardinality scope reviewed: 17 | Not applicable |
| 1mo / child | TRIANGLE | 2 | cardinality scope reviewed: 2 | Not applicable |
| 1mo / child | NORMAL_IMPULSE_PARTIAL | 5 | satisfied: 2; violated: 3 | sufficiency established: 3; unresolved: 2 |
| 1wk / parent | SINGLE_ZIGZAG | 3 | cardinality scope reviewed: 3 | Not applicable |
| 1wk / parent | FLAT | 3 | cardinality scope reviewed: 3 | Not applicable |
| 1wk / parent | TRIANGLE | 1 | cardinality scope reviewed: 1 | Not applicable |
| 1wk / parent | ENDING_DIAGONAL | 1 | cardinality scope reviewed: 1 | Not applicable |
| 1wk / parent | NORMAL_IMPULSE_PARTIAL | 1 | satisfied: 1 | unresolved: 1 |
| 1wk / child | SINGLE_ZIGZAG | 14 | cardinality scope reviewed: 14 | Not applicable |
| 1wk / child | FLAT | 14 | cardinality scope reviewed: 14 | Not applicable |
| 1d / parent | SINGLE_ZIGZAG | 3 | cardinality scope reviewed: 3 | Not applicable |
| 1d / parent | FLAT | 3 | cardinality scope reviewed: 3 | Not applicable |
| 1d / parent | TRIANGLE | 1 | cardinality scope reviewed: 1 | Not applicable |
| 1d / parent | ENDING_DIAGONAL | 1 | cardinality scope reviewed: 1 | Not applicable |
| 1d / parent | NORMAL_IMPULSE_PARTIAL | 1 | violated: 1 | unresolved: 1 |
| 1d / child | SINGLE_ZIGZAG | 42 | cardinality scope reviewed: 42 | Not applicable |
| 1d / child | FLAT | 42 | cardinality scope reviewed: 42 | Not applicable |
| 1d / child | TRIANGLE | 5 | cardinality scope reviewed: 5 | Not applicable |
| 1d / child | NORMAL_IMPULSE_PARTIAL | 9 | satisfied: 7; violated: 2 | unresolved: 9 |

## Proposed structures: bounded display

At most 2 sequence groups per parent scope/path are shown, in deterministic generation order, not quality order: the first group of each neutral shape. Every hypothesis, including omitted display rows and rejected cases, remains in JSON/CSV. Compact H/C aliases resolve to exact hypothesis/candidate IDs in candidates.csv. Numeric roles belong only to the Normal Impulse hypothesis; other families retain neutral child slots.

### 1mo / parent — sequence 2be2e183f830

Observed in 1mo; snapshot prefix 5f2964509cad (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0001 | H0001 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0001 | H0002 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| child_1 | 2025-01-01T05:00:00+00:00 / high / 153.1300048828125 (CONFIRMED_BY_GEOMETRY) | 2025-04-01T04:00:00+00:00 / low / 86.62000274658203 (CONFIRMED_BY_GEOMETRY) |
| child_2 | 2025-04-01T04:00:00+00:00 / low / 86.62000274658203 (CONFIRMED_BY_GEOMETRY) | 2025-10-01T04:00:00+00:00 / high / 212.19000244140625 (CONFIRMED_BY_GEOMETRY) |
| child_3 | 2025-10-01T04:00:00+00:00 / high / 212.19000244140625 (CONFIRMED_BY_GEOMETRY) | 2026-03-01T05:00:00+00:00 / low / 164.27000427246094 (CONFIRMED_BY_GEOMETRY) |

### 1mo / parent — sequence 2c2865d05ccc

Observed in 1mo; snapshot prefix 5f2964509cad (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0004 | H0007 | TRIANGLE | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0004 | H0008 | ENDING_DIAGONAL | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0004 | H0009 | NORMAL_IMPULSE_PARTIAL | DOWN | REJECTED_EXACT_HYPOTHESIS_P004; P004 RULE_VIOLATED; P005 UNRESOLVED: DEVELOPING_REQUIRED_ENDPOINT |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| 1 | 2025-01-01T05:00:00+00:00 / high / 153.1300048828125 (CONFIRMED_BY_GEOMETRY) | 2025-04-01T04:00:00+00:00 / low / 86.62000274658203 (CONFIRMED_BY_GEOMETRY) |
| 2 | 2025-04-01T04:00:00+00:00 / low / 86.62000274658203 (CONFIRMED_BY_GEOMETRY) | 2025-10-01T04:00:00+00:00 / high / 212.19000244140625 (CONFIRMED_BY_GEOMETRY) |
| 3 | 2025-10-01T04:00:00+00:00 / high / 212.19000244140625 (CONFIRMED_BY_GEOMETRY) | 2026-03-01T05:00:00+00:00 / low / 164.27000427246094 (CONFIRMED_BY_GEOMETRY) |
| 4 | 2026-03-01T05:00:00+00:00 / low / 164.27000427246094 (CONFIRMED_BY_GEOMETRY) | 2026-05-01T04:00:00+00:00 / high / 236.5399932861328 (CONFIRMED_BY_GEOMETRY) |
| 5 | 2026-05-01T04:00:00+00:00 / high / 236.5399932861328 (CONFIRMED_BY_GEOMETRY) | 2026-09-04T20:00:00+00:00 / high / 234.75999450683594 (DEVELOPING) |

For H0009 only, the P004 operands are the proposed Wave 1 origin 153.1300048828125 and supplied Wave 2 retracement endpoint 212.19000244140625. Returned reason: The supplied Wave 2 retracement extreme moved beyond the supplied Wave 1 origin.. These are rule operands, not trading levels.

### 1mo / child — sequence 1fcd833260d2

Observed in 1wk; snapshot prefix b6695aa0b692 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0005 | H0010 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0005 | H0011 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0015 | H0030 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0015 | H0031 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| child_1 | 2025-02-03T05:00:00+00:00 / low / 113.01000213623047 (CONFIRMED_BY_GEOMETRY) | 2025-02-17T05:00:00+00:00 / high / 143.44000244140625 (CONFIRMED_BY_GEOMETRY) |
| child_2 | 2025-02-17T05:00:00+00:00 / high / 143.44000244140625 (CONFIRMED_BY_GEOMETRY) | 2025-03-10T04:00:00+00:00 / low / 104.7699966430664 (CONFIRMED_BY_GEOMETRY) |
| child_3 | 2025-03-10T04:00:00+00:00 / low / 104.7699966430664 (CONFIRMED_BY_GEOMETRY) | 2025-03-31T04:00:00+00:00 / low / 92.11000061035156 (DEVELOPING) |

Exact finer-evidence links (repetition retained):

| Child hypothesis | Parent family hypothesis | Required child |
| --- | --- | --- |
| H0010 | H0002 | child_1: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0011 | H0002 | child_1: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0030 | H0007 | child_1: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |
| H0031 | H0007 | child_1: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |

### 1mo / child — sequence 217bec38c791

Observed in 1wk; snapshot prefix b6695aa0b692 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0019 | H0038 | TRIANGLE | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0024 | H0046 | NORMAL_IMPULSE_PARTIAL | UP | REJECTED_EXACT_HYPOTHESIS_P004; P004 RULE_VIOLATED; P005 SUFFICIENT_CONDITION_ESTABLISHED: BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION |
| C0025 | H0047 | NORMAL_IMPULSE_PARTIAL | UP | REJECTED_EXACT_HYPOTHESIS_P004; P004 RULE_VIOLATED; P005 SUFFICIENT_CONDITION_ESTABLISHED: BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION |
| C0026 | H0048 | NORMAL_IMPULSE_PARTIAL | UP | REJECTED_EXACT_HYPOTHESIS_P004; P004 RULE_VIOLATED; P005 SUFFICIENT_CONDITION_ESTABLISHED: BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| 1 | 2025-10-20T04:00:00+00:00 / low / 176.75999450683594 (CONFIRMED_BY_GEOMETRY) | 2025-10-27T04:00:00+00:00 / high / 212.19000244140625 (CONFIRMED_BY_GEOMETRY) |
| 2 | 2025-10-27T04:00:00+00:00 / high / 212.19000244140625 (CONFIRMED_BY_GEOMETRY) | 2025-11-24T05:00:00+00:00 / low / 169.5500030517578 (CONFIRMED_BY_GEOMETRY) |
| 3 | 2025-11-24T05:00:00+00:00 / low / 169.5500030517578 (CONFIRMED_BY_GEOMETRY) | 2025-12-15T05:00:00+00:00 / low / 170.30999755859375 (CONFIRMED_BY_GEOMETRY) |
| 4 | 2025-12-15T05:00:00+00:00 / low / 170.30999755859375 (CONFIRMED_BY_GEOMETRY) | 2026-01-05T05:00:00+00:00 / high / 193.6300048828125 (CONFIRMED_BY_GEOMETRY) |
| 5 | 2026-01-05T05:00:00+00:00 / high / 193.6300048828125 (CONFIRMED_BY_GEOMETRY) | 2026-01-26T05:00:00+00:00 / high / 194.49000549316406 (CONFIRMED_BY_GEOMETRY) |

For H0046 only, the P004 operands are the proposed Wave 1 origin 176.75999450683594 and supplied Wave 2 retracement endpoint 169.5500030517578. Returned reason: The supplied Wave 2 retracement extreme moved beyond the supplied Wave 1 origin.. These are rule operands, not trading levels.

Exact finer-evidence links (repetition retained):

| Child hypothesis | Parent family hypothesis | Required child |
| --- | --- | --- |
| H0038 | H0007 | child_3: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |
| H0046 | H0001 | child_3: MOTIVE_FIVE_FAMILY_REQUIRED (exact ID in export) |
| H0047 | H0002 | child_3: MOTIVE_FIVE_FAMILY_REQUIRED (exact ID in export) |
| H0048 | H0005 | child_1: MOTIVE_FIVE_FAMILY_REQUIRED (exact ID in export) |

### 1wk / parent — sequence 14e29bddeba1

Observed in 1wk; snapshot prefix b6695aa0b692 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0029 | H0051 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0029 | H0052 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| child_1 | 2026-06-01T04:00:00+00:00 / high / 232.27999877929688 (CONFIRMED_BY_GEOMETRY) | 2026-06-22T04:00:00+00:00 / high / 213.99000549316406 (CONFIRMED_BY_GEOMETRY) |
| child_2 | 2026-06-22T04:00:00+00:00 / high / 213.99000549316406 (CONFIRMED_BY_GEOMETRY) | 2026-06-29T04:00:00+00:00 / low / 189.8000030517578 (CONFIRMED_BY_GEOMETRY) |
| child_3 | 2026-06-29T04:00:00+00:00 / low / 189.8000030517578 (CONFIRMED_BY_GEOMETRY) | 2026-07-27T04:00:00+00:00 / low / 190.00999450683594 (CONFIRMED_BY_GEOMETRY) |

### 1wk / parent — sequence d34fc300ea2d

Observed in 1wk; snapshot prefix b6695aa0b692 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0032 | H0057 | TRIANGLE | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0032 | H0058 | ENDING_DIAGONAL | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0032 | H0059 | NORMAL_IMPULSE_PARTIAL | DOWN | PARTIAL_REVIEW_UNRESOLVED_FAMILY; P004 RULE_SATISFIED; P005 UNRESOLVED: DEVELOPING_REQUIRED_ENDPOINT |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| 1 | 2026-06-01T04:00:00+00:00 / high / 232.27999877929688 (CONFIRMED_BY_GEOMETRY) | 2026-06-22T04:00:00+00:00 / high / 213.99000549316406 (CONFIRMED_BY_GEOMETRY) |
| 2 | 2026-06-22T04:00:00+00:00 / high / 213.99000549316406 (CONFIRMED_BY_GEOMETRY) | 2026-06-29T04:00:00+00:00 / low / 189.8000030517578 (CONFIRMED_BY_GEOMETRY) |
| 3 | 2026-06-29T04:00:00+00:00 / low / 189.8000030517578 (CONFIRMED_BY_GEOMETRY) | 2026-07-27T04:00:00+00:00 / low / 190.00999450683594 (CONFIRMED_BY_GEOMETRY) |
| 4 | 2026-07-27T04:00:00+00:00 / low / 190.00999450683594 (CONFIRMED_BY_GEOMETRY) | 2026-08-24T04:00:00+00:00 / low / 207.25 (CONFIRMED_BY_GEOMETRY) |
| 5 | 2026-08-24T04:00:00+00:00 / low / 207.25 (CONFIRMED_BY_GEOMETRY) | 2026-09-04T20:00:00+00:00 / high / 234.75999450683594 (DEVELOPING) |

For H0059 only, the P004 operands are the proposed Wave 1 origin 232.27999877929688 and supplied Wave 2 retracement endpoint 189.8000030517578. Returned reason: The supplied Wave 2 retracement extreme did not move beyond the supplied Wave 1 origin.. These are rule operands, not trading levels.

### 1wk / child — sequence b256af8c8df4

Observed in 1d; snapshot prefix cb40f31e2718 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0033 | H0060 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0033 | H0061 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0035 | H0064 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0035 | H0065 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0039 | H0072 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0039 | H0073 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0043 | H0080 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0043 | H0081 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| child_1 | 2026-07-07T13:30:00+00:00 / low / 191.13999938964844 (CONFIRMED_BY_GEOMETRY) | 2026-07-15T13:30:00+00:00 / high / 213.80999755859375 (CONFIRMED_BY_GEOMETRY) |
| child_2 | 2026-07-15T13:30:00+00:00 / high / 213.80999755859375 (CONFIRMED_BY_GEOMETRY) | 2026-07-17T13:30:00+00:00 / low / 197.97000122070312 (CONFIRMED_BY_GEOMETRY) |
| child_3 | 2026-07-17T13:30:00+00:00 / low / 197.97000122070312 (CONFIRMED_BY_GEOMETRY) | 2026-07-22T13:30:00+00:00 / high / 214.38999938964844 (CONFIRMED_BY_GEOMETRY) |

Exact finer-evidence links (repetition retained):

| Child hypothesis | Parent family hypothesis | Required child |
| --- | --- | --- |
| H0060 | H0053 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0061 | H0053 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0064 | H0054 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0065 | H0054 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0072 | H0056 | child_1: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0073 | H0056 | child_1: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0080 | H0057 | child_3: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |
| H0081 | H0057 | child_3: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |

### 1d / parent — sequence e46c20b55f8c

Observed in 1d; snapshot prefix cb40f31e2718 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0047 | H0088 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0047 | H0089 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| child_1 | 2026-08-11T13:30:00+00:00 / low / 216.1999969482422 (CONFIRMED_BY_GEOMETRY) | 2026-08-17T13:30:00+00:00 / high / 227.9199981689453 (CONFIRMED_BY_GEOMETRY) |
| child_2 | 2026-08-17T13:30:00+00:00 / high / 227.9199981689453 (CONFIRMED_BY_GEOMETRY) | 2026-08-24T13:30:00+00:00 / low / 207.25 (CONFIRMED_BY_GEOMETRY) |
| child_3 | 2026-08-24T13:30:00+00:00 / low / 207.25 (CONFIRMED_BY_GEOMETRY) | 2026-08-27T13:30:00+00:00 / high / 230.47000122070312 (CONFIRMED_BY_GEOMETRY) |

### 1d / parent — sequence 7e772744c4fa

Observed in 1d; snapshot prefix cb40f31e2718 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0050 | H0094 | TRIANGLE | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0050 | H0095 | ENDING_DIAGONAL | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0050 | H0096 | NORMAL_IMPULSE_PARTIAL | UP | REJECTED_EXACT_HYPOTHESIS_P004; P004 RULE_VIOLATED; P005 UNRESOLVED: DEVELOPING_REQUIRED_ENDPOINT |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| 1 | 2026-08-11T13:30:00+00:00 / low / 216.1999969482422 (CONFIRMED_BY_GEOMETRY) | 2026-08-17T13:30:00+00:00 / high / 227.9199981689453 (CONFIRMED_BY_GEOMETRY) |
| 2 | 2026-08-17T13:30:00+00:00 / high / 227.9199981689453 (CONFIRMED_BY_GEOMETRY) | 2026-08-24T13:30:00+00:00 / low / 207.25 (CONFIRMED_BY_GEOMETRY) |
| 3 | 2026-08-24T13:30:00+00:00 / low / 207.25 (CONFIRMED_BY_GEOMETRY) | 2026-08-27T13:30:00+00:00 / high / 230.47000122070312 (CONFIRMED_BY_GEOMETRY) |
| 4 | 2026-08-27T13:30:00+00:00 / high / 230.47000122070312 (CONFIRMED_BY_GEOMETRY) | 2026-09-01T13:30:00+00:00 / low / 215.10000610351562 (CONFIRMED_BY_GEOMETRY) |
| 5 | 2026-09-01T13:30:00+00:00 / low / 215.10000610351562 (CONFIRMED_BY_GEOMETRY) | 2026-09-04T13:30:00+00:00 / high / 234.75999450683594 (DEVELOPING) |

For H0096 only, the P004 operands are the proposed Wave 1 origin 216.1999969482422 and supplied Wave 2 retracement endpoint 207.25. Returned reason: The supplied Wave 2 retracement extreme moved beyond the supplied Wave 1 origin.. These are rule operands, not trading levels.

### 1d / child — sequence df1cd7d540dd

Observed in 1h; snapshot prefix 5b0239693550 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0051 | H0097 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0051 | H0098 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0057 | H0109 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0057 | H0110 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0063 | H0121 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0063 | H0122 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0082 | H0158 | SINGLE_ZIGZAG | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0082 | H0159 | FLAT | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| child_1 | 2026-08-17T15:30:00+00:00 / high / 227.9199981689453 (CONFIRMED_BY_GEOMETRY) | 2026-08-18T14:30:00+00:00 / low / 218.69020080566406 (CONFIRMED_BY_GEOMETRY) |
| child_2 | 2026-08-18T14:30:00+00:00 / low / 218.69020080566406 (CONFIRMED_BY_GEOMETRY) | 2026-08-18T17:30:00+00:00 / high / 220.50999450683594 (CONFIRMED_BY_GEOMETRY) |
| child_3 | 2026-08-18T17:30:00+00:00 / high / 220.50999450683594 (CONFIRMED_BY_GEOMETRY) | 2026-08-19T18:30:00+00:00 / high / 219.99000549316406 (CONFIRMED_BY_GEOMETRY) |

Exact finer-evidence links (repetition retained):

| Child hypothesis | Parent family hypothesis | Required child |
| --- | --- | --- |
| H0097 | H0088 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0098 | H0088 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0109 | H0089 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0110 | H0089 | child_2: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0121 | H0091 | child_1: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0122 | H0091 | child_1: CORRECTIVE_THREE_FAMILY_REQUIRED (exact ID in export) |
| H0158 | H0094 | child_2: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |
| H0159 | H0094 | child_2: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |

### 1d / child — sequence f6d03f45f82d

Observed in 1h; snapshot prefix 5b0239693550 (full hash in JSON/CSV). These are proposed endpoints, not certified orthodox ends.

| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |
| --- | --- | --- | --- | --- |
| C0081 | H0157 | TRIANGLE | NOT_ASSIGNED | CURRENT_SUPPLIED_SCOPE_REVIEWED |
| C0098 | H0186 | NORMAL_IMPULSE_PARTIAL | UP | PARTIAL_REVIEW_UNRESOLVED_FAMILY; P004 RULE_SATISFIED; P005 UNRESOLVED: ZERO_OR_OPPOSING_ROLE_MOVEMENT |

| Proposed slot | Start UTC / field / price | End UTC / field / price |
| --- | --- | --- |
| 1 | 2026-08-11T17:30:00+00:00 / low / 216.3000030517578 (CONFIRMED_BY_GEOMETRY) | 2026-08-12T14:30:00+00:00 / high / 225.10000610351562 (CONFIRMED_BY_GEOMETRY) |
| 2 | 2026-08-12T14:30:00+00:00 / high / 225.10000610351562 (CONFIRMED_BY_GEOMETRY) | 2026-08-12T16:30:00+00:00 / low / 222.67010498046875 (CONFIRMED_BY_GEOMETRY) |
| 3 | 2026-08-12T16:30:00+00:00 / low / 222.67010498046875 (CONFIRMED_BY_GEOMETRY) | 2026-08-12T19:30:00+00:00 / low / 222.22999572753906 (CONFIRMED_BY_GEOMETRY) |
| 4 | 2026-08-12T19:30:00+00:00 / low / 222.22999572753906 (CONFIRMED_BY_GEOMETRY) | 2026-08-13T13:30:00+00:00 / high / 227.22999572753906 (CONFIRMED_BY_GEOMETRY) |
| 5 | 2026-08-13T13:30:00+00:00 / high / 227.22999572753906 (CONFIRMED_BY_GEOMETRY) | 2026-08-13T15:30:00+00:00 / low / 223.7100067138672 (CONFIRMED_BY_GEOMETRY) |

For H0186 only, the P004 operands are the proposed Wave 1 origin 216.3000030517578 and supplied Wave 2 retracement endpoint 222.67010498046875. Returned reason: The supplied Wave 2 retracement extreme did not move beyond the supplied Wave 1 origin.. These are rule operands, not trading levels.

Exact finer-evidence links (repetition retained):

| Child hypothesis | Parent family hypothesis | Required child |
| --- | --- | --- |
| H0157 | H0094 | child_1: CORRECTIVE_FAMILY_REQUIRED (exact ID in export) |
| H0186 | H0088 | child_1: MOTIVE_FIVE_FAMILY_REQUIRED (exact ID in export) |

## Rejections, unresolved internals and exclusions

### 1mo with 1wk child observations

Internal requirements: 28; satisfied: 0. Requirements with partial Normal Impulse execution: 5. Window coverage: {'FULL_WINDOW_COVERAGE': 28}.

- parent: P004 rejections 1; P004-invalid despite P005 sufficiency 0. P005 unresolved reasons: {'DEVELOPING_REQUIRED_ENDPOINT': 1}.
- child: P004 rejections 3; P004-invalid despite P005 sufficiency 3. P005 unresolved reasons: {'DEVELOPING_REQUIRED_ENDPOINT': 2}.

Search exclusions: 65 parent pivots outside the latest-six consideration window; 12 subsequences outside span/skip bounds. Child windows with insufficient pivots: 12; finer-coverage failures: 0. No cap exception occurred; these exclusions are not evidence of family impossibility. Full diagnostics remain in JSON.


### 1wk with 1d child observations

Internal requirements: 28; satisfied: 0. Requirements with partial Normal Impulse execution: 0. Window coverage: {'FULL_WINDOW_COVERAGE': 24, 'PARTIAL_WINDOW_COVERAGE': 4}.

- parent: P004 rejections 0; P004-invalid despite P005 sufficiency 0. P005 unresolved reasons: {'DEVELOPING_REQUIRED_ENDPOINT': 1}.
- child: P004 rejections 0; P004-invalid despite P005 sufficiency 0. P005 unresolved reasons: {}.
- No Normal Impulse child hypothesis was available in this bounded search; P004/P005 were not evaluated on that path.

Search exclusions: 363 parent pivots outside the latest-six consideration window; 12 subsequences outside span/skip bounds. Child windows with insufficient pivots: 14; finer-coverage failures: 4. No cap exception occurred; these exclusions are not evidence of family impossibility. Full diagnostics remain in JSON.

- 4 requirement links use incompletely covered window 2026-08-24T04:00:00+00:00 to 2026-09-04T20:00:00+00:00, with 10 supplied bars per link. No full-coverage geometry was fabricated.

### 1d with 1h child observations

Internal requirements: 28; satisfied: 0. Requirements with partial Normal Impulse execution: 9. Window coverage: {'FULL_WINDOW_COVERAGE': 28}.

- parent: P004 rejections 1; P004-invalid despite P005 sufficiency 0. P005 unresolved reasons: {'DEVELOPING_REQUIRED_ENDPOINT': 1}.
- child: P004 rejections 2; P004-invalid despite P005 sufficiency 0. P005 unresolved reasons: {'DEVELOPING_REQUIRED_ENDPOINT': 5, 'ZERO_OR_OPPOSING_ROLE_MOVEMENT': 4}.

Search exclusions: 1805 parent pivots outside the latest-six consideration window; 12 subsequences outside span/skip bounds. Child windows with insufficient pivots: 0; finer-coverage failures: 0. No cap exception occurred; these exclusions are not evidence of family impossibility. Full diagnostics remain in JSON.


## Limitations and next decision

- P006 remains frozen/unresolved/conflicted: orthodox endpoints, scope, equality and timing are not resolved.
- P005 establishes percentage sufficiency only, not full P005 or impulse validity.
- SOURCE_DERIVED_BASE_CASE_NOT_FOUND: reviewed children do not supply positive family proof.
- Flat/Triangle geometry freezes remain intact; cardinality is not subtype or full-family validation.
- Validated-family producers and issuances remain 0 / 0. Missing children are not terminal waves.
- Data quality below retains provider omissions; nominal interval gaps are not exchange-calendar proof of missing trading bars.
- No RSI/MACD/EWO, Fibonacci evidence, volume interpretation, targets, entry/exit advice or trading invalidation levels were added.
- Next step: review these candidate/evidence links; additional exact-family claims remain blocked by source authority, not by a preference score.

- 1mo: provider warnings []; dropped null-OHLC rows []; duplicate timestamps []; nominal interval gaps 0.
- 1wk: provider warnings []; dropped null-OHLC rows []; duplicate timestamps []; nominal interval gaps 0.
- 1d: provider warnings []; dropped null-OHLC rows []; duplicate timestamps []; nominal interval gaps 1508.
- 1h: provider warnings ['YAHOO_INTRADAY_RETENTION_LIMIT', 'YAHOO_NULL_OHLC_ROWS_DROPPED']; dropped null-OHLC rows [409, 526, 1427, 2146, 2270]; duplicate timestamps []; nominal interval gaps 499.

## Evidence exports and replay

candidates.csv: 194 rows. endpoints.csv: 1284 rows. All 194 originating hypothesis links are retained. market_report.json contains full results within the executed search and exact source references. Run the offline command in README.md against saved inputs; no serialized methodology authority is reused.
