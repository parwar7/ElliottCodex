# NVDA full-history hierarchical hypotheses V1

## What this stage does

This is bounded operational exploration, not a complete validated Elliott count
or project-manager approval. The preserved NVDA capture is reused without any
network retrieval. See report/report.md for results, report/results.json for
all linked evidence, and capability_review.md for the API and source boundaries.

Approved base: 035eeb62f386f206a0ba7ec05b51a648337b06b4.

## Reproduce

From C:\ElliottCodex\Runtime_WORKSPACE:

~~~powershell
$env:PYTHONPATH='src;tools'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/nvda_hierarchical_hypotheses.py --output runs/NVDA-full-history-replay
~~~

The output directory must be new. The default input folder is the previous
approved NVDA-BOUNDED-ANALYSIS-REPORT-V1/inputs capture; no normalized data is
duplicated here. Its manifest is pinned to
bb8d73a6ace250a5d8815cd215760b210913db715fb43d6ef3327a8cb535424e.
The manifest and each normalized input are verified before execution.
Original capture dates and latest observed bar dates remain distinct.
No raw Yahoo response body or protected source media is committed.

The preserved capture contains 334 Monthly, 1,443 Weekly, 6,948 Daily and
3,486 hourly bars. Hourly coverage begins on 9 September 2024. Five null-OHLC
hourly rows were omitted by the existing provider, with indices/warnings
retained in input metadata. Nominal interval gaps are not exchange-calendar
proof of missing trading bars. This stage performs no additional cleanup.
Historical windows use the captured snapshot, not information-as-known-at-the-time
backtests. No historical completion or first-observation availability is inferred.

The runner writes configuration and search_plan before execution. Results,
Markdown and CSV follow only after successful live identity validation and
report reconciliation. If execution fails, a plan alone is not a completed run.

## Four separate answers

A. This search schedules bounded windows in all three historical regions.
It does not exhaust every six-pivot window or every possible pivot combination.

B. One coarsened source-pivot sequence spans the first to last available
Monthly geometric pivots. Family selectors over it remain hypotheses. This is
not a coherent full-history Elliott count: data before/after each proposal,
unexamined internal structures and excluded pivots remain unresolved.

C. Successive links use only exact returned child-family bridges, their
originating requirement identities and the existing public APIs. The deepest
actually generated level is reported; the configured limit does not claim
that level was reached. All unexpanded contexts remain explicit.

D. Every current position remains CURRENT_POSITION_UNRESOLVED. Proposed slot
mapping is not a developing-wave template or completion proof. Trailing bars,
hypothesis-local P004 rejection, P006 and missing exact family proof remain
visible. The final selected pivot is never automatically the current wave.

## Search and presentation

The deterministic policy is declared in report/configuration.json and
capability_review.md. Six regional windows and one coarsened proposal are
scheduled. Per-region unvisited starts, cross-region policy exclusions,
per-job selected indices and timestamps, and per-level unvisited requirements
are machine-readable. The full-range sample skips source pivots explicitly;
the scoped generator's zero-skip parameter refers only to its supplied scope.

The source hierarchy is not mapped to timeframe/depth. Levels 0..3 are neutral
operational labels. Monthly -> Weekly -> Daily -> 1H are explicit observation
choices. Missing older hourly coverage remains unresolved, without resampling.

The compact report table shows first-in-enumeration family contexts, not best
ones. Component examples suppress repeated shape/family-slot displays only;
JSON/CSV retain every original hypothesis. Repeated contexts are not independent
confirmation. No full recursive certification or upward positive proof is claimed.

## Preservation and verification

Only the new tools/nvda_hierarchical_hypotheses.py command and its new tests
are implementation additions. No existing Runtime file, Kernel/shared contract,
protected file, prior test or historical baseline is edited.

Pre/final integrity checks verify every Brain entry (30), every approved source
entry (21), current policy, VERSION 0.1.0 and the approved book. Inventories
remain 11 executable methodology behaviors, 7 structural-invalidity producers,
0 validated-family producers and 0 issuances.

P004 and P005 retain their exact semantics. P005 sufficiency cannot rescue P004.
P006, Flat/Triangle freezes, SOURCE_DERIVED_BASE_CASE_NOT_FOUND and legacy
analyze = NOT_IMPLEMENTED remain unchanged.

See tests.json and audit.json for actual receipts and limitations. The initial
development fixture for missing older hourly data mistakenly used latest-only
Monthly requirements; it was corrected to issue a genuine earliest-history
hypothesis. This was not a Kernel or source-semantics defect.

Reporting and validation skills informed the separate capability claims,
exact linked lookup tables and all-row reconciliation. The established repo
Markdown/JSON/CSV delivery is retained rather than introducing another report
application. Codex Process Jobs rejects win32 in this installation; ordinary
foreground processes were used.

This is a logical hash baseline, not physical immutability, a new protected
methodology adoption or project-manager approval.
