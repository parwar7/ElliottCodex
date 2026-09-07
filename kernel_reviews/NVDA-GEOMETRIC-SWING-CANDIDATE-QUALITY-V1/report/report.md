# NVDA geometric swing search

## Technical summary

This run selects nonzero alternating price movements before Elliott evaluation. It does not establish correct waves, a coherent count or a current-wave position.

## Same data, different search domain

The saved Yahoo capture is unchanged: collected 6 September 2026, latest bars 4 September 2026. Geometry windows 2, 4 and 8 are operational scales on Monthly bars, not degrees or proof of major waves.

Historical H0467 movements: UP / UP / UP / UP / UP. It falls outside this search domain; no new structural rejection is issued.

## Coverage by scale and historical region

Each region selects its first eligible consecutive six-pivot sequence. All other starts are classified explicitly; this is not exhaustive history or skipped-pivot search.

| Window | Region | Emitted pivots (whole scale) | Eligible starts | Selected | Unvisited |
|---:|---|---:|---:|---:|---:|
| 2 | 1999–2007 | 71 | 14 | 1 | 13 |
| 2 | 2008–2016 | 71 | 13 | 1 | 12 |
| 2 | 2017–2026 | 71 | 17 | 1 | 16 |
| 4 | 1999–2007 | 42 | 3 | 1 | 2 |
| 4 | 2008–2016 | 42 | 2 | 1 | 1 |
| 4 | 2017–2026 | 42 | 6 | 1 | 5 |
| 8 | 1999–2007 | 20 | 1 | 1 | 0 |
| 8 | 2008–2016 | 20 | 0 | 0 | 0 |
| 8 | 2017–2026 | 20 | 0 | 0 | 0 |

Window 2 dispositions: {'SEARCH_DOMAIN_EXCLUDED': 12, 'SELECTED': 3, 'UNVISITED_BUDGET': 41, 'REGION_POLICY_EXCLUDED': 10}. Same-kind pairs: 5; tied-extreme diagnostic windows: 3. ['INPUT_BAR_COUNT=334', 'GEOMETRIC_PIVOT_COUNT=71', 'AMBIGUOUS_SAME_BAR_HIGH_LOW_EXCLUDED=0', 'GEOMETRIC_PIVOT_IS_NOT_ELLIOTT_WAVE_ENDPOINT', 'TIMEFRAME_IS_NOT_DEGREE']


Window 4 dispositions: {'SELECTED': 3, 'UNVISITED_BUDGET': 8, 'SEARCH_DOMAIN_EXCLUDED': 18, 'REGION_POLICY_EXCLUDED': 8}. Same-kind pairs: 7; tied-extreme diagnostic windows: 1. ['INPUT_BAR_COUNT=334', 'GEOMETRIC_PIVOT_COUNT=42', 'AMBIGUOUS_SAME_BAR_HIGH_LOW_EXCLUDED=0', 'GEOMETRIC_PIVOT_IS_NOT_ELLIOTT_WAVE_ENDPOINT', 'TIMEFRAME_IS_NOT_DEGREE']


Window 8 dispositions: {'SELECTED': 1, 'SEARCH_DOMAIN_EXCLUDED': 9, 'REGION_POLICY_EXCLUDED': 5}. Same-kind pairs: 3; tied-extreme diagnostic windows: 0. ['INPUT_BAR_COUNT=334', 'GEOMETRIC_PIVOT_COUNT=20', 'AMBIGUOUS_SAME_BAR_HIGH_LOW_EXCLUDED=0', 'GEOMETRIC_PIVOT_IS_NOT_ELLIOTT_WAVE_ENDPOINT', 'TIMEFRAME_IS_NOT_DEGREE']

## Existing checks, not family proof

Hypothesis counts include separate family selectors over the same neutral candidate. They are not independent confirmations. Child results below use the unchanged child API, not the new parent-domain filter.

