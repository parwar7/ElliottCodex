# NVDA geometric swing candidate quality

## Scope and replay

Approved base: fae333e0b02a9f348edadb4c0b43df3ef63a6751.
This additive stage improves the selected geometric search domain, not Elliott
validation. It preserves the prior equal-index H0467 proposal as historical
evidence and never rewrites its original P004/P005 outcomes.

From C:\ElliottCodex\Runtime_WORKSPACE, with an unused output directory:

~~~powershell
$env:PYTHONPATH='src;tools'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/nvda_geometric_swing_quality.py --output runs/NVDA-swing-quality-replay
~~~

The command verifies and reuses NVDA-BOUNDED-ANALYSIS-REPORT-V1/inputs,
whose input-manifest SHA-256 is
bb8d73a6ace250a5d8815cd215760b210913db715fb43d6ef3327a8cb535424e.
The capture was collected on 6 September 2026; latest observations are dated
4 September 2026. No fresh Yahoo call, resampling, input correction or new data
capture occurs here. Existing provider null-OHLC omissions and warnings remain
in input metadata. Historical exploration is not an as-known-at-the-time backtest.

## Read the result

- report/report.md: technical comparison, exact movement samples and caveats.
- report/results.json: complete hypotheses, endpoint prices/fields/provenance,
  parent/requirement identities, source geometry, all window dispositions,
  duplicate-coordinate contexts and current-position dependencies.
- report/search_plan.json and configuration.json: pre-execution search policy.
- report/candidates.csv and endpoints.csv: existing lossless evidence exports;
  new geometric-domain classification and window diagnostics are in JSON.
- tests.json, audit.json and final_integrity.json: verification receipts.

This is a bounded operational report, not a completed analysis under the protected
full-count output schema. No Preferred/Alternative ranking, current-wave claim,
complete family validity, forecast, targets or trade decision is supplied.

## Authority and limits

The new Runtime module selects an explicit geometric domain: nonzero consecutive
price movements alternate sign. Comparisons use represented finite values
directly, without subtraction rounding or tolerances. This is not the protected
Elliott alternation guideline and cannot issue structural invalidity.

Monthly local-extrema windows 2, 4 and 8 use the existing LAST tie policy and
developing-pivot handling. No emitted pivots are consolidated or spliced across
discovery objects. Same-kind pairs and ties are reported, not automatically
relabelled. Existing discovery excludes ambiguous same-bar high/low extrema;
this stage does not infer their hidden order. Wider windows are not Elliott
degrees or proof of major waves.

Every consecutive six-pivot scope is classified, then one earliest eligible
scope per scale and historical region is selected. Region boundaries are
1999–2007, 2008–2016, 2017–2026. Selection is outcome-independent. All unvisited
starts, cross-region exclusions and domain exclusions remain explicit. Four
neutral candidates at most arise per selected scope: three consecutive
three-segment candidates and one five-segment candidate. No all-subset search.

Only scale-2 selected roots explore one existing Monthly→Weekly child layer.
The other roots and all deeper levels remain unvisited. Child evidence retains
the exact existing requirement and full finer-pivot tuple, so child results use
the existing unfiltered contract. Their geometric-domain status is reported
separately. No claim is made that the new parent filter governs those children.
The exact limitation and minimal deferred proposal are in child_scope_boundary.md.

All candidate origins and duplicate coordinate contexts are preserved. Repeated
coordinates do not create independent confirmation. Current position remains
unresolved; proposed roles and developing pivots do not establish an active wave.

## Preservation

No existing code, tests, Kernel/shared contract, protected file or historical
baseline is modified. Methodology stays 11; structural producers 7; validated
family producers and issuances 0/0. P004/P005 semantics, P006, Flat/Triangle
freezes, SOURCE_DERIVED_BASE_CASE_NOT_FOUND and legacy analyze NOT_IMPLEMENTED
remain unchanged. This is a logical hash baseline, not physical immutability
or project-manager approval.

The analytics validation/reporting skills informed exact lookup tables, source
checks and caveats. The user-requested existing Markdown/JSON/CSV surface takes
precedence over the skill's default UI/HTML delivery. Tables are operand and
ancestry lookups, not visual fit charts; no chart or reporting framework is added.
Technical structure: summary, comparison, definitions/method, coverage/outcomes,
exact samples, limitations and next question. Codex Process Jobs explicitly
rejects Windows in this installation, so finite foreground execution is used.
