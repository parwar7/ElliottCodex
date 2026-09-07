# Exact scoped child-search transport — proposed, not implemented

The safe implementation stops at filtered parent selection. Existing finer
child exploration remains available without redefining its input contract.

## Exact boundary

src/elliott_runtime/analysis/recursive_child_candidate_generation.py,
GeneratedChildCandidateEvidence.__post_init__, requires:

generation.request.scoped_pivots is selection.finer_geometric_pivots.pivots

The no-finer-selection path similarly pins the full ordered_interval_pivots
tuple. A new selected subset cannot simply replace that tuple while claiming
the existing selection/evidence identity. The existing recursive generation
factory also creates its own scoped request and complete competing set.

Therefore this stage delegates the unchanged child path and reports its
geometric-domain membership separately. No filtered-child certificate or
alternative ancestry system is introduced. Time containment alone is not a link.

## Minimal future engineering proposal — NOT APPLIED

Review an additive explicit selected-pivot scope on the child generation request,
keyed by the exact existing internal requirement and exact finer selection.
Every selected pivot must be identical to a member of that selection's original
discovery result; preserve strict chronology, uniqueness, config identity,
snapshot identity and exact parent endpoints. Record all omitted pivots and
window budgets. Existing generation/evidence factories must bind that original
scope at issuance and fail closed on later substitution, including equivalent
tuples with different origins.

Affected contracts would be the child generation request, GeneratedChildCandidateEvidence
validation and its existing factory, with corresponding tests. No protected
source change, family proof, P004/P005 change or new methodology is proposed.
This is a concrete dependency proposal, not authorization to edit those contracts.

Proposed next review: EXACT-SCOPED-CHILD-SWING-SEARCH-TRANSPORT-V1.
Developing-position inference remains a separate unresolved capability; this
proposal would not solve it or establish coherent full-history counts.
