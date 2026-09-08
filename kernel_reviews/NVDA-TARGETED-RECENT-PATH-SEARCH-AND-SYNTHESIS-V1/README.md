# NVDA targeted recent search and synthesis

Open **report.html** offline; Arabic companion **report.md**. The HTML bundles the canonical native reader and semantic chart-data tables. No login, server, network or fresh provider data is needed. Use Find for exact scenario aliases; no unverified clickable hierarchy is claimed.

This is a new bounded recent search, not the previous link-only replay. See `search_plan.json` and `selection_before_evaluation.json`, saved before new evaluations. The canonical JSON separates original role nodes, independent corrective evaluate-as hypotheses and observational links. `path_synthesis.json` and `link_coverage.json` preserve exact support and uncovered spans. `wave_table.json` is the complete exact role lookup; chart samples never replace the full ledger. The last captured bars stay visible after the last proposed endpoints.

## Practical findings

- 154 newly evaluated scopes: 67 Normal Impulse partial hypotheses (61 unique endpoint sequences, six repeated contexts), and 87 three-segment scopes yielding 174 separate Zigzag/Flat evaluate-as hypotheses (79 unique endpoint sequences). Only M1/M2 were replayed; no new sequence duplicates the 52 compared earlier full-digital/recent hypothesis contexts.
- New P004 outcomes: 36 satisfied, 31 violated. P005: 43 sufficient, 24 unresolved. 25 P004-invalid hypotheses remain invalid despite P005 sufficiency.
- All 243 routed links and 123 occurrence pairings were examined. Nineteen non-rejected interior observational edges reach at most **27 August 2026, Daily high 230.47**, through M2 -> D2026:1D:N6:S38. Zero full-boundary refinements and zero non-rejected Daily-to-intraday edges. This improves the prior July reach, not family proof.
- Independent intraday proposals extend into September. Four contextual corrective hypotheses share a genuine developing 4H endpoint at the captured **8 September 13:30 UTC low 229.06**; they are two windows times two evaluate-as families, not four confirmations. The 4H close is 230.0 at its own capture; 15m close 229.29 belongs to a different capture. No active Elliott wave is certified.
- The concrete recent correspondence blockers include Daily **216.20 vs intraday 216.18** on 11 August and Daily **207.25 vs 207.22** on 24 August. The earlier July 190.01/190.02 disagreement remains. No tolerance or replacement endpoint is applied.
- 257 eligible sequence contexts remain unvisited; 311 are nonfatally excluded by the operational movement domain, and 20 previous-coordinate occurrences are not re-evaluated. Available history is not exhaustively analyzed.

Six native annotated chart datasets retain captured trailing bars, with 936 wave-table rows and 26 proposed labels reconciled against original observations. Native packaging/structural checks passed. Installed Chrome failed the extraction environment check; enhanced chart placement, source-dialog and interaction checks are **not visually verified**. Semantic chart-data tables are available offline; no browser was installed.

## Saved data and previous baseline

Inputs are referenced in place, not copied or recaptured:

- `kernel_reviews/TRADINGVIEW-DIGITAL-DATA-AND-NVDA-ANALYSIS-BRIDGE-V1/`
- `kernel_reviews/NVDA-AGGREGATE-EXTREMUM-TIME-EVIDENCE-AND-RECENT-ANALYSIS-V1/`
- `kernel_reviews/NVDA-OBSERVATIONAL-HIERARCHY-LINK-AND-REPORT-V1/`

The preceding review manifest SHA-256 is `bb9e07cd16a8644074c19675b5b798a3c9e312a6cd06d729e194b96135df5058`. Its files/implementation are verified before this run, followed by its existing verification chain to all protected entries and original bridge inputs. Historical artifacts remain unchanged. Inventories: 11/7/0/0.

## Offline replay

From `C:\ElliottCodex\Runtime_WORKSPACE`, set `PYTHONPATH=src;tools;tests`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`, and TEMP/TMP to the existing `artifacts\tmp` inside Runtime. Use a **new, empty Runtime output path**, never this sealed baseline:

```powershell
python -B tools/nvda_targeted_recent.py --output artifacts/new-targeted-replay
python -B tools/nvda_targeted_recent_report.py --output artifacts/new-targeted-replay
```

The runner loads this stage's declared plan and refuses overwriting generated inputs/results. The report helper can regenerate report-only outputs for this stage while unsealed, with resolved Runtime path checks; it refuses after REVIEW_manifest.json exists. Neither helper edits historical baselines. The runner verifies protected and previous baselines, rebuilds exact live factories from saved observations, and checks caps before execution. A 1800-second operational limit records unvisited work rather than asserting completeness; machine-speed-dependent exhaustion must be compared from the ledger. No live retrieval is used.

Package `artifact.json` with the available Data Analytics native `deliver_portable_artifact.mjs --input <artifact.json> --output <report.html>`, with temporary files confined to Runtime. No extra chart runtime or browser installation. Render-only replay does not reevaluate methodology.

```powershell
python -B -m unittest test_nvda_targeted_recent test_observational_hierarchy
python -B -m unittest discover -s tests
```

Tests use genuine factory-issued synthetic fixtures explicitly labelled NOT_NVDA; synthetic data is never an experiment input. See tests/audit receipts for actual results and browser limitations. This additive hash baseline is logical sealing, not physical immutability or project-manager approval.
