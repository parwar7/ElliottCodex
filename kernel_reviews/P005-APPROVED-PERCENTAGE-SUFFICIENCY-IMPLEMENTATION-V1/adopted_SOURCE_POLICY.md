# Source Policy

## 1. Authoritative source set

The Elliott reasoning in this repository is locked to:

1. User-provided Elliott Wave educational videos, Volumes 1–10.
2. User-provided matching transcripts.
3. User-provided Frost/Prechter *Elliott Wave Principle* book.

This policy intentionally excludes:

- web Elliott material;
- other Elliott books or courses;
- prior ChatGPT conversations;
- remembered model knowledge;
- third-party TradingView Elliott counts;
- modern indicator folklore.

If the source set does not support a claim, mark it `UNRESOLVED` rather than importing an answer.

## 2. Theory versus market data

Market data is not Elliott theory.

Allowed external data:
- OHLCV;
- timestamps;
- splits and corporate actions;
- instrument metadata;
- market-session information;
- chart screenshots.

Not allowed as theory without explicit user approval:
- analyst wave counts;
- blog definitions;
- Elliott rules from websites;
- third-party pattern scanners;
- indicator-based Elliott conventions.

## 3. Evidence classes

Every extracted concept belongs to one class:

- `SOURCE_RULE` — the source treats it as compulsory within its stated pattern scope.
- `SOURCE_DEFINITION` — structural definition or terminology.
- `SOURCE_GUIDELINE` — a tendency that helps rank valid counts.
- `SOURCE_OBSERVATION` — personality, volume, breadth, psychology, fundamentals, etc.
- `SOURCE_TRADING_PRACTICE` — execution or money-management practice, not an Elliott law.
- `UNRESOLVED_CONFLICT` — the source material is ambiguous, internally conflicting, or incomplete.

## 4. Conflict handling

When the book and seminar differ:

1. preserve both statements;
2. record their source;
3. prefer an explicit later correction when the seminar clearly says an earlier statement should not be treated as a rule/guideline;
4. do not use outside doctrine to reconcile them.

### P005 measurement-policy exception (user-authorized project policy)

For P005 in normal impulses only, the user has authorized the approved Frost/Prechter book's percentage-based sufficient condition (page 31) to control its conflict with the Volume 10 both-bases statement (00:28:14.840-00:28:25.640). Arithmetic failure alone must not override that sufficient condition.

This is a narrow project-policy decision, not new source evidence, an explicit source correction, or general book precedence. Preserve the original conflict and source classifications: the book's sufficient condition and the seminar statement remain SOURCE_RULE; the book's almost-always arithmetic statement remains SOURCE_GUIDELINE.

Do not convert the sufficient condition into an exhaustive pass/fail definition. Exact ties, formulas, operand authority, numerical conventions and developing-wave timing remain unresolved. P005 remains unimplemented; this exception grants no implementation authority.

This exception refers to the approved book SHA-256 c78e1a29b717445e01de421370a627c440b127cf42c34646526a495b8c42ab9e under SOURCE_MANIFEST SHA-256 ad774642080c9112796510c01697fd70f2499c828aede547de0b3d39429ad089.

### P005 approved measurement contract (USER_APPROVED_PROJECT_CONVENTIONS)

The subsequent P005-APPROVED-PERCENTAGE-SUFFICIENCY-IMPLEMENTATION-V1 authorization permits only the following bounded implementation. It supersedes the preceding historical unimplemented statement and unresolved measurement conventions only within this scope; it does not erase their source conflict or create new source evidence.

- For each peer wave independently: R = 100 * abs(end - start) / start.
- Accept only finite, strictly positive prices. Proposed waves 1, 3, and 5 must move in the explicit hypothesis direction; zero or opposing movement is unsupported.
- Operands are exact identity-bound proposed endpoints, not certified orthodox endpoints.
- Results apply only to the immutable input snapshot. Required endpoints still marked developing remain unresolved. Missing endpoint eligibility evidence remains unresolved. Absence of developing geometry does not certify Elliott completion.
- If R3 > R1 OR R3 > R5, establish ONLY the book's sufficient condition. Otherwise remain unresolved, including tied-shortest/all-equal cases. Do not infer structural invalidity.
- Compare the exact represented input values without rounding, epsilon, tick buffers, or invented precision. Convert stored floats to their exact represented ratios before subtraction or division; do not stringify them and claim original decimal precision.
- These measurement conventions are USER_APPROVED_PROJECT_CONVENTIONS, not newly discovered source rules. Arithmetic failure alone must not override established percentage sufficiency. Genuine P004 invalidity remains fatal to its exact hypothesis and cannot be rescued by P005.

This adoption authorizes no negative P005 validator, structural or family certificate, complete impulse validation, P006 change, or general book precedence. The protected-state transition remains subject to project-manager review.

## 5. Source trace

Each analysis should include a `source_trace` field containing the source principles actually used.

The canonical principle IDs are in `SOURCE_EVIDENCE_MAP.json`.

## 6. Modern indicators

RSI, MACD, EWO and similar tools are outside the current source-locked brain unless a supplied source explicitly establishes how to use them.

They may later be added as a separate, clearly labeled extension layer. They may never override source rules.
