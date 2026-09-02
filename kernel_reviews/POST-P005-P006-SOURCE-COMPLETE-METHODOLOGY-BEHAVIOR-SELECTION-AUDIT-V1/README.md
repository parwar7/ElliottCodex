# POST-P005-P006 source-complete behavior selection

This is an additive decision/review artifact, not a methodology baseline and not executable methodology. It records the protected-source and dependency audit performed after P005 and P006 were frozen as deferred.

The audit selects exactly one next approval target: `P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY`. The selected predicate is deliberately narrower than full zigzag validation. Given an exact `OrderedChildBinding` supplied for an explicitly proposed single-zigzag candidate, it checks only whether there are exactly three direct children corresponding positionally to A, B, and C. Satisfaction proves cardinality only. It does not validate 5-3-5 subdivisions, child families, labels, parentage, chronology, degree, geometry, completion, or full zigzag validity.

The protected P007 definition and the verified Volume 4 transcript/video make this narrow proposition explicit. Existing Runtime contracts can carry the ordered operands without treating caller labels as family proof. A resolved mismatch is fatal to that proposed single-zigzag candidate under the Master Protocol's definition-first structural validation order. Missing, malformed, or unsupported inputs fail closed to unresolved outcomes.

P005 and P006 remain deferred. P006's source conflict remains unresolved. Nothing in this package redefines either principle.

The full candidate inventory, selection rationale, locked implementation design, and deferred register are in the sibling JSON files. No implementation, producer registration, certificate, test, schema change, Git mutation, or protected-source modification was made.
