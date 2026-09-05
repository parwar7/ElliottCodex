# BOUNDED-SNAPSHOT-ELIGIBILITY-REPLAY-V1

Completed bounded engineering diagnostic, not an Elliott count or a historical trading validation. Project-manager approval is not claimed.

**These are values captured on 2026-09-05, filtered by recorded timestamps. This is NOT a lookahead-free historical backtest. Final OHLC values are not asserted to have been known at bar opening. No exchange calendar, bar-close rule or Elliott completion proof is inferred.**

## What the replay establishes

Nine scopes completed from the preserved Yahoo NVDA capture, without fresh market-data retrieval. Three cutoffs were recorded in `configuration.json` before evaluation: July 31 and August 31 at 23:59:59 UTC, then the original capture request timestamp, September 5 at 09:09:19 UTC. Selection was the last two UTC calendar month-ends before capture plus capture, independent of results. Membership is exactly `bar.timestamp_utc <= cutoff`.

Every cutoff rebuilt factual observations, geometry, candidates, selections, bindings and P004/P005 results. No earlier eligibility or result authority was reused. The final cutoff reproduces the previous baseline's scope reports exactly. Independent audit checked all 240 reported endpoints against retained bars and the existing public geometry implementation.

There were **zero eligibility changes among 10 comparable contextual rows** across adjacent cutoffs. Most differences are endpoint-sequence additions/disappearances under the existing latest-parent/earliest-child selection policy. They are not confirmations, continuations of live identity, or retroactive changes to earlier outcomes. Stable Monthly parent sequences in July/August established P005 sufficiency but failed P004; the September Monthly parent has different endpoints and unresolved developing geometry.

## Normal Impulse partial outcomes

P004 columns are satisfied/violated/unresolved. P005 columns are sufficiency-established/unresolved. These are evaluation occurrences, not independent hypotheses or family proofs.

| Cutoff UTC | Parent scope | Path | Hypotheses | P004 S/V/U | P005 E/U | P004-invalid + P005-E |
|---|---|---|---:|---|---|---:|
| July 31 | Monthly | Parent | 1 | 0/1/0 | 1/0 | 1 |
| July 31 | Monthly | Child | 3 | 0/3/0 | 2/1 | 2 |
| July 31 | Weekly | Parent | 1 | 1/0/0 | 0/1 | 0 |
| July 31 | Weekly | Child | 0 | 0/0/0 | 0/0 | 0 |
| July 31 | Daily | Parent | 1 | 1/0/0 | 0/1 | 0 |
| July 31 | Daily | Child | 4 | 2/2/0 | 2/2 | 0 |
| August 31 | Monthly | Parent | 1 | 0/1/0 | 1/0 | 1 |
| August 31 | Monthly | Child | 3 | 0/3/0 | 2/1 | 2 |
| August 31 | Weekly | Parent | 1 | 1/0/0 | 0/1 | 0 |
| August 31 | Weekly | Child | 0 | 0/0/0 | 0/0 | 0 |
| August 31 | Daily | Parent | 1 | 0/1/0 | 0/1 | 0 |
| August 31 | Daily | Child | 7 | 7/0/0 | 0/7 | 0 |
| September 5 | Monthly | Parent | 1 | 0/1/0 | 0/1 | 0 |
| September 5 | Monthly | Child | 5 | 2/3/0 | 3/2 | 3 |
| September 5 | Weekly | Parent | 1 | 1/0/0 | 0/1 | 0 |
| September 5 | Weekly | Child | 0 | 0/0/0 | 0/0 | 0 |
| September 5 | Daily | Parent | 1 | 0/1/0 | 0/1 | 0 |
| September 5 | Daily | Child | 9 | 7/2/0 | 0/9 | 0 |

Pooled: 40 evaluations; P004 22 satisfied / 18 violated / 0 unresolved; P005 11 sufficient / 29 unresolved. Unresolved reasons: 20 `DEVELOPING_REQUIRED_ENDPOINT`, 9 `ZERO_OR_OPPOSING_ROLE_MOVEMENT`. Nine sufficient results remain P004-invalid. P005 never rescues P004. The two sufficient, P004-satisfied July Daily child evaluations are still only partial supplied-scope coverage, not complete impulses or validated families.

## Search scope and coverage

Each scope has four neutral parent candidates, eight existing four-family bridge hypotheses, one additional Normal Impulse partial hypothesis, and 28 internal requirements. None of these requirements is satisfied. Monthly/Weekly/Daily are observation resolutions, not degrees. Exactly one child layer uses Monthly->Weekly, Weekly->Daily and Daily->1H.

| Cutoff | Scope | Parent/finer bars | Neutral child candidates | Four-family child hypotheses | Requirements with partial Normal Impulse execution |
|---|---|---|---:|---:|---:|
| July 31 | Monthly | 331/1437 | 46 | 40 | 3 |
| July 31 | Weekly | 1437/6923 | 8 | 8 | 0 |
| July 31 | Daily | 6923/3317 | 88 | 77 | 4 |
| August 31 | Monthly | 332/1442 | 46 | 40 | 3 |
| August 31 | Weekly | 1442/6944 | 28 | 28 | 0 |
| August 31 | Daily | 6944/3464 | 96 | 82 | 7 |
| September 5 | Monthly | 334/1443 | 52 | 36 | 5 |
| September 5 | Weekly | 1443/6948 | 28 | 28 | 0 |
| September 5 | Daily | 6948/3493 | 112 | 89 | 9 |

