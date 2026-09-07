# NVDA linked historical hypotheses

Open `chart.html` directly in a current browser. It is standalone: its data, SVG renderer, styles and navigation are embedded. No credentials, server, installation or network access are needed. `canonical.json` is the identical evidence projection available from the export button. JavaScript is required for interaction; the JSON remains independently readable.

## What the viewer shows

- All 334 saved Monthly close observations, from the provider's 1 January 1999 bar label to 4 September 2026, with a shaded selected-hypothesis interval. These dates are bar labels, not certified completion or IPO-wave origins.
- The saved Yahoo capture requested 6 September 2026 at 23:20:10 UTC. Per-resolution actual ingestion times and coverage are in evidence details and JSON. Monthly/Weekly final observations are 4 September 2026 at 20:00 UTC; Daily ends at 13:30 UTC. No fresh capture occurred.
- Exactly 27 parent hypotheses and 63 child-context occurrences from the approved scale-2 scoped search. This is not exhaustive full-history analysis. Parent proposal windows are historical, and every current-wave position remains unresolved.
- Exact saved role names, endpoint timestamps, price fields, represented prices, ratios, binding IDs, snapshots, parent hypothesis IDs and requirement IDs. Generic child slots are not relabeled ABC or 1–5. Normal Impulse's existing 1–5 slots remain proposed metadata only.
- All 84 unresolved internal requirements, source search exclusions and budget-unvisited contexts. No fabricated child/deeper links. A Normal Impulse parent has no recorded internal-requirement child links in this capture; similar coordinates do not provide one.

Choose a parent from the selector. Open a child through its originating requirement and use **Return to linked parent** to switch interpretation. Only one interpretation is drawn at a time. The small chart fits that hypothesis; the overview always retains the full Monthly date range. Exact role data is in the table. Expand evidence details for technical identity/provenance. Arabic instructions are included in the HTML.

## Evidence and replay

Approved base: `6ee23ae8859e19b34caf64a8ad3f910f73fe407f`.

The exporter verifies every artifact in `kernel_reviews/EXACT-SCOPED-CHILD-SWING-SEARCH-TRANSPORT-V1/EXACT_SCOPED_CHILD_SWING_SEARCH_TRANSPORT_manifest.json`, locked to SHA-256 `414d11c24974db3c05114762325025ddbb23dbaebf18d5e83687fe71dcff1019`. It uses only its **after** results, never merges the before/after runs. It verifies all four normalized captures against `kernel_reviews/NVDA-BOUNDED-ANALYSIS-REPORT-V1/inputs/input_manifest.json`, SHA-256 `bb8d73a6ace250a5d8815cd215760b210913db715fb43d6ef3327a8cb535424e`.

From `C:\ElliottCodex\Runtime_WORKSPACE`, export to a **new** folder beneath Runtime:

```powershell
$env:PYTHONPATH='src;tools'
python -B tools/nvda_linked_hypothesis_chart.py --output chart-replay
```

Existing files are never overwritten by the exporter. It reads and audits saved results/observations only; it does not invoke pipeline generation or Yahoo retrieval. No raw captures or large historical hash inventories were copied into this baseline. The JSON includes close arrays for Monthly/Weekly/Daily and the projected saved endpoint evidence; the viewer uses Monthly overview and Monthly/Weekly detail. Close prices are background context, never substituted for the high/low endpoint operands.

Focused tests:

```powershell
$env:PYTHONPATH='src;tools;tests'
python -B -m unittest discover -s tests -p test_nvda_linked_hypothesis_chart.py -v
```

Browser QA uses the already-installed Playwright package and Edge, without downloading anything:

```powershell
$env:NODE_PATH='C:\Users\Parwa\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
node tools/verify_nvda_linked_chart.cjs kernel_reviews/NVDA-LINKED-HYPOTHESIS-CHART-V1/chart.html
```

The browser verifier creates an isolated `chart-browser-qa-*` directory only beneath Runtime and reports its screenshot path. After inspection, this stage's QA profiles were retained recoverably under the already-ignored `htmlcov/linked-chart-qa/` Runtime directory; none are committed baseline evidence. A recursive cleanup command was rejected by the tool policy; no deletion workaround was attempted. See `tests.json` for the receipt. Other browsers, touch input and print layout are not certified by the Edge checks.

## Authority and compatibility boundary

Rendering cannot issue or restore live evidence authority. JSON IDs are faithful records, not replacement identity proofs. Existing saved-evidence audits verify prices, roles and ancestry against preserved observations; the viewer does not deserialize certified objects or call methodology factories.

P004 rejection remains effective even when P005 percentage sufficiency is established (two parent occurrences here). P005 is not full rule or family validation. Inventory remains **11 / 7 / 0 / 0**. P006, Flat/Triangle freezes, `SOURCE_DERIVED_BASE_CASE_NOT_FOUND` and legacy analyze `NOT_IMPLEMENTED` are unchanged. No ranking, active-wave inference, confidence, indicators, forecast or trading is added.

This additive logical baseline introduces rendering only. It supersedes no historical implementation hashes or methodology guarantees. All prior tracked files and baselines remain unchanged. It is not a physical seal or project-manager approval.
