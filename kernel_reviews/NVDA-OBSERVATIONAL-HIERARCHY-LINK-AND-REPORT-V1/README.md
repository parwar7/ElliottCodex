# NVDA observational hierarchy links

Open **report.html** locally. Arabic companion: **report.md**. No server, login, network, new capture or provider required. The HTML bundles the native reader; semantic chart tables remain readable if enhanced rendering cannot start. Browser Find can locate a hypothesis alias. We do not claim unverified click-through navigation or visually verified chart labels.

## Practical result

One non-rejected observational edge: **M2 role 5 ↝ JULY:1D:S0**. It is interior evidence, not complete subdivision. Its finer endpoint is the Daily high **202.0**, bar **31 July 2026 13:30 UTC**. The last captured Daily bar is **8 September 2026 13:30 UTC**. No connected proposed path reaches that last bar. No active wave, family validity, degree, ranking or trading claim.

150 contextual links: 100 missing-boundary, 37 outside the supported region, 8 unresolved boundary-overlap/crossing, 5 interior. Four of those five interior children are P004-rejected. 78 rejected link contexts are not 78 unique invalid waves. All 50 available occurrence pairings are retained. There are 27 existing hypotheses (M1/M2 plus the previous 25), 46 boundary evidence records, zero new candidate searches or data captures, and zero new Kernel ancestry links.

Exact gaps: the sole supported child leaves the interval from the end of the 13 October 2022 occurrence envelope to the start of 7 July 2026 unrepresented, and from the end of 31 July to the start of 4 September unrepresented. Its July internals are unresolved. The July Daily low 190.01 remains unmatched against observed intraday 190.02. Direct M2-to-1H/15m links lack October 2022 history. No interpolation or epsilon was used.

## Files and reading order

1. `report.html` / `report.md`: Arabic answer, proposed paths, three separately sourced annotated charts, all alternatives and original indicator context.
2. `canonical_hierarchy.json`: independently issued hypotheses, their original role nodes, and **separate** observational links. Serialized IDs are records, never restored runtime authority.
3. `proposed_paths.json`: non-rejected supported paths only. No leaf reaches its latest captured bar.
4. `link_coverage.json`: exact original aggregate boundaries, independent finer endpoints, all paired uncovered intervals, and missing boundaries.
5. `wave_table.json`, `chart_rows.json`, `indicator_evidence.json`: reconciled display values.
6. `contract_boundary.md`, `search_plan.json`, `planned_links.json`: implementation boundary and predeclared work domain.
7. Integrity, tests, audit and `REVIEW_manifest.json`: additive logical hash seal, not physical immutability or project-manager approval.

## Saved inputs and predecessors

Referenced in place; no raw captures or media copied:

- `kernel_reviews/TRADINGVIEW-DIGITAL-DATA-AND-NVDA-ANALYSIS-BRIDGE-V1/`: original BATS:NVDA / Cboe One native snapshots. NASDAQ:NVDA is the listing identifier only.
- `kernel_reviews/NVDA-DIGITAL-MULTIDEGREE-ANALYSIS-AND-REPORT-V1/`: original M1/M2 saved selection configuration and results.
- `kernel_reviews/NVDA-AGGREGATE-EXTREMUM-TIME-EVIDENCE-AND-RECENT-ANALYSIS-V1/`: original 25 recent selections, occurrence contract, source references. Manifest SHA-256 **5d19c4d7530f56f2a319c16b9cbab3c21ffe8ffc1075aafe79a4a256aa19089a**.

This stage does not supersede their implementation hashes or approved results. It implements an additional observational link, leaving their prohibition on altering issued ancestry intact. Kernel/shared contracts, protected state and every historical baseline remain unchanged.

## Offline replay

From `C:\ElliottCodex\Runtime_WORKSPACE`, use the installed Python 3.12+ runtime and set:

```powershell
$env:PYTHONPATH='src;tools;tests'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -B tools/nvda_observational_hierarchy.py --output artifacts/observational-replay-new
```

The output directory must be fresh; the runner refuses to overwrite artifacts. It verifies the previous manifests and all protected entries, reconstructs exact live factory objects from the original hashes/selections and computes new links without changing any selected hypothesis. No credentials or network needed. Byte-for-byte equality of timestamps in integrity receipts is not expected; compare canonical_hierarchy.json and observed values/outcomes. This replays only 27 saved hypotheses, not the expensive full-history pipeline.

For report-only replay against the sealed canonical stage evidence, without rebuilding hypotheses:

```powershell
python -B tools/nvda_observational_hierarchy_report.py --output artifacts/observational-report-new
```

The report writes artifact.json and report.md to a fresh Runtime directory. Package artifact.json using the installed Data Analytics `deliver_portable_artifact.mjs --input <artifact.json> --output <report.html>` with TEMP/TMP inside Runtime. Do not install a browser. The portable builder is external tooling, not a project methodology dependency; the delivered HTML itself requires no tool installation.

Tests:

```powershell
python -B -m unittest tests.test_observational_hierarchy tests.test_nvda_observational_hierarchy_report
python -B -m unittest discover -s tests
```

Original metadata remains visible: regular session 09:30–16:00 America/New_York, nonsynchronous 8 September 2026 captures, unknown split-adjustment semantics, forming/revised flags, and incomplete holiday/early-close coverage. A unique observed match is not global uniqueness. Indicators retain the original later Daily study capture; no new interpretation is attached.