No hard-cap exception occurred. This is not exhaustive: parent selection considers the latest six pivots, child selection the earliest six; span six, zero skips, ten candidates per window. The full unchanged caps are in `configuration.json`; per-scope excluded pivots, combinations, insufficient windows and diagnostics are in `operational_summary.json` and `replay_results.json`. Zero Weekly child Normal Impulse hypotheses is bounded absence, not family impossibility.

All 28 windows per scope have full timestamp-span coverage except four Weekly requirement contexts at the final cutoff. Those four share a newly selected window ending September 4 at 20:00 UTC; available Daily observations end at 13:30 UTC. There is no deterioration of a comparable earlier window: the exact window contexts were newly added. Full timestamp-span coverage is not a session-completeness assertion. Nominal gap diagnostics are retained without treating weekends, sessions or gaps as known missing trading bars. Original hourly capture dropped five null-OHLC rows; the preserved input metadata and warnings remain authoritative for those omissions.

## Comparisons and provenance

`replay_results.json` retains every trace and derived-subset membership/hash. `audit_results.json` includes stable-sequence examples, additions/disappearances and partial-window cases, with exact timestamps, fields, represented prices, roles, eligibility, snapshot hashes and original source provenance.

Keys use endpoint timestamp, field, exact represented ratio, role/edge, resolution/direction and, for children, family/slot/required shape/window context. They are limited factual reporting keys, **not full parent-ancestry continuity or live identity**. Ambiguous duplicate contexts are excluded from matching. Repeated endpoint sequences across requirements are counted separately as evaluation occurrences and explicitly identified as duplicates; none is an independent confirmation. Disappeared and added sequences are not forcibly paired.

Original normalized capture transports and Yahoo response hashes remain unchanged. Each subset preserves original capture provenance and separately records its transport SHA-256, prefix membership, source record indices, cutoff and quality-report derivation. A subset hash is never called a Yahoo response hash. Raw Yahoo bodies were not exposed/retained by the previous capture. No new source authority is serialized. Existing runner identifiers/provenance labels remain in delegated traces; the new stage, cutoff and subset records distinguish this replay invocation. Identical textual IDs across snapshots do not imply identical live objects.

## Replay

From `C:\ElliottCodex\Runtime_WORKSPACE`, PowerShell:

```powershell
$env:PYTHONPATH='src;tools'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B tools/bounded_snapshot_replay.py --inputs kernel_reviews/NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1/inputs --plan kernel_reviews/BOUNDED-SNAPSHOT-ELIGIBILITY-REPLAY-V1/configuration.json --output kernel_reviews/BOUNDED-SNAPSHOT-ELIGIBILITY-REPLAY-V1-local-replay.json
python -B kernel_reviews/BOUNDED-SNAPSHOT-ELIGIBILITY-REPLAY-V1/audit_replay.py
```

The output path must be new and beneath Runtime. The audit command checks this baseline's saved result; a repeat output is not automatically adopted as a baseline. No captures or previous outputs are overwritten. Tests use synthetic fixtures, never live retrieval.

## Validation and preservation

Final focused suite: 87 passed. Full suite: 1,017 passed. Twenty new deterministic tests cover membership, provenance, fresh identity, cross-snapshot rejection on both paths, source/result preservation, determinism, replacement versus eligibility, duplicate contexts, coverage reporting and outcome/non-rescue reconciliation. Initial development-only test/audit mistakes and their corrections are recorded in `tests.json`; they were not Kernel defects.

Brain VERSION 0.1.0, all 30 Brain and 21 Source entries passed before writes and after the full suite. Policy and book hashes match the approved state. No protected writes. All 591 previously tracked files remain unchanged; 590 have additionally been checked against the preceding baseline's recorded raw-byte hashes, and its manifest hash is preserved. No Kernel, existing Runtime implementation, shared contract, existing test or historical baseline was edited.

Inventories remain **11 executable methodology / 7 structural-invalidity producers / 0 validated-family producers / 0 family issuances**. P006 conflict, Flat/Triangle freezes, `SOURCE_DERIVED_BASE_CASE_NOT_FOUND` and legacy `analyze = NOT_IMPLEMENTED` remain unchanged. No ranking, indicators, forecast, trading, completion or family-validity authority was added.

## Exactly one recommended next stage

**CAPTURE-TIME-OBSERVATION-AVAILABILITY-CONTRACT-V1**: an engineering contract design for bounded successive capture/version provenance, separating bar timestamp from observed availability. This single later capture cannot answer what values were actually available at historical cutoffs; repeating the same cutoff experiment cannot repair that gap. Design must not infer bar-close calendars, promote geometry to completion, relax P005 eligibility or force persistent endpoints. Source-authority blockers remain separate and frozen. This recommendation requires separate approval and is not implemented here.

This is a logical additive review baseline, not physically sealed storage. Artifact hashes detect change; they do not confer approval or methodology authority.