| Path | Hypotheses | Candidate contexts | P004 | P005 | Outside domain |
|---|---:|---:|---|---|---:|
| child | 137 | 74 | {'RULE_SATISFIED': 6, 'RULE_VIOLATED': 1} | {'SUFFICIENT_CONDITION_ESTABLISHED': 2, 'UNRESOLVED': 5} | 58 |
| parent | 63 | 28 | {'RULE_SATISFIED': 2, 'RULE_VIOLATED': 5} | {'SUFFICIENT_CONDITION_ESTABLISHED': 4, 'UNRESOLVED': 3} | 0 |

Child P005 unresolved reasons: {'DEVELOPING_REQUIRED_ENDPOINT': 1, 'SUFFICIENCY_NOT_ESTABLISHED_NO_NEGATIVE_INFERENCE': 3, 'ZERO_OR_OPPOSING_ROLE_MOVEMENT': 1}. P004-invalid despite P005 sufficiency: 0.

Parent P005 unresolved reasons: {'SUFFICIENCY_NOT_ESTABLISHED_NO_NEGATIVE_INFERENCE': 3}. P004-invalid despite P005 sufficiency: 3.

P004 remains fatal to its exact hypothesis regardless of P005 sufficiency. Internal requirements remain unsatisfied. P005 is sufficiency-only; neither alternation nor these checks establish family validity.

## Deterministic movement samples

The first Normal Impulse proposal per root is displayed in enumeration order, not ranked. All prices/fields, original pivots and parent links are in JSON/CSV. Signs are factual price comparisons, not new wave rules.

### H0009 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2000-10-01 / high / 0.359375 | 2000-12-01 / low / 0.11458300054073334 | DOWN |
| 2 | 2000-12-01 / low / 0.11458300054073334 | 2001-05-01 / high / 0.41666701436042786 | UP |
| 3 | 2001-05-01 / high / 0.41666701436042786 | 2001-10-01 / low / 0.18883299827575684 | DOWN |
| 4 | 2001-10-01 / low / 0.18883299827575684 | 2002-01-01 / high / 0.6054999828338623 | UP |
| 5 | 2002-01-01 / high / 0.6054999828338623 | 2002-10-01 / low / 0.05999999865889549 | DOWN |

P004: RULE_VIOLATED; P005: UNRESOLVED (SUFFICIENCY_NOT_ESTABLISHED_NO_NEGATIVE_INFERENCE). Current position unresolved.

### H0069 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2008-03-01 / low / 0.43274998664855957 | 2008-06-01 / high / 0.6337500214576721 | UP |
| 2 | 2008-06-01 / high / 0.6337500214576721 | 2008-11-01 / low / 0.14374999701976776 | DOWN |
| 3 | 2008-11-01 / low / 0.14374999701976776 | 2009-09-01 / high / 0.41449999809265137 | UP |
| 4 | 2009-09-01 / high / 0.41449999809265137 | 2009-11-01 / low / 0.289000004529953 | DOWN |
| 5 | 2009-11-01 / low / 0.289000004529953 | 2010-01-01 / high / 0.4740000069141388 | UP |

P004: RULE_VIOLATED; P005: SUFFICIENT_CONDITION_ESTABLISHED (BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION). Current position unresolved.

### H0126 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2017-02-01 / high / 3.0230000019073486 | 2017-03-01 / low / 2.3792500495910645 | DOWN |
| 2 | 2017-03-01 / low / 2.3792500495910645 | 2018-10-01 / high / 7.318999767303467 | UP |
| 3 | 2018-10-01 / high / 7.318999767303467 | 2018-12-01 / low / 3.1115000247955322 | DOWN |
| 4 | 2018-12-01 / low / 3.1115000247955322 | 2019-04-01 / high / 4.836750030517578 | UP |
| 5 | 2019-04-01 / high / 4.836750030517578 | 2019-06-01 / low / 3.315000057220459 | DOWN |

P004: RULE_VIOLATED; P005: SUFFICIENT_CONDITION_ESTABLISHED (BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION). Current position unresolved.

