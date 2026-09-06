# NVDA bounded analysis report V1

The user accepts bounded, non-certifying analysis as the current deliverable,
while retaining the existing exact-family proof contract and long-term goal.
This stage adds reporting, not Elliott methodology or project-manager approval.

Approved base: 3cfab72c3fa96ce7e73f02b870ceadaa6e784c65.

## Read the result

[Market report](report/market_report.md) shows actual proposed structures,
hypothesis-only roles, P004/P005 outcomes, finer-evidence links and limitations.
[JSON](report/market_report.json) retains every hypothesis and requirement
within the search. [Candidates](report/candidates.csv) maps compact H/C aliases
to exact identities; [endpoints](report/endpoints.csv) retains every role,
timestamp, source field, exact represented ratio and link.

- 194 family/partial hypotheses, grouped into 45 repeated endpoint sequences.
- 177 generic family hypotheses have supplied cardinality scope reviewed only.
- 17 Normal Impulse partial hypotheses: 10 P004 satisfied, 7 P004 rejected.
- P005 sufficiency: 3 established, 14 unresolved. All 3 sufficient hypotheses
  remain rejected by P004, across distinct parent requirements.
- All 84 internal requirements remain unsatisfied; 14 have partial Normal
  Impulse child execution. There is no validated family or directional forecast.

The report displays the first sequence of each neutral shape per parent
scope/path: at most two groups, without outcome-based selection. All original
links remain in JSON/CSV. Grouping is presentation only, not candidate merging,
ranking, continuity, or proof that repeated sequences are independent episodes.

## Capture and reproducibility

One fresh Yahoo capture occurred on 6 September 2026, 23:20:10–23:20:12 UTC.
Actual capture times and latest bar timestamps are separate. Latest bars are
dated 4 September; fresh retrieval does not mean a new trading session occurred.
No fallback or synthetic observations were used.

Preserved inputs contain 334 Monthly, 1,443 Weekly, 6,948 Daily and 3,486 hourly
bars. The provider dropped five hourly null-OHLC rows and retained their raw
row indices and warnings. Nominal fixed interval gaps are not exchange-calendar
proof of missing trading bars. No silent resampling, price substitution,
endpoint selection or cleanup was introduced. Hourly retrieval requests the
existing rolling 729-day window. Differences from prior captures must not be
attributed solely to code.

inputs/input_manifest.json hashes every normalized input. Each snapshot retains
request, response hash, provider metadata, quality and retrieval time. Raw Yahoo
bodies are not exposed by the public provider and are not retained; their hashes
are provenance, not independently replayable bodies. Stored floats round-trip
as the same represented values, not original decimal precision.

Capture was saved and reloaded before analysis. Offline replay reconstructs
factual objects and obtains new genuine public-factory results. No certificate
is deserialized. This is not a point-in-time backtest or completion-time contract.

From the repository root:

~~~powershell
$env:PYTHONPATH='src;tools'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/nvda_bounded_report.py --inputs kernel_reviews/NVDA-BOUNDED-ANALYSIS-REPORT-V1/inputs --output runs/NVDA-bounded-report-offline
python -B tools/audit_nvda_bounded_report.py runs/NVDA-bounded-report-offline
~~~

The output directory must not exist. Do not add --capture for replay.
The stage replay used runs/NVDA-BOUNDED-ANALYSIS-REPORT-V1-replay;
its verified outputs are retained in this baseline's replay directory.
Cleanup was blocked by environment policy; no deletion retry or permission
change was attempted. Original inputs are shared, not duplicated.
Execution mode is FRESH_CAPTURE in the original and OFFLINE_REPLAY in replay.
That label is the sole expected content difference; capture dates, prices,
identities, outcomes and full evidence remain identical.

For a future separately authorized fresh run, --capture and an explicit
--fallback-inputs directory are supported. Only a provider failure permits
fallback, with actual failure time and reason. Partial captures are not mixed
with old data. STALE_FALLBACK retains the older capture dates conspicuously.
Kernel/policy/identity failures are never worked around. Outputs are write-once.

## Interfaces and exact scope

- tools/nvda_bounded_report.py: separate report command, live result adapters,
  grouping, JSON/CSV/Markdown renderer and bounded write-once output.
- tools/audit_nvda_bounded_report.py: read-only all-row checks against saved
  prices/dates/provenance, CSV, Markdown and requirement links.
- tools/nvda_post_p005_experiment.py: one optional reporting callback on
  run_scope. Default behavior, IDs, configuration, results and execution order
  remain unchanged. The new manifest records original/resulting file hashes.
- tests/test_nvda_bounded_report.py: 18 deterministic tests using genuine public
  factories over the prior immutable NVDA snapshot, with no network.

The existing runner supplies Monthly→Weekly, Weekly→Daily, Daily→1H, one child
layer, latest six parent pivots, earliest six child pivots, zero skips and all
existing operational caps. report/configuration.json contains the complete limits.
No methodology, shared contract, certificate producer, automatic degree,
ranking, indicator, forecast or trading feature was added.

The four-family bridge supplies cardinality evidence and internal requirements;
Normal Impulse supplies P004 and partial P005. Normal Impulse-specific complete
internals are not fabricated by copying another family's requirements.
Leading Diagonal and combinations were not added. Flat/Triangle geometry
freezes, P006 conflict and SOURCE_DERIVED_BASE_CASE_NOT_FOUND remain unchanged.
Legacy analyze remains NOT_IMPLEMENTED.

JSON is a bounded operational report, not a completed ANALYSIS_OUTPUT_SCHEMA
count. That schema's ranked-count/forecast/trade fields cannot honestly be
populated here; no fake Preferred count or decision is inserted.

## Verification and preservation

Pre/final verification hashes every protected entry: Brain VERSION 0.1.0,
30 entries; Sources 21 entries; current policy and approved book unchanged.
Inventories remain 11 executable behaviors / 7 structural producers /
0 validated-family producers / 0 family issuances.

The audit checks all 1,284 endpoints against saved observations, all 194 links,
status/count reconciliation, table content, capture times, provenance and the
exact callback diff. Tests include genuine P004 non-rescue, grouping, missing
authority, stale labeling, mutation rejection, all-row audit and determinism.
See tests.json, audit.json, replay_verification.json and preservation_inventory.json.

The full regression suite is run once after final implementation changes.
The intentionally mocked legacy provider-failure test prints an INCOMPLETE
traceback; it is not a fresh Yahoo failure. Codex Process Jobs explicitly lacks
win32 support in this installation; local foreground processes were used with
outputs inside Runtime_WORKSPACE.

Reporting/validation skills informed the answer-first narrative and all-row
checks. The explicit Markdown/JSON/CSV request overrides generic HTML defaults.
Exact tables suit identity/operand/status lookup better than charts. Definitions
precede evidence; methods, robustness and unresolved decisions remain visible.
No chart/UI was implemented.

The new baseline is a logical hash record, not enforced physical immutability,
protected methodology adoption or project-manager approval. Historical artifacts
remain byte-for-byte unchanged.
