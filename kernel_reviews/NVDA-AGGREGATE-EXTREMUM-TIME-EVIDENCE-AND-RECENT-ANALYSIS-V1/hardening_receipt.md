# Pre-seal Runtime identity hardening

An adversarial check during this stage found that a newly issued extremum-evidence object rejected changed provenance content, but accepted replacing `finer.observations.provenance` with an equal-content `dataclasses.replace(...)` instance. This was a defect in the **new Runtime layer**, not the existing Kernel or approved methodology. No baseline had been sealed.

Minimal observed reproduction:

```python
e = find_extremum_occurrences(aggregate, aggregate.observations.bars[0], "high", finer)
object.__setattr__(finer.observations, "provenance", replace(finer.observations.provenance))
e.validated()  # accepted before this stage's hardening; rejected afterward
```

Correction: issuance identity evidence now pins nested observation provenance, symbol, timeframe, quality, bar provenance and source-resolution records. The geometry cache also pins exact discovery, pivot tuple, individual pivots, their parameter objects and provenance tuples. Equality of content cannot substitute these identities, and failed validation does not refresh captured evidence.

New regressions cover the original reproduction, equal nested provenance/timeframe/symbol/quality/bar provenance/source resolution, equal discovery and pivot tuple/config replacement, plus repeated rejection. Untouched factory objects still pass and produce their own original P004/P005 evidence.

The first full-suite attempt was stopped after verifying its exact process identity, because this relevant audit finding required a code change. Its incomplete output is preserved in `interrupted_full_tests.log`; it is **not a full-suite pass**. `full_tests.log` and `test_results.json` record the complete invocation after final hardening. No test was weakened. This is the explicit reason for a second full-suite launch, not an unexplained pipeline rerun.

The guards do not change prices, calendar membership, exact matches, pivot discovery, search selection, methodology comparisons or valid-input results. Existing approved source/tests/contracts and historical artifacts remain unchanged. No protected or shared-contract repair was needed.