### H0173 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-4:swing:0

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2000-06-01 / high / 0.3666670024394989 | 2000-12-01 / low / 0.11458300054073334 | DOWN |
| 2 | 2000-12-01 / low / 0.11458300054073334 | 2001-05-01 / high / 0.41666701436042786 | UP |
| 3 | 2001-05-01 / high / 0.41666701436042786 | 2001-10-01 / low / 0.18883299827575684 | DOWN |
| 4 | 2001-10-01 / low / 0.18883299827575684 | 2002-01-01 / high / 0.6054999828338623 | UP |
| 5 | 2002-01-01 / high / 0.6054999828338623 | 2002-10-01 / low / 0.05999999865889549 | DOWN |

P004: RULE_VIOLATED; P005: UNRESOLVED (SUFFICIENCY_NOT_ESTABLISHED_NO_NEGATIVE_INFERENCE). Current position unresolved.

### H0182 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-4:swing:16

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2008-11-01 / low / 0.14374999701976776 | 2010-01-01 / high / 0.4740000069141388 | UP |
| 2 | 2010-01-01 / high / 0.4740000069141388 | 2010-08-01 / low / 0.2162500023841858 | DOWN |
| 3 | 2010-08-01 / low / 0.2162500023841858 | 2011-02-01 / high / 0.6542500257492065 | UP |
| 4 | 2011-02-01 / high / 0.6542500257492065 | 2011-10-01 / low / 0.2867499887943268 | DOWN |
| 5 | 2011-10-01 / low / 0.2867499887943268 | 2012-02-01 / high / 0.42250001430511475 | UP |

P004: RULE_SATISFIED; P005: SUFFICIENT_CONDITION_ESTABLISHED (BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION). Current position unresolved.

### H0191 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-4:swing:31

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2020-03-01 / low / 4.517000198364258 | 2020-09-01 / high / 14.726750373840332 | UP |
| 2 | 2020-09-01 / high / 14.726750373840332 | 2021-03-01 / low / 11.566499710083008 | DOWN |
| 3 | 2021-03-01 / low / 11.566499710083008 | 2021-11-01 / high / 34.64699935913086 | UP |
| 4 | 2021-11-01 / high / 34.64699935913086 | 2022-10-01 / low / 10.812999725341797 | DOWN |
| 5 | 2022-10-01 / low / 10.812999725341797 | 2025-01-01 / high / 153.1300048828125 | UP |

P004: RULE_SATISFIED; P005: UNRESOLVED (SUFFICIENCY_NOT_ESTABLISHED_NO_NEGATIVE_INFERENCE). Current position unresolved.

### H0200 — NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-8:swing:0

| Role | Start UTC / field / price | End UTC / field / price | Move |
|---|---|---|---|
| 1 | 2000-06-01 / high / 0.3666670024394989 | 2000-12-01 / low / 0.11458300054073334 | DOWN |
| 2 | 2000-12-01 / low / 0.11458300054073334 | 2002-01-01 / high / 0.6054999828338623 | UP |
| 3 | 2002-01-01 / high / 0.6054999828338623 | 2002-10-01 / low / 0.05999999865889549 | DOWN |
| 4 | 2002-10-01 / low / 0.05999999865889549 | 2003-06-01 / high / 0.23125000298023224 | UP |
| 5 | 2003-06-01 / high / 0.23125000298023224 | 2004-04-01 / high / 0.22791700065135956 | DOWN |

P004: RULE_VIOLATED; P005: SUFFICIENT_CONDITION_ESTABLISHED (BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION). Current position unresolved.

## Exact child links and operational stops

One genuine Monthly→Weekly child layer is explored for the scale-2 roots only. Later scales and deeper levels remain unvisited, not impossible. A child outside the geometric search domain is separately identified; its existing methodology outcome is not rewritten.

