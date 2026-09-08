# NVDA — Digital multiresolution hypothesis review

Open **report.html** locally. Arabic companion: **report.md**. These are frozen BATS:NVDA / Cboe One observations, not live data or a validated Elliott count.

The deliverable is an additive partial-analysis/report schema, not a completed ranked ANALYSIS_OUTPUT_SCHEMA response. Ranking, forecasting and trading fields are deliberately absent under this stage's authorization.

## Read the evidence

- `canonical_hierarchy.json`: final expanded-resolution experiment, 25 hypotheses / 150 nodes. Every role contains exact snapshot, bar, field, represented float ratio and original runtime IDs. JSON is evidence for inspection, never deserialized runtime authority.
- `wave_table.json`: exact role/parent endpoints and source-reference keys; no rounding of stored numbers.
- `resolution_expanded/hierarchy.json`: actual final runtime export, including P004/P005 traces, partial recursive-composition summaries and all operational search contexts.
- `hierarchy.json`: preserved initial run (21 hypotheses), before the explicit same-parent finer-resolution retry. Not combined with the final run as independent evidence.
- `search_plan.json` and `resolution_retry_plan.json`: declared bounds before their respective evaluations. Retry does not manufacture intermediate daily parents or degrees.
- `planned_search.json` and `resolution_expanded/planned_search.json`: selections before evaluation. Identical source snapshot and original root plan in both runs.
- `coverage.json`: source coverage, geometric exclusions and unvisited windows. Timeframe is observation resolution only.
- `indicator_evidence.json`: 10 saved daily study values verified directly against their original study rows; later indicator capture remains separate from OHLCV capture.
- `latest_observations.json`: exact last captured OHLCV for each of the six native resolutions. Latest 15m capture closes its still-forming bar at 229.29 (13:53:45 UTC); the report's 229.56 is explicitly the earlier Daily snapshot, not a merged latest quote.
- `artifact.json` / `chart_rows.json`: canonical portable-report input and actual SQLite-projected chart data. Fractional year and log10 price are display transforms only; exact prices remain unchanged in tables/tooltips. The four scatter plots retain proposed-point labels 0–5 alongside closes; no interpolated market path is invented.

M1/M2 are separate broad region-based proposals. Neither is ranked. The selected November 2009 local geometric low is **not** represented as the absolute 2008–2009 crisis low. Missing interiors prevent a comprehensive count. A monthly bar's label is not the day of its extreme; child windows were not extended to force equality with daily extrema.

Actual linked depth: Monthly → Weekly → 4H, at most two child edges. Daily/1H/15m were inspected where the declared windows called for them; absence of eligible sequences, missing history and resource limits prevented additional executed child hypotheses. Do not describe this as five proven Elliott degrees.

## Offline replay

From `C:\ElliottCodex\Runtime_WORKSPACE`, with the existing Python runtime and dependencies:

```powershell
$env:PYTHONPATH='src;tools;tests'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/nvda_digital_multidegree.py --output artifacts/nvda-multidegree-replay-new
```

Use a new output directory. The runner verifies protected entries and the approved bridge manifest; it reconstructs genuine factory objects from the **same** six saved native TradingView snapshots. No network, capture, Yahoo or resampling is called. Final expanded experiment counts should match; output timestamps/receipt hashes are intentionally run-specific.

Report-only replay, without regenerating the pipeline:

```powershell
python -B tools/nvda_digital_multidegree_report.py --output artifacts/nvda-multidegree-report-new
```

This reads the approved final evidence in this pack and produces canonical report input, companion and tables in a new Runtime directory. Package `artifact.json` using the existing Data Analytics `deliver_portable_artifact.mjs --input ... --output .../report.html` builder. Set TEMP/TMP beneath Runtime. No browser/package installation is required or performed. An incompatible browser leaves semantic tables available; this run's exact browser limitation is recorded in `browser_audit.json`.

The approved inputs are referenced, not recopied:
`kernel_reviews/TRADINGVIEW-DIGITAL-DATA-AND-NVDA-ANALYSIS-BRIDGE-V1/`.
Its manifest SHA-256 is `8821c441cbb1e72bfe8d99f4474b781316ec9f18d3af82fffd344bc73f0beb03`.

## Compatibility and limitations

Only new Runtime orchestration/report files and tests were added. Existing Kernel/public evidence contracts and historical baselines are unchanged. The generic five-slot bridge uses the existing ending-diagonal **cardinality transport**, not an assertion of diagonal family or an internal family certificate. New child exploration binds exact existing Normal Impulse role subjects, observations and parents; partial one-child composition leaves omitted siblings unresolved.

The preserved live chain is validated before export. A JSON hash/ID never replaces object identity. Geometry cache reuse is restricted to the exact snapshot/config/window; contextual subject/results are not cached. Five-slot original bindings remain pinned by existing repaired validators.

Methodology 11; structural producers 7; validated-family producers/issuances 0/0. P004 rejection remains fatal to its exact hypothesis even when P005 establishes percentage sufficiency. P006, Flat/Triangle freezes, source-derived terminal/base-case blocker and legacy analyze remain unchanged. No ranking, targets, confidence, forecasts or trading signals.

Next unresolved boundary, not a newly started stage: reconciling aggregate-bar extremum time with exact parent component-window authority. More candidate search alone cannot resolve that source/evidence-contract issue or terminal-family proof.

No project-manager approval is claimed.
