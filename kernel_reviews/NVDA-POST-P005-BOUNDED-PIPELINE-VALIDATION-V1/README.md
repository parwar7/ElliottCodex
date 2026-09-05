# NVDA post-P005 bounded pipeline validation V1

The existing parent/child pipeline ran successfully with the repaired P005
binding. This is an operational experiment, not a complete Elliott analysis,
forecast, count selection or trading signal.

Approved base: `d16e0e5049206fd76a8753f8f2754c8ba3cd3246`.
The user reports project-manager approval of that base and its preceding policy
transition. This new experiment does not claim project-manager approval.

## Result

S/V/U means P004 satisfied / violated / unresolved. P005 E/U means percentage
sufficiency established / unresolved, never full P005 or family validation.

| Parent / finer observations | Parent P004 S/V/U | Parent P005 E/U | Child P004 S/V/U | Child P005 E/U | P004-invalid despite P005 E |
| --- | --- | --- | --- | --- | --- |
| Monthly / Weekly | 0 / 1 / 0 | 0 / 1 | 2 / 3 / 0 | 3 / 2 | 3 |
| Weekly / Daily | 1 / 0 / 0 | 0 / 1 | 0 / 0 / 0 | 0 / 0 | 0 |
| Daily / 1H | 0 / 1 / 0 | 0 / 1 | 7 / 2 / 0 | 0 / 9 | 0 |

All three P005-positive child hypotheses remain invalid under their genuine
P004 results/certificates. They share one endpoint sequence but belong to three
distinct parent requirements; these are hypothesis counts, not independent
market episodes. No hypothesis was discarded or ranked by the report.

All three parents and seven children have P005 reason
`DEVELOPING_REQUIRED_ENDPOINT`. Four other children have
`ZERO_OR_OPPOSING_ROLE_MOVEMENT`. These are exact returned reasons;
no negative P005 invalidity was inferred. None of the ten P004-satisfied
hypotheses also establishes P005 sufficiency in this snapshot.

| Parent scope | Neutral parent candidates | Existing family bridge hypotheses | Neutral child candidates | Child family bridge hypotheses | Requirements with Normal Impulse partial execution |
| --- | --- | --- | --- | --- | --- |
| Monthly | 4 | 8 | 52 | 36 | 5 |
| Weekly | 4 | 8 | 28 | 28 | 0 |
| Daily | 4 | 8 | 112 | 89 | 9 |

Normal Impulse hypotheses in the first table are additive to the four-family
bridge counts in the second table. Each scope has 28 internal requirements,
including nine motive-five requirements. All 84 remain unsatisfied; only 14
have actual Normal Impulse partial execution. Coverage is not proof.

## Bounds and incomplete coverage

See configuration.json for every active limit and experiment_results.json for
the original diagnostics.

- Parent geometry: existing local-extrema discovery, left/right windows 2/2,
  LAST equal-extreme policy, developing pivots retained.
- Parent enumeration: latest six pivots; span six; zero skips; cap ten;
  neutral three-/five-segment shapes only.
- Child enumeration: existing earliest-six policy inside exact supplied parent
  endpoint windows; span six; zero skips; ten per requirement; 500 total.
- At most 100 requirements/windows/finer selections; 10,000 finer pivots total.
  Finer selection permits 10,000 bars / 5,000 geometric pivots per window.
- Existing child family dispatch: 500 candidates, three families per candidate,
  1,500 total hypotheses/evaluations. Normal Impulse caps: 100 parent / 1,000
  child, including the corresponding existing partial/P004 execution caps.
- Exactly one generated child layer. No grandchildren, automatic degree,
  timeframe-degree mapping, P023 auto-confirmation, or silent resampling.

No limit exception occurred. This is NOT exhaustive: consideration bounds
excluded 65 Monthly, 363 Weekly and 1,805 Daily parent pivots before enumeration.
Span/skip restrictions excluded 12 combinatorial subsequences per parent scope.
Per-requirement child windows additionally excluded 8 Monthly-scope and 22
Daily-scope pivot occurrences. These totals can repeat the same physical pivot
across overlapping hypothesis windows.

Weekly->Daily has four partial windows, all ending 2026-09-04T20:00:00Z,
beyond the daily snapshot's last timestamp of 13:30Z. They retain ten supplied
bars each but receive no fabricated full-coverage geometry. Full-coverage
Weekly child windows contain at most five geometric pivots: no six-pivot
Normal Impulse child hypothesis exists in this bounded search. That is not
proof of Elliott family impossibility.

## Data and replay

No replayable prior OHLCV snapshot was found in the repository; previous NVDA
artifacts held summaries and hashes. Fresh public Yahoo provider retrieval
occurred on 2026-09-05 at approximately 09:09 UTC.

- Monthly: 334 bars, first timestamp 1999-01-01.
- Weekly: 1,443 bars, first timestamp 1999-01-18.
- Daily: 6,948 bars, first timestamp 1999-01-22.
- 1H: 3,493 bars, first timestamp 2024-09-06; requested 729 days.

