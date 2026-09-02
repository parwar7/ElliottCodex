# P003-V1

This additive logical methodology baseline records:

`P003_ONE_LARGER_DEGREE_SEARCH_THEME`

The behavior maps only a caller-established relation to the one-larger-degree
direction into a structural search theme:

- `WITH` -> `MOTIVE`
- `AGAINST` -> `CORRECTIVE`
- `UNRESOLVED` -> `UNRESOLVED`

`MOTIVE` and `CORRECTIVE` are search themes only. They do not identify or
validate a motive or corrective pattern, and no P003 result establishes
candidate-wide structural validity.

## Locked public behavior

- Function: `map_p003_one_larger_degree_theme(candidate)`
- Input: `P003OneLargerDegreeThemeInput`
- Result: `P003OneLargerDegreeThemeResult`
- Protected principle ID: `P003`
- Source classification: `SOURCE_DEFINITION`
- Execution role: `STRUCTURAL_CONTEXT`
- Fatality: always `false`
- Structural-invalidity producer: no
- Certifiable result: no

The uppercase relation, theme, status, and execution-role tokens are
behavior-local Runtime vocabulary. The protected output schema uses lowercase
relation/theme values; no schema adapter or output integration is implemented
by this behavior.

## Explicit exclusions

P003 does not establish the relation it receives. It does not inspect price or
bars, detect pivots, infer direction or degree, map timeframe to degree,
identify or validate a pattern, generate candidates, evaluate evidence or
Fibonacci, rank counts, certify invalidity, invoke another methodology
behavior, or access Runtime integrations.

Missing, malformed, case-changed, or whitespace-padded input fails closed to a
nonfatal unresolved Runtime diagnostic without normalization. This diagnostic
handling is Runtime policy and is not promoted into protected methodology.

## Baseline status

This is a logical development baseline. It remains writable and is not
physically immutable, cryptographically sealed, ACL-protected, or isolated
from a hostile process.
