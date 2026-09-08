# NVDA-RECENT-COMPONENT-VISUAL-RESOLUTION-V1

Start with **[Arabic report](report_ar.md)**. Four full-resolution annotated views are in `annotated/`; seven untouched MCP screenshots and individual capture receipts are in `originals/`.

Approved repository base: `25b56d9a8b0da62420546c1c9ad0baef7e64a755`.
Prior review manifest: `1975bc826517b9783ee4d4f826358eca99bf68795b61829013eef680fdbacb5e`.

This is additive provisional visual research, not an engine run, methodology baseline, verified family, or project-manager approval. L1 and L2 are instantiated independently under prior A and B; chronological regions and observation boundaries are not certified wave endpoints. Read the report's session and current-position qualifications before interpreting any labels.

## Files and reproduction

- `hierarchy.json`, `node_table.md`: exact local node IDs, parent links, source references, approximate regions and prior mappings.
- `annotations.json`: deterministic pixel callouts. Coordinate space is 2048x1112; originals are 2534x1376. No generated market pixels or synthetic price lines.
- `capture_provenance.json`: dates, metadata, price/session separation and capture budget.
- `source_references.json`: precise protected references; source facts separate from analyst hypotheses.
- `pre_integrity.json`, `final_integrity.json`: all 30 Brain and 21 Source entry checks.
- `audit.json`, `validation_receipt.json`, `REVIEW_manifest.json`: bounded audit, artifact tests and byte hashes.

To regenerate **only report data and exported annotations**, using the existing Python/Pillow environment:

```powershell
python -B kernel_reviews/NVDA-RECENT-COMPONENT-VISUAL-RESOLUTION-V1/build_review.py
python -B kernel_reviews/NVDA-RECENT-COMPONENT-VISUAL-RESOLUTION-V1/validate_review.py
```

These helpers never navigate TradingView, call an Elliott evaluator, retrieve prices or write protected files. They generate files only in this new review directory; do not rerun against a frozen pack to claim the original capture can be refreshed. The source inputs are saved screenshots, not a reproducible live-market request. No credentials, MCP configuration, profiles, source media or old history inventories are copied.

Packaging uses a short Markdown report and original-resolution PNG callouts; no extra chart metric, dashboard framework or browser dependency was added. No browser-rendered HTML QA is claimed. Original and annotated images were inspected directly. Full regression/pipeline reruns are intentionally out of scope.