| Root | Requirements | Coverage | Child hypotheses | Further levels |
|---|---:|---|---:|---|
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5 | 28 | {'FULL_WINDOW_COVERAGE': 28} | 51 | ONE_CHILD_LEVEL_BUDGET; DEEPER_LEVELS_UNVISITED |
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24 | 28 | {'FULL_WINDOW_COVERAGE': 28} | 48 | ONE_CHILD_LEVEL_BUDGET; DEEPER_LEVELS_UNVISITED |
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49 | 28 | {'FULL_WINDOW_COVERAGE': 28} | 38 | ONE_CHILD_LEVEL_BUDGET; DEEPER_LEVELS_UNVISITED |
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-4:swing:0 | 0 | {} | 0 | CHILD_SCALE_BUDGET_UNVISITED |
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-4:swing:16 | 0 | {} | 0 | CHILD_SCALE_BUDGET_UNVISITED |
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-4:swing:31 | 0 | {} | 0 | CHILD_SCALE_BUDGET_UNVISITED |
| NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-8:swing:0 | 0 | {} | 0 | CHILD_SCALE_BUDGET_UNVISITED |

Representative first linked child per root (IDs are exact; full records retain all links):

- H0010: parent `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:THREE_SEGMENT_HYPOTHESIS:5-6-7-8:evaluate-as:SINGLE_ZIGZAG`, requirement `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:child:internals:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:THREE_SEGMENT_HYPOTHESIS:5-6-7-8:evaluate-as:SINGLE_ZIGZAG:child:2`, hypothesis `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:child:families:child:1:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:child:children:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:child:internals:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:5:THREE_SEGMENT_HYPOTHESIS:5-6-7-8:evaluate-as:SINGLE_ZIGZAG:child:2:neutral-children:THREE_SEGMENT_HYPOTHESIS:0-1-2-3:evaluate-as:SINGLE_ZIGZAG`.
- H0070: parent `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:THREE_SEGMENT_HYPOTHESIS:24-25-26-27:evaluate-as:SINGLE_ZIGZAG`, requirement `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:child:internals:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:THREE_SEGMENT_HYPOTHESIS:24-25-26-27:evaluate-as:SINGLE_ZIGZAG:child:2`, hypothesis `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:child:families:child:2:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:child:children:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:child:internals:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:24:THREE_SEGMENT_HYPOTHESIS:24-25-26-27:evaluate-as:SINGLE_ZIGZAG:child:2:neutral-children:THREE_SEGMENT_HYPOTHESIS:0-1-2-3:evaluate-as:SINGLE_ZIGZAG`.
- H0127: parent `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:THREE_SEGMENT_HYPOTHESIS:49-50-51-52:evaluate-as:SINGLE_ZIGZAG`, requirement `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:child:internals:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:THREE_SEGMENT_HYPOTHESIS:49-50-51-52:evaluate-as:SINGLE_ZIGZAG:child:2`, hypothesis `NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:child:families:child:1:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:child:children:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:child:internals:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:family:NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1:scale-2:swing:49:THREE_SEGMENT_HYPOTHESIS:49-50-51-52:evaluate-as:SINGLE_ZIGZAG:child:2:neutral-children:THREE_SEGMENT_HYPOTHESIS:0-1-2-3:evaluate-as:SINGLE_ZIGZAG`.

## Limitations and next question

No consolidation is performed. Discovery resolves equal extrema only by its explicit LAST policy and excludes ambiguous same-bar high/low extrema. Such omissions do not establish hidden endpoint order. Coarser windows are not guaranteed to identify meaningful Elliott waves.

Duplicate origins are retained. The geometric signature groups in JSON identify repeated coordinates but do not merge ancestry or count repetitions as confirmation.

- P006 remains frozen/unresolved/conflicted: orthodox endpoints, scope, equality and timing are not resolved.
- P005 establishes percentage sufficiency only, not full P005 or impulse validity.
- SOURCE_DERIVED_BASE_CASE_NOT_FOUND: reviewed children do not supply positive family proof.
- Flat/Triangle geometry freezes remain intact; cardinality is not subtype or full-family validation.

CURRENT_POSITION_UNRESOLVED remains explicit for every context. Developing-position inference is still a separate missing capability. No degree, forecast, targets, confidence, ranking or trading signal is produced.

Next engineering review: exact scoped child-search transport. The current child-evidence contract requires the full finer-discovery pivot tuple; filtered child selection would need an explicitly reviewed contract extension, not tuple substitution. No such extension is implemented here.
