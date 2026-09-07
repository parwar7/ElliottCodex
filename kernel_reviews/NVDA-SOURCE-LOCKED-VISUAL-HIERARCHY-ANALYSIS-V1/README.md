# NVDA source-locked visual hierarchy review

Start with `report.html` (portable Arabic narrative plus four key charts), or `report_ar.md` (authoring source). All ten full-resolution annotated views are in `annotated/`; seven unchanged market screenshots and their receipts are in `originals/`.

This is a human visual hypothesis review, not an engine run. A and B are unranked, mutually separate ancestry interpretations. A current-component assignment is conditional; no family, degree, exact historical endpoint or completion authority is issued. The report intentionally does not claim compliance with the operational ANALYSIS_OUTPUT_SCHEMA, which would require fields outside this user-authorized no-ranking/no-forecast review.

## Evidence and reproduction

- `hierarchy.json`: one parent per node, approximate endpoint evidence, current-position conditions and unresolved checks.
- `annotations.json`: source-image coordinates, exact local node/evidence links and output names; coordinates locate visual regions, not market operands.
- `capture_provenance.json`: original capture times, viewport ranges, BATS/Cboe One identity, settings and unknowns. A viewport ending beyond observed bars is not available future history.
- `source_references.json`: protected references/classes; local S-prefixed reference keys are not protected principle IDs.
- `coverage_and_audit.json`, pre/final integrity receipts, validation receipt and hash manifest accompany the review.

`prepare_pack.py` regenerates the authored annotation exports from saved screenshots without network calls or methodology evaluation. It needs existing Pillow and fonts; the original local capture pack is needed only for its initial three-image provenance check/copy. It never redraws market prices. The capture-only MCP helper is retained with local, untracked capture artifacts, outside this committed pack; its successful tool sequence is recorded in the audit. Do not recapture merely to replay this report. No installation/configuration, authentication material or protected source media is included.

The HTML is generated from canonical `artifact.json` through the installed Data Analytics portable report builder, not a second analytical implementation. `report_ar.md` is its editable prose source, not a separate claim set.

HTML validation and structural/payload verification passed. Compatible Chromium headless-shell was unavailable; browser layout and source-dialog QA were not performed. All ten annotated PNGs were visually inspected independently.

Original saved TradingView layouts/drawings were not saved or edited. Temporary tab only, Autosave off. Native OHLCV export and native drawing were not established; exported image copies were annotated locally. Historical baseline files, Kernel, runtime implementation and tests are unchanged. No full regression or expensive pipeline rerun belongs to this artifact-only stage.
