"""Factory-issued ancestry regressions for the Normal Impulse Runtime sidecar."""

import unittest

from elliott_methodology_kernel import AnalyzedWaveSubject, OrderedChildBinding
from elliott_runtime.analysis.normal_impulse_partial_evaluation import validate_normal_impulse_partial_evaluation_result
import elliott_runtime.analysis.normal_impulse_partial_evaluation as implementation
from test_normal_impulse_partial_evaluation import evaluate, parent_bridge, child_result


class NormalImpulseAncestryIdentityTests(unittest.TestCase):
    def fixtures(self):
        for path in ("parent", "recursive_child"):
            source = parent_bridge() if path == "parent" else child_result()
            yield path, evaluate(source)

    def reject_mutation(self, mutate, *, request_only=False):
        for path, result in self.fixtures():
            evaluation = result.evaluations[0]
            hypothesis = evaluation.hypothesis
            mutate(evaluation)
            validators = [("evaluation", evaluation._validated),
                          ("result", lambda: validate_normal_impulse_partial_evaluation_result(result))]
            if not request_only:
                validators = [(f"role_{i}", r._validated) for i, r in enumerate(hypothesis.role_bindings)] + [
                    ("hypothesis", hypothesis._validated)
                ] + validators
            for entry, validator in validators:
                with self.subTest(path=path, entry=entry):
                    with self.assertRaises(ValueError):
                        validator()
                    # Revalidation must not bless the modified object by refreshing evidence.
                    with self.assertRaises(ValueError):
                        validator()

    def test_equivalent_binding_substitution_is_rejected(self):
        def mutate(e):
            view = e.hypothesis.five_slot_view
            b = view.binding
            object.__setattr__(view, "binding", OrderedChildBinding(b.binding_id, b.parent_subject, b.ordered_children))
        self.reject_mutation(mutate)

    def test_foreign_parent_binding_substitution_is_rejected(self):
        def mutate(e):
            view = e.hypothesis.five_slot_view
            b = view.binding
            object.__setattr__(view, "binding", OrderedChildBinding(b.binding_id, AnalyzedWaveSubject("foreign", "foreign"), b.ordered_children))
        self.reject_mutation(mutate)

    def test_original_binding_parent_mutation_is_rejected(self):
        self.reject_mutation(lambda e: object.__setattr__(
            e.hypothesis.five_slot_view.binding, "parent_subject", AnalyzedWaveSubject("foreign", "foreign")
        ))

    def test_equivalent_parent_identity_substitution_is_rejected(self):
        def mutate(e):
            b = e.hypothesis.five_slot_view.binding
            p = b.parent_subject
            object.__setattr__(b, "parent_subject", AnalyzedWaveSubject(p.subject_id, p.observation_provenance_ref))
        self.reject_mutation(mutate)

    def test_children_reordering_is_rejected_by_every_role(self):
        def mutate(e):
            b = e.hypothesis.five_slot_view.binding
            c = b.ordered_children
            object.__setattr__(b, "ordered_children", (c[1], c[0], *c[2:]))
        self.reject_mutation(mutate)

    def test_child_substitution_is_rejected_by_every_role(self):
        def mutate(e):
            b = e.hypothesis.five_slot_view.binding
            object.__setattr__(b, "ordered_children", (*b.ordered_children[:4], AnalyzedWaveSubject("foreign-child", "foreign")))
        self.reject_mutation(mutate)

    def test_equivalent_children_tuple_substitution_is_rejected(self):
        def mutate(e):
            b = e.hypothesis.five_slot_view.binding
            object.__setattr__(b, "ordered_children", tuple(list(b.ordered_children)))
        self.reject_mutation(mutate)

    def test_subject_provenance_mutation_is_rejected(self):
        self.reject_mutation(lambda e: object.__setattr__(
            e.hypothesis.five_slot_view.binding.ordered_children[-1],
            "observation_provenance_ref", "foreign-provenance",
        ))

    def test_failed_validation_does_not_refresh_issuance_evidence(self):
        for path, result in self.fixtures():
            e = result.evaluations[0]
            view = e.hypothesis.five_slot_view
            evidence = implementation._ISSUED_VIEWS[view]
            b = view.binding
            object.__setattr__(view, "binding", OrderedChildBinding(b.binding_id, b.parent_subject, b.ordered_children))
            for _ in range(2):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        validate_normal_impulse_partial_evaluation_result(result)
                    self.assertIs(evidence, implementation._ISSUED_VIEWS[view])
                    self.assertIs(b, evidence[0])

    def test_p004_request_binding_substitution_is_rejected(self):
        def mutate(e):
            b = e.hypothesis.five_slot_view.binding
            object.__setattr__(e.bounded_request, "child_binding", OrderedChildBinding(b.binding_id, b.parent_subject, b.ordered_children))
        self.reject_mutation(mutate, request_only=True)

    def test_p004_request_subject_substitution_is_rejected(self):
        self.reject_mutation(lambda e: object.__setattr__(
            e.bounded_request, "subject", AnalyzedWaveSubject("foreign", "foreign")
        ), request_only=True)

    def test_untouched_factory_objects_share_exact_ancestry(self):
        for path, result in self.fixtures():
            for e in result.evaluations:
                h = e.hypothesis
                b = h.five_slot_view.binding
                self.assertIs(b.parent_subject, h.generated_candidate.subject)
                self.assertIs(e.bounded_request.child_binding, b)
                self.assertIs(e.bounded_request.subject, b.parent_subject)
                for i, role in enumerate(h.role_bindings):
                    self.assertIs(role.five_slot_view, h.five_slot_view)
                    self.assertIs(role.five_slot_view.binding, b)
                    self.assertIs(role.child_subject, b.ordered_children[i])
                    self.assertIs(role.start_boundary, h.generated_candidate.ordered_selected_pivots[i])
                    self.assertIs(role.end_boundary, h.generated_candidate.ordered_selected_pivots[i + 1])
                    self.assertIs(role, role._validated())
                if path == "parent":
                    original = next(x for x in h.source.candidate_evaluations if x.generated_candidate is h.generated_candidate)
                    self.assertIs(original.child_binding, b)
                else:
                    evidence = h.generated_child_evidence
                    self.assertTrue(any(evidence is x for x in h.source.generated_child_evidence))
                    self.assertIs(evidence.competing_candidate_set, h.competing_candidate_set)
                self.assertIs(h, h._validated())
                self.assertIs(e, e._validated())
            self.assertIs(result, validate_normal_impulse_partial_evaluation_result(result))


if __name__ == "__main__":
    unittest.main()
