# NVDA — aggregate extremum occurrence evidence and recent independent hypotheses

Open **report.html** locally; Arabic companion **report.md**. Neither is live, a validated count, a ranking, or a trading signal.

## Practical result

- May Monthly high **236.54** matches the saved Daily bar of May 14 and the 15m bar **19:00–19:15 UTC**. This identifies a bar interval, not the exact trade instant, orthodox wave end or completion.
- July Monthly/Daily low **190.01** matches the July 29 Daily bar, but not the saved 4H/1H/15m lows. The observed intraday low **190.02** is not substituted. The cause remains unresolved.
- September Monthly high **234.76** matches the September 4 15m bar **14:15–14:30 UTC**. The Monthly bar is still forming in its own frozen snapshot.
- 16 predeclared searches produced 25 fresh independent hypotheses: P004 satisfied 11 / violated 14; P005 sufficiency established 17 / unresolved 8. Eleven rejected hypotheses also meet P005 sufficiency and remain rejected.
- Zero new certified parent-child attachments to M1/M2. Existing original subjects, five-slot bindings, aggregate endpoints and outcomes remain unchanged. Every new hypothesis has its own subject, binding and P004/P005 evidence.

The latest saved 15m observation is from September 8, 2026, captured at 13:53:45.992 UTC, with close 229.29 in a forming bar. It is not a live quote. The hourly and 15m local proposals are independent alternatives, not a stitched count; current wave position remains unresolved.

## Evidence index

- `search_plan.json`: fixed windows, geometry width, explicit operational tie policy, candidate domain and budgets recorded before evaluation. Occurrence matching itself never tie-breaks.
- `selection_before_evaluation.json`: every considered six-pivot window and pre-evaluation selection. 575 domain exclusions, 438 eligible unvisited windows, 25 selected. Exclusion is not structural invalidity.
- `occurrence_evidence.json`: 21 records, including every Monthly-to-Daily match and its finer inspections. Original timestamps and all matching bars remain separate. Each includes interval basis, all matching occurrences, raw hashes, capture compatibility/limitations and old parent context where applicable.
- `canonical_analysis.json`: 25 new hypotheses / 150 nodes, original and new IDs, exact represented endpoints, own P004/P005 traces, operational dispositions, original-parent preservation receipt. JSON does not restore live object authority.
- `wave_table.json`: all node/role links and exact date/field/price exports.
- `artifact.json` / `chart_rows.json`: canonical offline-report definition and actual SQLite-projected native data. Three charts; plotting coordinates/log10 are display-only. No market-price redraw or resampling.
- `indicator_evidence.json`: ten checked Daily indicator values from the separate later study capture. No new indicator computation or interpretation.
- `independent_reconciliation.json` / `raw_audit.json`: raw-input comparisons and all chart/table reconciliation.
- `contract_boundary.md`: current interval authority and the precise deferred parent-link gap.
- `source_refs.json`: references to unchanged approved source research, not newly promoted rules.
- `test_results.json`, `full_tests.log`, `browser_audit.json`, `audit.json`: verification and limitations.
- `pre_integrity.json` / `final_integrity.json`: all 30 Brain and 21 Source entries, not manifest-only checks.
- `REVIEW_manifest.json`: additive logical seal; historical baselines not rewritten. Workspace is writable, so this is not physical immutability.

No large input captures are duplicated. Reused inputs are in `kernel_reviews/TRADINGVIEW-DIGITAL-DATA-AND-NVDA-ANALYSIS-BRIDGE-V1/`, manifest SHA-256 `8821c441cbb1e72bfe8d99f4474b781316ec9f18d3af82fffd344bc73f0beb03`. Prior analysis is `NVDA-DIGITAL-MULTIDEGREE-ANALYSIS-AND-REPORT-V1`, manifest `2538c3c9d17e5cee965d6a368574b70405d589a81698bbbdfcde75cca6d7fdbe`.

## Replay without network

From `C:\ElliottCodex\Runtime_WORKSPACE`, using the existing Python environment:

```powershell
$env:PYTHONPATH='src;tools;tests'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/nvda_aggregate_recent.py --output artifacts/nvda-aggregate-replay-new
```

Use a new Runtime directory. This verifies both input baselines and every protected entry, reconstructs genuine original M1/M2 factory objects only, then runs the bounded new scopes against the same snapshots. It does not rerun the full earlier multidegree pipeline. Stable proposal IDs/prices/counts should match; integrity receipt timestamps change. Later cache hardening only rejects substituted cache identities, not untouched inputs.

Report-only replay (no methodology execution):

```powershell
python -B tools/nvda_aggregate_recent_report.py --output artifacts/nvda-aggregate-report-new
```

This intentionally renders the frozen canonical evidence in this approved review pack, rather than silently ingesting a different replay. Package its `artifact.json` using the installed Data Analytics `deliver_portable_artifact.mjs --input ... --output .../report.html`. Keep TEMP/TMP beneath Runtime. No browser/package installation is performed.

Focused tests: `python -B -m unittest test_aggregate_extremum test_nvda_aggregate_recent_report -v`.

## Display limitation

The native builder validates and bundles the offline report and semantic data tables. An installed Chrome attempt failed `browser_environment_mismatch`; no compatible default headless-shell was available. Therefore actual chart label placement, enhanced source dialogs and navigation interactions are **not visually/browser verified** in this environment. This is recorded, not represented as a passed browser test. No browser was installed or plugin changed.

The static fallback has no matching `id` targets for its in-page navigation links (see `html_structure_audit.json`). Use browser Find with the exact scenario ID, or the Markdown companion's explicit anchors. Enhanced-reader navigation is unverified, not assumed to fix this. No external resource tags were found; the canonical chart payload is bundled and reconciled.

## Preservation

Only five new Runtime source/test helpers and this new review pack are added. No existing executable file, test, shared contract, protected file or historical baseline is modified. Inventories remain **11 / 7 / 0 / 0**. P004/P005, P006, Flat/Triangle freezes, SOURCE_DERIVED_BASE_CASE_NOT_FOUND and legacy `analyze = NOT_IMPLEMENTED` remain unchanged. No project-manager approval is claimed.
