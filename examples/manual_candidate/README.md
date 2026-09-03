# Human-readable manual candidate examples

Run an example from the repository root:

```powershell
$env:PYTHONPATH='C:\ElliottCodex\Runtime_WORKSPACE\src'
python -B -m elliott_runtime.manual_candidate_cli examples\manual_candidate\p004_reviewed.json
```

The input declares structure manually. It is not a methodology result, proof,
certificate, market-data interpretation, or source authority. The JSON emitted
on standard output is a non-authoritative diagnostic snapshot; it cannot be
loaded back as methodology authority.

`p004_reviewed.json` demonstrates one explicit P004 declaration whose bounded
workflow can report `CURRENT_SUPPLIED_SCOPE_REVIEWED`. That status is not
validity, completeness, confirmation, family validation, rank, or trade advice.

`cardinality_unresolved.json` demonstrates one explicit single-zigzag selector
with two explicitly ordered children. It selects only the existing P007 check;
the CLI does not infer a family or behavior from the child count.
