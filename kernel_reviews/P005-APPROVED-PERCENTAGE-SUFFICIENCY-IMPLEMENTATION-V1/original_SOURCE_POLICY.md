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

## 5. Source trace

Each analysis should include a `source_trace` field containing the source principles actually used.

The canonical principle IDs are in `SOURCE_EVIDENCE_MAP.json`.

## 6. Modern indicators

RSI, MACD, EWO and similar tools are outside the current source-locked brain unless a supplied source explicitly establishes how to use them.

They may later be added as a separate, clearly labeled extension layer. They may never override source rules.
