# Human-assisted explicit-pivot candidate examples

Run either document with the existing CLI:

```powershell
$env:PYTHONPATH='C:\ElliottCodex\Runtime_WORKSPACE\src'
python -B -m elliott_runtime.manual_candidate_cli examples\explicit_pivot_candidate\grouped_p004_zigzag.json
```

Every pivot and child boundary is supplied explicitly by the caller. The
system does not search prices, detect pivots, split children, label waves,
select patterns, infer degrees, or infer visibility or P003 direction.

`grouped_p004_zigzag.json` explicitly supplies three child groups, a P004
pivot-role mapping, the `SINGLE_ZIGZAG` cardinality selector, and visibility.
The identifiers and grouping remain non-authoritative declarations.

`pivots_only_no_inference.json` contains four ordered pivots but no groups or
manual facts. It remains unresolved and demonstrates that pivot count and
price direction generate no methodology input.

The output is marked `NON_AUTHORITATIVE_REPORTING_VIEW` and cannot be loaded
back as methodology or certificate authority.
