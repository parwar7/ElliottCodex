"""Public-factory scoped transport attacks; synthetic fixtures are not NVDA."""
import copy
from dataclasses import replace
import pickle
import unittest

import support
from test_finer_child_observation_selection import setup_case, child_config
from test_recursive_child_family_evaluation import evaluate as evaluate_families
from elliott_runtime.analysis.finer_child_observation_selection import select_finer_child_observations
from unittest.mock import patch
from elliott_runtime.analysis.recursive_child_candidate_generation import (
    ChildPivotSelectionScope, ChildRequirementGenerationStatus,
    RecursiveChildCandidateGenerationRequest, RecursiveChildCandidateGenerationLimitExceeded,
    create_child_pivot_selection_scope, generate_child_candidate_evidence,
)
from elliott_runtime.analysis.geometric_swing_search import (
    GeometricSwingSearchConfig, select_child_geometric_swing_scope, movement_domain,
)
from elliott_runtime.analysis.normal_impulse_partial_evaluation import (
    NormalImpulsePartialEvaluationRequest, evaluate_normal_impulse_partial_scope,
    validate_normal_impulse_partial_evaluation_result,
)
from elliott_methodology_kernel import MethodologyKernel
import elliott_methodology_kernel._validated_internal_family_certification as family_private


class ScopedChildTests(unittest.TestCase):
    def setUp(self):
        self.source, self.req, self.window, self.parent, self.obs, _, request = setup_case()
        self.selection = select_finer_child_observations(request)
        self.pivots = self.selection.finer_geometric_pivots.pivots
        self.selected = self.pivots[:6]
        self.scope = self.make_scope(self.selected)

    def make_scope(self, selected):
        return create_child_pivot_selection_scope(self.req, self.selection, selected, ('test:scope',))

    def request(self, scopes=None, config=None):
        return RecursiveChildCandidateGenerationRequest('scoped-test', '2026-09-04T00:00:00Z',
            self.source, config or child_config(max_pivots_per_child_window=6, max_child_skipped_pivots=0),
            ('test:scoped',), (self.selection,), (self.scope,) if scopes is None else scopes)

    def test_exact_scope_descendants_and_window_identity(self):
        result = generate_child_candidate_evidence(self.request())
        evidence = next(e for e in result.generated_child_evidence if e.internal_requirement is self.req)
        self.assertIs(evidence.selected_pivot_scope, self.scope)
        self.assertIs(evidence.evaluation_window, self.window)
        self.assertIs(evidence.candidate_generation_result.request.scoped_pivots, self.selected)
        self.assertIs(evidence.candidate_generation_result.request.observations, self.obs)
        for candidate in evidence.competing_candidate_set.ordered_candidates:
            self.assertTrue(all(any(p is q for q in self.selected) for p in candidate.ordered_selected_pivots))
        result._validated()

    def test_default_unfiltered_compatibility(self):
        result = generate_child_candidate_evidence(self.request(scopes=()))
        evidence = next(e for e in result.generated_child_evidence if e.internal_requirement is self.req)
        self.assertIsNone(evidence.selected_pivot_scope)
        self.assertIs(evidence.candidate_generation_result.request.scoped_pivots, self.pivots)

    def test_explicit_empty_has_no_fallback(self):
        result = generate_child_candidate_evidence(self.request(scopes=(self.make_scope(()),)))
        outcome = next(o for o in result.requirement_outcomes if o.internal_requirement is self.req)
        self.assertIsNone(outcome.generated_evidence)
        self.assertIs(outcome.status, ChildRequirementGenerationStatus.NO_SEQUENCE_IN_SELECTED_SEARCH_DOMAIN)

    def test_same_requirement_multiple_scopes_rejected(self):
        with self.assertRaises(ValueError):
            self.request(scopes=(self.scope, self.make_scope(self.pivots[1:7])))

    def test_foreign_requirement_rejected_at_factory(self):
        with self.assertRaises(ValueError):
            create_child_pivot_selection_scope(self.source.internal_requirements[1], self.selection, self.selected, ())

    def test_equal_content_foreign_selection_rejected_by_request(self):
        foreign = select_finer_child_observations(self.selection.request)
        scope = create_child_pivot_selection_scope(self.req, foreign, foreign.finer_geometric_pivots.pivots[:6], ())
        with self.assertRaises(ValueError):
            self.request(scopes=(scope,))

    def test_cross_parent_scope_rejected(self):
        other = setup_case()
        foreign = select_finer_child_observations(other[-1])
        scope = create_child_pivot_selection_scope(other[1], foreign, foreign.finer_geometric_pivots.pivots[:6], ())
        with self.assertRaises(ValueError):
            self.request(scopes=(scope,))

    def test_duplicates_reversal_and_foreign_pivots(self):
        for values in ((self.pivots[0], self.pivots[0]), tuple(reversed(self.selected)),
                       (replace(self.pivots[0]),) + self.selected[1:], list(self.selected)):
            with self.subTest(values_type=type(values)), self.assertRaises(ValueError):
                self.make_scope(values)

    def test_out_of_window_original_member_rejected(self):
        # Attack a genuine result, not a fake issued selection. Existing public
        # geometry replay may reject before the explicit window guard.
        pivot = self.pivots[0]
        object.__setattr__(pivot, 'timestamp_utc', self.parent.bars[0].timestamp_utc)
        with self.assertRaises(ValueError):
            self.make_scope((pivot,))

    def test_mapping_duck_subclass_and_unissued_rejected(self):
        for value in ({}, object()):
            with self.assertRaises(ValueError):
                self.request(scopes=(value,))
        with self.assertRaises(TypeError):
            type('ForeignScope', (ChildPivotSelectionScope,), {})
        clone = object.__new__(ChildPivotSelectionScope)
        for name in ('internal_requirement', 'finer_observation_selection', 'selected_pivots', 'provenance_refs'):
            object.__setattr__(clone, name, getattr(self.scope, name))
        with self.assertRaises(ValueError):
            clone._validated()

    def test_copy_pickle_cannot_restore_scope(self):
        for operation in (copy.copy, copy.deepcopy, pickle.dumps):
            with self.assertRaises(TypeError):
                operation(self.scope)

    def test_scope_tuple_substitution_repeated_validation(self):
        evidence = self.scope.selected_pivots
        object.__setattr__(self.scope, 'selected_pivots', tuple(list(evidence)))
        for _ in range(3):
            with self.assertRaises(ValueError):
                self.scope._validated()

    def test_nested_mutations_never_refresh_evidence(self):
        geometry = self.selection.finer_geometric_pivots
        binding = self.req.family_hypothesis.child_binding
        mutations = (
            (geometry, 'config', replace(geometry.config)),
            (geometry, 'pivots', tuple(list(geometry.pivots))),
            (geometry, 'input_observations', replace(self.obs)),
            (self.obs, 'bars', tuple(list(self.obs.bars))),
            (self.obs.bars[0], 'close', self.obs.bars[0].close + 0.01),
            (self.pivots[0], 'observed_price', self.pivots[0].observed_price + 0.01),
            (binding, 'parent_subject', replace(binding.parent_subject)),
            (binding, 'ordered_children', tuple(list(binding.ordered_children))),
            (self.req, 'parent_candidate', self.source.internal_requirements[-1].parent_candidate),
        )
        for obj, name, new in mutations:
            old = getattr(obj, name)
            if new is old:
                continue
            with self.subTest(field=name):
                object.__setattr__(obj, name, new)
                try:
                    for _ in range(2):
                        with self.assertRaises(ValueError):
                            self.scope._validated()
                finally:
                    object.__setattr__(obj, name, old)
        self.scope._validated()

    def test_request_and_result_reject_later_mutation(self):
        request = self.request()
        result = generate_child_candidate_evidence(request)
        object.__setattr__(self.scope, 'selected_pivots', ())
        for validate in (request._validated, request.__post_init__, result._validated):
            for _ in range(2):
                with self.assertRaises(ValueError):
                    validate()

    def test_evidence_scope_substitution_rejected(self):
        result = generate_child_candidate_evidence(self.request())
        evidence = next(e for e in result.generated_child_evidence if e.internal_requirement is self.req)
        object.__setattr__(evidence, 'selected_pivot_scope', self.make_scope(self.selected))
        for validate in (evidence._validated, evidence.__post_init__, result._validated):
            with self.assertRaises(ValueError):
                validate()

    def test_scope_size_and_aggregate_bounds_preflight(self):
        with self.assertRaises(RecursiveChildCandidateGenerationLimitExceeded):
            generate_child_candidate_evidence(self.request(scopes=(self.make_scope(self.pivots[:7]),)))
        with self.assertRaises(RecursiveChildCandidateGenerationLimitExceeded):
            generate_child_candidate_evidence(self.request(config=child_config(max_total_child_candidates=1)))
        with self.assertRaises(RecursiveChildCandidateGenerationLimitExceeded):
            generate_child_candidate_evidence(self.request(config=child_config(max_total_finer_geometric_pivots=1)))

    def test_aggregate_two_distinct_requirement_scopes(self):
        coarse = generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
            'windows', '2026-09-04T00:00:00Z', self.source, child_config(), ()))
        requirement = self.source.internal_requirements[1]
        window = coarse.evaluation_windows[1]
        selection = select_finer_child_observations(replace(self.selection.request,
            selection_id='second-selection', internal_requirement=requirement, proposed_child_window=window))
        self.assertGreaterEqual(len(selection.finer_geometric_pivots.pivots), 6)
        second = create_child_pivot_selection_scope(requirement, selection,
            selection.finer_geometric_pivots.pivots[:6], ())
        config = child_config(max_pivots_per_child_window=6, max_child_skipped_pivots=0,
                              max_total_child_candidates=7)
        request = RecursiveChildCandidateGenerationRequest('aggregate-scopes', '2026-09-04T00:00:00Z',
            self.source, config, (), (self.selection, selection), (self.scope, second))
        with patch('elliott_runtime.analysis.recursive_child_candidate_generation.generate_candidate_hypotheses') as materialize:
            with self.assertRaises(RecursiveChildCandidateGenerationLimitExceeded):
                generate_child_candidate_evidence(request)
            materialize.assert_not_called()

    def test_foreign_config_and_snapshot_rejected_at_scope_factory(self):
        geometry = self.selection.finer_geometric_pivots
        for field, foreign in (('config', replace(geometry.config)),
                               ('input_observations', replace(self.obs))):
            old = getattr(geometry, field)
            object.__setattr__(geometry, field, foreign)
            try:
                with self.assertRaises(ValueError):
                    self.make_scope(self.selected)
            finally:
                object.__setattr__(geometry, field, old)

    def test_selection_nested_mutation_repeated_downstream_failure(self):
        result = generate_child_candidate_evidence(self.request())
        evidence = next(e for e in result.generated_child_evidence if e.internal_requirement is self.req)
        object.__setattr__(self.selection.request, 'selected_observations', replace(self.obs))
        for validate in (evidence._validated, result._validated, self.scope._validated):
            for _ in range(2):
                with self.assertRaises(ValueError):
                    validate()

    def test_unfiltered_equivalent_request_and_scoped_search_are_not_mutated_results(self):
        request = self.request(scopes=())
        before = generate_child_candidate_evidence(request)
        after = generate_child_candidate_evidence(self.request())
        self.assertIs(before.request, request)
        self.assertEqual((), before.request.selected_pivot_scopes)
        self.assertIsNot(before, after)
        before._validated()
        after._validated()

    def test_policy_preselects_alternating_candidates_nonfatally(self):
        config = GeometricSwingSearchConfig(((self.window.start_pivot.timestamp_utc.year,
                                               self.window.end_pivot.timestamp_utc.year),), 1, 10000, 10000)
        scope, diagnostics = select_child_geometric_swing_scope(self.selection, config)
        result = generate_child_candidate_evidence(self.request(scopes=(scope,)))
        for evidence in result.generated_child_evidence:
            if evidence.internal_requirement is self.req:
                for candidate in evidence.competing_candidate_set.ordered_candidates:
                    self.assertTrue(movement_domain(tuple(p.observed_price for p in candidate.ordered_selected_pivots))['eligible'])
        self.assertFalse(diagnostics['structural_invalidity'])
        self.assertEqual(len(self.pivots), len(diagnostics['selected_pivot_ids']) + len(diagnostics['omitted_pivot_ids']))

    def test_existing_family_and_normal_consumers_and_no_rescue(self):
        children = generate_child_candidate_evidence(self.request())
        evaluate_families(children)
        result = evaluate_normal_impulse_partial_scope(NormalImpulsePartialEvaluationRequest(
            'scoped-normal', '2026-09-04T00:00:00Z', children, 100, 100, 100, ()),
            MethodologyKernel(support.PROTECTED_ROOT))
        validate_normal_impulse_partial_evaluation_result(result)
        self.assertGreater(len(result.evaluations), 0)
        for evaluation in result.evaluations:
            self.assertIs(evaluation.p005_input.observation_snapshot, evaluation.hypothesis.generated_candidate.source_observations)
            self.assertEqual(evaluation.p004_result.status.value == 'RULE_VIOLATED', evaluation.p004_result.fatal_to_candidate)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))


if __name__ == '__main__':
    unittest.main()
