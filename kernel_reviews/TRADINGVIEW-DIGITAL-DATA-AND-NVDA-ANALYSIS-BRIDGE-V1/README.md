# TradingView digital NVDA bridge

Additive stage based on `b6fc12d110a4dded5db084ac664c105a89aa2726`.
No project-manager approval is claimed. This is a data bridge and bounded
operational/analytical review, not a certified Elliott count.

## Reading order

Open `report.html` (portable Arabic report), then `data_quality.json`,
`pipeline_results.json`, and `audit.json`. `input_manifest.json` pins six
unaltered captures. `reconciliation_*.json` records later actual data-window
readings; later forming-bar revisions are not silently applied to frozen data.
The initial 15-minute reconciliation missed its earliest loaded bar; the
`_completed` receipt follows one additional ordinary history request. It does
not change the frozen 15-minute dataset.

## Replay, without network

From Runtime, use the project's existing Python environment:

```powershell
$env:PYTHONPATH='src'
python -B tools/nvda_tradingview_replay.py --quality --output artifacts/tv_quality_replay.json
python -B tools/nvda_tradingview_replay.py --output artifacts/tv_pipeline_replay.json
python -B -m unittest discover -s tests -p test_tradingview_digital.py -v
```

Output paths must be new and inside Runtime. Input hashes are checked before
normalization. The unchanged existing `run_scope` factory path supplies exact
parent/child observation bindings and audits P004/P005 result identities. Its
legacy `nvda-post-p005` ID namespace is retained; that is NOT a Yahoo source
claim. Replay creates fresh identities, not restored authority. No Yahoo API
is invoked. Nominal month/week resolution labels do not assign wave degree.

## Local MCP integration

`tools/tradingview_digital_tools.py` exposes `register_digital_tools(mcp,
existing_cdp_client, require_authorized_unsaved)`. The supplied guard must
verify the exact authorized temporary chart and visibly verify Autosave OFF.
This stage used the existing local capture-server transport through genuine
MCP calls. It did not change MCP configuration or install another server.
The local launcher and machine-specific target IDs remain untracked.

Registered tools: `tv_digital_state`, `tv_digital_configure`,
`tv_digital_request_history`, `tv_digital_snapshot`,
`tv_digital_data_window_samples`, `tv_digital_reconcile_times`,
`tv_digital_indicator_snapshot`, `tv_digital_add_macd`,
`tv_digital_show_sample`. No arbitrary-JavaScript, trading or certificate tool.
The deployed desktop's internal loaded-series API is version-sensitive;
repeat context/schema/data-window checks after an application change.

The public chart `exportData()` method returned **Data export is not supported**.
The working path is the already accessible chart's loaded historical OHLCV
store, not a quote widget, screenshot digitization or entitlement bypass.
Ordinary `requestMoreData` calls load only what this account returns.
Native `240` was verified as 4H. No resampling.

## Frozen context

Actual symbol BATS:NVDA, feed Cboe One, listing identifier NASDAQ:NVDA;
regular session 09:30–16:00 America/New_York, chart timezone Etc/UTC, USD.
Dividend adjustment false; back-adjustment property true; split-adjustment
semantics independently UNKNOWN. No inference that the back-adjustment flag
certifies split policy. Data are not combined with Yahoo or 24H observations.
Daily is not asserted equal to aggregated intraday; volume units and feed
aggregation across resolutions remain unverified.

UNIX values are native bar timestamps, retained as aware UTC. Monthly/weekly
labels may precede the first trading day represented. Calendar-unaware elapsed
gap diagnostics include closures and variable months, not proven missing bars.
No gaps filled; no null volume converted to zero; no duplicate bars accepted.
Chart decimal-format matching is presentation QA only, not a rule tolerance or
claim of original decimal precision. P005 keeps exact represented float ratios.

## Boundaries

Historical baselines, protected entries, Kernel, P004/P005, P006 and
Flat/Triangle freezes remain untouched. Methodology 11; structural producers
7; validated-family producers/issuances 0/0. Base-case proof remains blocked.
Indicators are returned study observations, not Elliott confirmation rules.
No locally invented EWO definition, ranking, targets, forecast or trade signal.

The report is packaged with the existing Data Analytics portable renderer;
there is no new chart framework. Canonical input is `artifact.json`.
