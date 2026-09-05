# P005 Kernel observation-binding repair V1

Completed narrow Runtime/Kernel input-evidence repair; no measurement change.

- Actual repair base: `14f61b8a3964d71100af6334be6e1fad3dbe21f1`.
- Last approved Git HEAD: `7b8f4efd38694eef76eea05459973081026269ba`.
- The adopted protected policy is unchanged. This record does not claim
  project-manager approval of the previous implementation or this repair.

## Root cause and repair

The old public Kernel accepted six arbitrary references, independent prices and
caller-declared eligibility. Identity pinning alone did not prove observation
membership, price basis, or geometry eligibility; Runtime checks could be bypassed
by direct Kernel callers.

The new public Kernel-owned `bind_p005_observations` factory verifies six exact
snapshot Bars and their chronology against the exact five-slot view. It reads
explicit HIGH/LOW prices from those Bars and independently checks existing bounded
local-extrema window evidence. Eligibility derives from verified window coverage,
not a supplied flag. The compatibility price/eligibility fields must agree with
the evidence before the unchanged percentage comparison can execute.

Original binding, subjects, observations, price fields and geometry evidence are
pinned at issuance. Substitution, mutation and repeated failed validation cannot
refresh them. Both parent and recursive-child Runtime paths use the same factory.
Original pivots remain pinned as opaque provenance, never as proof of prices or
eligibility. Geometry confirmation remains distinct from Elliott completion.

## Verification

- Three public-API regressions failed on the repair base and pass after repair,
  with the real adopted policy gate active.
- Focused suite: 128 passed. Full suite: 986 passed. Zero failures/errors.
- 28 repair tests cover forged references/flags, wrong fields/values, foreign or
  same-value snapshots, roles/order, mutation/reissuance, factory evidence checks,
  and parity with existing geometry discovery.
- Existing numerical assertions, P004 non-rescue and ancestry checks pass.
- P005 arithmetic, result/status definitions, P004 state mapping and repaired
  ancestry validator are AST-identical to the repair base.
- 556 of 560 previously tracked files remain byte-identical; the other four are
  the authorized implementation/public exports/fixture edits. Prior baselines
  and shared-contract implementations remain unchanged.
- Methodology/structural producers/family producers/issuances: **11 / 7 / 0 / 0**.

## Protected integrity and scope

Before and after work: Brain VERSION 0.1.0, 30 entries; Sources 21 entries;
zero mismatches. No protected file was written or restored.

- SOURCE_POLICY: `605a5dc2f4819816ead3c81aa945579eb4f439e139bf50715b93a30d15adc018`
- PACKAGE_MANIFEST: `6a7831795b10e98292f9d1fcf8f3e11586031cf7ff2bb0b256efc0735d303338`
- SOURCE_MANIFEST: `ad774642080c9112796510c01697fd70f2499c828aede547de0b3d39429ad089`
- Book: `c78e1a29b717445e01de421370a627c440b127cf42c34646526a495b8c42ab9e`

This additive logical baseline supersedes only the affected input-binding
guarantees/hashes in P005-APPROVED-PERCENTAGE-SUFFICIENCY-IMPLEMENTATION-V1
(manifest `958d6e66e58deb1765bed371a7256fe1f4b68337b84b268aeb9e019326d7bc58`).
It is not physical sealing or a new authoritative protected source baseline.

P005 remains sufficiency-only; missing/developing evidence remains unresolved.
No P005 invalidity producer, full impulse/family validity, P004 rescue, P006 work,
ranking, indicators, forecast or trading was introduced. P006, Flat/Triangle
freezes and SOURCE_DERIVED_BASE_CASE_NOT_FOUND remain unchanged.

See repair_contract.json for the precise evidence chain and limits; tests.json
contains the before/after reproduction and test results. The manifest records
old/new implementation hashes and all review artifact hashes.