Full ranges, request URLs, exact UTC timestamps, metadata, provider warnings and
raw-response hashes are in inputs/NVDA_*.json. The existing provider discarded
five hourly null-OHLC rows; their original raw row indices are retained.
There are no duplicate normalized timestamps or naive timestamp assumptions.
Nominal fixed-interval gaps are NOT exchange-calendar-verified missing bars.
No calendar correction was introduced.

The public provider does not expose its response body. Therefore replay starts
at the complete losslessly preserved normalized observation transport, not
raw Yahoo bytes. The raw-body hash is provenance, not independently
recomputable from the saved normalized snapshot. Stored float values
round-trip exactly; all numerical comparisons use existing Kernel semantics.
Every fresh run already reloaded these saved files before evaluation.
Fresh inputs differ from historical hashes; code-only causal attribution is
not justified.

From the repository root, replay without any market network request:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/nvda_post_p005_experiment.py --inputs kernel_reviews/NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1/inputs --output runs/NVDA-post-P005-replay.json
```

The output path must not already exist. Do not use --capture for replay.
Replay validates input hashes, reconstructs only factual observation objects,
and establishes new live identities through genuine public factories. It
does not deserialize certificates or reuse issuance attestations.

Read-only independent result/price/percentage audit:

```powershell
python -B kernel_reviews/NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1/audit_results.py
```

Compare replay scopes and snapshot_identity with experiment_results.json;
input_kind intentionally differs between FRESH_CAPTURE and REPLAY.

## Traceability and audit

experiment_results.json retains every Normal Impulse trace.
representative_cases.json contains the first case per path/outcome/reason group,
not a preferred-candidate selection. Each trace includes snapshot content hash,
Yahoo source hash, hypothesis/subject/binding IDs, originating requirement,
role 1/3/5 endpoint timestamps, exact bar provenance, HIGH/LOW basis, represented
integer ratios, recorded geometry state and eligibility, outcomes and reasons.
Live exact-identity checks are recorded separately from replay content hashes.

All 17 traces / 102 endpoints were checked against the saved snapshots.
Applicable percentages were independently recomputed with exact Fraction
arithmetic for audit only. P004 certificate origins and non-rescue intersections,
outcome totals and all requirement totals reconcile. No Kernel/shared-contract
defect was observed. Existing validators, ancestry, policy gates and issuance
validation remain in use.

## Tests, integrity and preservation

- 11 new deterministic orchestration/reporting tests; no live network in tests.
- Focused suite: 139 passed, zero failures/errors (45.748 seconds).
- Full suite: 997 passed, zero failures/errors (109.442 seconds).
- Each suite ran once after final implementation/test changes.
- The provider-failure test intentionally prints an exception/INCOMPLETE;
  both complete suites exit successfully.
- Codex Process Jobs rejected Windows as unsupported; no background job
  started. Execution used the current foreground session instead.

All 570 previously tracked files remain unchanged, including all methodology,
tests, shared contracts and historical baselines. Only the new experiment runner,
new tests and this additive review package were added.

Before and after: Brain VERSION 0.1.0, 30 entries; Sources 21 entries; zero
mismatches. No protected writes, ACL changes or identity changes.

- Brain PACKAGE_MANIFEST:
  `6a7831795b10e98292f9d1fcf8f3e11586031cf7ff2bb0b256efc0735d303338`
- SOURCE_POLICY:
  `605a5dc2f4819816ead3c81aa945579eb4f439e139bf50715b93a30d15adc018`
- SOURCE_MANIFEST:
  `ad774642080c9112796510c01697fd70f2499c828aede547de0b3d39429ad089`
- Approved book:
  `c78e1a29b717445e01de421370a627c440b127cf42c34646526a495b8c42ab9e`

Inventory is unchanged: **11 methodology / 7 structural producers / 0 family
producers / 0 family issuances**. The seven observed P004 certificates are
result instances, not new producers. P005 remains nonfatal sufficiency-only.
P006 remains frozen/unresolved/conflicted; Flat/Triangle freezes,
SOURCE_DERIVED_BASE_CASE_NOT_FOUND and legacy analyze=NOT_IMPLEMENTED remain.

## One next stage

Recommend **BOUNDED-SNAPSHOT-ELIGIBILITY-REPLAY-V1**: engineering-only replay
across explicit observation cutoffs, with a new immutable identity chain at
each snapshot. Ten of fourteen P005-unresolved cases stop at developing
endpoint evidence, and four Weekly requirements lack full finer timestamp
coverage. Measure those transitions without carrying eligibility forward,
relaxing geometry gates, or declaring Elliott completion.

This would require separate stage approval. It cannot resolve full family
proof: P006 and the source-derived base-case blocker require separate source
authority, not more data or operational conventions. No frozen semantics
were reopened and no next stage was implemented.

This is an additive logical baseline, not physically immutable storage or a
new protected-source baseline.
