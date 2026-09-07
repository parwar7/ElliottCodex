# Exact scoped child swing search transport

Classification: PROJECT_ANALYSIS_INFRASTRUCTURE. Selection policy:
PROJECT_OPERATIONAL_POLICY. This is not new Elliott methodology.

## Public contract

`create_child_pivot_selection_scope(requirement, selection, selected_pivots,
provenance_refs)` issues an exact `ChildPivotSelectionScope` in the existing
child-generation issuance registry. Its public fields retain the exact original
requirement, finer selection and caller's immutable pivot tuple. It creates no
certificate. Direct construction, subclassing, copying and pickling cannot
issue a live scope.

`RecursiveChildCandidateGenerationRequest.selected_pivot_scopes` is a new final
optional argument with default `()`. `GeneratedChildCandidateEvidence` gains a
final optional `selected_pivot_scope` with default `None`. Existing positional
constructors and unfiltered behavior are preserved.

V1 permits at most one scope per requirement and requires its exact selection to
appear in the request. Cross-parent, cross-requirement and equal-content foreign
selection objects are rejected. Distinct requirements can carry distinct scopes;
all count toward existing request/window, finer-pivot and candidate budgets.
The original complete finer discoveries count toward the aggregate finer-pivot
budget even when selected subsets are small. Selected scopes exceeding the
per-window pivot limit fail before materialization, rather than being truncated.

## Issuance and mutation

Issuance first validates the genuine selection through its existing public
validator. It verifies discovery/configuration identities, every selected pivot
as an exact original discovery member, uniqueness, chronology and inclusive
parent-window containment. An empty tuple is valid and explicit.

Immutable issuance evidence pins requirement/hypothesis/candidate links,
selection/request/window links, original parent binding and child subjects,
parent/finer observations including individual bar fields and provenance, and
original parent/finer discovery configurations and pivots. Existing dataclass
public fields are retained by identity, not recreated from IDs or equality.
Validation checks that evidence before existing nested validators. Failed or
successful validation never refreshes it. This is local transport evidence in
the existing issuance registry, not a parallel recursive analyzer, family
certification algorithm or second ancestry graph with independent authority.

The guarantee covers substitution/mutation of the issued scope's bound object
graph. It is not protection against arbitrary in-process access to private
module registries or Python runtime replacement. Runtime remains writable;
this baseline is logical preservation, not physical sealing.

## Generation and geometric selection

Generation passes the original selected tuple into a new public
CandidateGenerationRequest and creates candidates and competing sets normally.
It never filters an issued result. Unfiltered requests still pass the complete
original finer tuple. Empty/too-short explicit scopes return
NO_SEQUENCE_IN_SELECTED_SEARCH_DOMAIN with no fallback and no structural
certificate. Existing no/partial finer coverage statuses are unchanged.

`select_child_geometric_swing_scope(selection, config)` reuses the prior nonzero
alternating-movement policy and chronological six-pivot enumeration. Exactly one
first eligible sequence is selected per full-coverage requirement; other eligible
sequences are UNVISITED_BUDGET, not failed waves. Domain exclusions are nonfatal.
For fewer than six original pivots it records INSUFFICIENT_GEOMETRIC_PIVOTS;
for no eligible sequence it records NO_SEQUENCE_IN_SELECTED_SEARCH_DOMAIN.
Missing/partial finer coverage is reported separately and has no pivot scope.
All source, selected and omitted pivot IDs, source observations, original UTC
window boundaries, configuration, per-window dispositions and exact requirement
links are recorded. Six-pivot scope length is an operational domain restriction,
not a claim that shorter shapes cannot exist.

Parent window endpoints remain search boundaries only. Scoped candidates may
occupy a strict subinterval. No endpoint is fabricated, no entire-window coverage
is claimed, and no finer resolution becomes wave degree or internal proof.

## Compatibility and preserved authority

Existing recursive child-family and Normal Impulse consumers use their normal
validators. The extension changes no Kernel/shared contract, P004/P005 operand
binding, P005 arithmetic/sufficiency-only semantics, P006 or Flat/Triangle freeze.
No family producer or issuance is added. Inventories remain 11 / 7 / 0 / 0.
P004 invalidity stays local and fatal even when P005 establishes sufficiency.
SOURCE_DERIVED_BASE_CASE_NOT_FOUND and legacy analyze=NOT_IMPLEMENTED remain.

No ranking, confidence, indicators, additional recursion, Elliott terminality,
completion proof, forecast or trading behavior is introduced.

## Limited supersession

This baseline implements the proposal in the preceding quality baseline's
child_scope_boundary.md. It supersedes only the child contract's requirement that
every finer child search must use the full finer pivot tuple, and the listed
implementation hashes for recursive_child_candidate_generation.py and
geometric_swing_search.py. Historical baseline bytes and findings are retained.
All other old guarantees remain; this is not project-manager approval.
