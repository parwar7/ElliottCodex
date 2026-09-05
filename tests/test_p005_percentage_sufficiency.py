"""Approved one-sided metric, exact arithmetic, authority and ancestry tests."""
import ast
from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import pickle
import unittest
from datetime import datetime, timedelta, timezone
import json

import support
from elliott_methodology_kernel import (
    AnalyzedWaveSubject, OrderedChildBinding, NormalImpulseFiveSlotCandidateView,
    SubjectBoundObservedPriceObservation as Observation,
    SubjectBoundObservedPriceEndpointPair as Pair,
    MethodologyKernel, ImpulseDirection, certify_structural_invalidity,
    P005PercentageSufficiencyInput as Input,
    P005PercentageSufficiencyStatus as Status,
    P005PercentageSufficiencyError, EXECUTABLE_BEHAVIOR_IDS,
    P005GeometryWindow, P005PriceBasis, bind_p005_observations,
)
from elliott_methodology_kernel.contracts import SymbolIdentity, MarketType, Timeframe
from elliott_runtime.market_data.ingestion import _normalize
from elliott_methodology_kernel.p005_percentage_sufficiency import P005_BEHAVIOR_ID
from test_candidate_generation import market_observations
from test_normal_impulse_partial_evaluation import evaluate, parent_bridge, child_result, equality_bridge


def metric_input(prices=((100, 110), (100, 120), (100, 110)), direction=ImpulseDirection.UP, **changes):
    parent = AnalyzedWaveSubject("parent", "test:parent")
    children = tuple(AnalyzedWaveSubject(f"child:{i}", "test:child") for i in range(5))
    view = NormalImpulseFiveSlotCandidateView(OrderedChildBinding("test:binding", parent, children))
    # Each price is an actual bar HIGH, surrounded by lower bars. Geometry is
    # verified against those observations, not asserted using object() tokens.
    records = []
    for value in (v for pair in prices for v in pair):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Malformed fixture price")
        lower = math.nextafter(float(value), -math.inf)
        lowest = math.nextafter(lower, -math.inf)
        for high, low in ((lower, lowest), (value, lower), (lower, lowest)):
            records.append(dict(timestamp=(datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=len(records))).isoformat(),
                                open=high, high=high, low=low, close=high, volume=1))
    snapshot = _normalize(records, json.dumps(records).encode(), "test", "p005-bound-observations",
                          SymbolIdentity("TEST", MarketType.STOCK), Timeframe("1d", 86400))
    selected = tuple(snapshot.bars[i] for i in (1, 4, 7, 10, 13, 16))
    facts = changes.pop("endpoint_eligibility", (True,) * 6)
    windows = tuple(None if fact is None else P005GeometryWindow(1, 1, "FIRST",
                    (snapshot.bars[3*i], selected[i]) if fact is False else None)
                    for i, fact in enumerate(facts))
    evidence = bind_p005_observations(view, snapshot, selected, (P005PriceBasis.HIGH,) * 6, windows)
    pairs = tuple(Pair(Observation(children[i], evidence.endpoint_prices[i], "test:start"),
                       Observation(children[i], evidence.endpoint_prices[i+1], "test:end")) for i in (0, 2, 4))
    values = dict(five_slot_view=view, direction=direction, endpoint_pairs=pairs,
                  observation_snapshot=snapshot, endpoint_eligibility=evidence.endpoint_eligibility,
                  provenance_refs=("test:approved-metric",), endpoint_identity_refs=selected, observation_binding=evidence)
    if "observation_snapshot" in changes and changes["observation_snapshot"] is None:
        values.update(endpoint_pairs=(None,) * 3, endpoint_identity_refs=(None,) * 6,
                      endpoint_eligibility=(None,) * 6, observation_binding=None)
    values.update(changes)
    return Input(**values)


class P005MetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kernel = MethodologyKernel(support.PROTECTED_ROOT)

    def run_metric(self, *args, **kwargs):
        return self.kernel.evaluate_p005_percentage_sufficiency(metric_input(*args, **kwargs))

    def test_upward_sufficiency(self):
        result = self.run_metric()
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, result.status)
        self.assertEqual((10, 20, 10), result.percentage_movements)

    def test_downward_sufficiency(self):
        result = self.run_metric(((100, 90), (100, 80), (100, 90)), ImpulseDirection.DOWN)
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, result.status)

    def test_upward_arithmetic_failure_cannot_override_percentage_sufficiency(self):
        result = self.run_metric(((200, 220), (100, 115), (200, 225)))
        self.assertLess(15, min(20, 25))
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, result.status)

    def test_downward_arithmetic_disagreement(self):
        result = self.run_metric(((200, 180), (100, 85), (200, 175)), ImpulseDirection.DOWN)
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, result.status)

    def test_tied_shortest_is_unresolved(self):
        self.assertIs(Status.UNRESOLVED, self.run_metric(((100, 110), (100, 110), (100, 120))).status)

    def test_all_equal_is_unresolved(self):
        self.assertIs(Status.UNRESOLVED, self.run_metric(((100, 110),) * 3).status)

    def test_strict_shortest_is_unresolved_not_invalid(self):
        result = self.run_metric(((100, 120), (100, 110), (100, 130)))
        self.assertIs(Status.UNRESOLVED, result.status)
        self.assertFalse(result.fatal_to_candidate)

    def test_tie_above_other_comparator_can_establish_sufficiency(self):
        for prices in (((100, 120), (100, 120), (100, 110)), ((100, 110), (100, 120), (100, 120))):
            self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, self.run_metric(prices).status)

    def test_invalid_numeric_domain(self):
        for value in (None, True, False, "100", float("nan"), float("inf"), -float("inf"), 0, -1):
            with self.subTest(value=value):
                try:
                    result = self.run_metric(((value, 110), (100, 120), (100, 110)))
                except (TypeError, ValueError):
                    # Existing exact observed-price contract rejects malformed prices.
                    continue
                self.assertIs(Status.UNRESOLVED, result.status)

    def test_missing_pair(self):
        request = metric_input()
        result = self.kernel.evaluate_p005_percentage_sufficiency(replace(request, endpoint_pairs=(None, *request.endpoint_pairs[1:])))
        self.assertIs(Status.UNRESOLVED, result.status)

    def test_opposing_direction_and_zero_movement(self):
        for direction, end in ((ImpulseDirection.UP, 90), (ImpulseDirection.UP, 100), (ImpulseDirection.DOWN, 110), (ImpulseDirection.DOWN, 100)):
            self.assertIs(Status.UNRESOLVED, self.run_metric(((100, end),) * 3, direction).status)

    def test_unknown_direction(self):
        self.assertIs(Status.UNRESOLVED, self.run_metric(direction=ImpulseDirection.UNKNOWN).status)
        self.assertIs(Status.UNRESOLVED, self.run_metric(direction="UP").status)

    def test_each_developing_endpoint_is_unresolved(self):
        for index in range(6):
            facts = [True] * 6
            facts[index] = False
            result = self.run_metric(endpoint_eligibility=tuple(facts))
            self.assertEqual("DEVELOPING_REQUIRED_ENDPOINT", result.reason)
            self.assertIs(Status.UNRESOLVED, result.status)

    def test_each_missing_endpoint_eligibility_is_unresolved(self):
        for index in range(6):
            facts = [True] * 6
            facts[index] = None
            self.assertIs(Status.UNRESOLVED, self.run_metric(endpoint_eligibility=tuple(facts)).status)

    def test_missing_observation_or_provenance(self):
        self.assertIs(Status.UNRESOLVED, self.run_metric(observation_snapshot=None).status)
        self.assertIs(Status.UNRESOLVED, self.run_metric(provenance_refs=()).status)

    def test_exact_float_boundary_no_tolerance(self):
        for end, expected in ((math.nextafter(110., math.inf), Status.SUFFICIENT_CONDITION_ESTABLISHED),
                              (110., Status.UNRESOLVED), (math.nextafter(110., -math.inf), Status.UNRESOLVED)):
            result = self.run_metric(((100., 110.), (100., end), (100., 110.)))
            self.assertIs(expected, result.status)
            self.assertEqual(100 * (Fraction(end) - Fraction(100.)) / Fraction(100.), result.percentage_movements[1])

    def test_downward_float_boundary_no_tolerance(self):
        result = self.run_metric(((100., 90.), (100., math.nextafter(90., -math.inf)), (100., 90.)), ImpulseDirection.DOWN)
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, result.status)

    def test_conversion_precedes_subtraction_and_division(self):
        result = self.run_metric(((0.1, 0.3), (0.1, 0.4), (0.1, 0.3)))
        exact = 100 * (Fraction(0.3) - Fraction(0.1)) / Fraction(0.1)
        self.assertEqual(exact, result.percentage_movements[0])
        self.assertNotEqual(Fraction(100 * abs(0.3 - 0.1) / 0.1), exact)

    def test_no_completion_or_certificate_or_family_authority(self):
        for result in (self.run_metric(), self.run_metric(((100, 110),) * 3)):
            self.assertFalse(result.fatal_to_candidate)
            self.assertFalse(result.family_validity_authority)
            self.assertFalse(result.completion_authority)
            with self.assertRaises((ValueError, TypeError)):
                certify_structural_invalidity(result)

    def test_source_and_project_classifications_remain_separate(self):
        result = self.run_metric()
        self.assertEqual("P005", result.source_principle_id)
        self.assertEqual("SOURCE_RULE", result.source_class)
        self.assertEqual("USER_APPROVED_PROJECT_CONVENTIONS", result.measurement_class)
        self.assertEqual(P005_BEHAVIOR_ID, result.behavior_id)
        self.assertTrue(result.protected_sources)

    def test_mapping_duck_subclass_pickle_rejected(self):
        for bad in ({}, object()):
            with self.assertRaises(ValueError):
                self.kernel.evaluate_p005_percentage_sufficiency(bad)
        with self.assertRaises(TypeError):
            type("Fake", (Input,), {})
        with self.assertRaises(TypeError):
            pickle.dumps(metric_input())
        with self.assertRaises(TypeError):
            pickle.dumps(self.run_metric())

    def test_mutation_and_reinitialization_fail_closed(self):
        request = metric_input()
        result = self.kernel.evaluate_p005_percentage_sufficiency(request)
        object.__setattr__(request.endpoint_pairs[0].proposed_start, "price", 101)
        for _ in range(2):
            with self.assertRaises(ValueError): result.validated()
            with self.assertRaises(ValueError): request.__post_init__()

    def test_foreign_pair_rejected(self):
        request, foreign = metric_input(), metric_input()
        with self.assertRaises(ValueError):
            replace(request, endpoint_pairs=foreign.endpoint_pairs)

    def test_result_status_mutation_rejected(self):
        result = self.run_metric()
        object.__setattr__(result, "status", Status.UNRESOLVED)
        with self.assertRaises(ValueError): result.validated()

    def test_policy_adoption_is_required_at_invocation(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        with patch("elliott_methodology_kernel.api.load_brain_manifest", return_value=SimpleNamespace(observed_hashes={})):
            with self.assertRaises(P005PercentageSufficiencyError): self.run_metric()

    def test_naked_result_and_copied_result_cannot_restore_issuance(self):
        from dataclasses import fields
        result = self.run_metric()
        fake = object.__new__(type(result))
        for f in fields(result):
            object.__setattr__(fake, f.name, getattr(result, f.name))
        with self.assertRaises(ValueError): fake.validated()
        with self.assertRaises(TypeError): type(result)(result)

    def test_foreign_nested_observation_type_rejected(self):
        from types import SimpleNamespace
        request = metric_input()
        pair = request.endpoint_pairs[0]
        original = pair.proposed_start
        object.__setattr__(pair, "proposed_start", SimpleNamespace(subject=original.subject, price=original.price, observation_provenance_ref="fake"))
        with self.assertRaises(ValueError): replace(request)

    def test_new_snapshot_cannot_mutate_an_earlier_snapshot_result(self):
        first = self.run_metric()
        second = self.run_metric(((100, 110),) * 3)
        self.assertIsNot(first.input_snapshot, second.input_snapshot)
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, first.validated().status)
        self.assertIs(Status.UNRESOLVED, second.validated().status)

    def test_observation_provenance_mutation_is_detected(self):
        result = self.run_metric()
        object.__setattr__(result.input_snapshot.observation_snapshot.provenance, "source_sha256", "changed")
        with self.assertRaises(ValueError): result.validated()

    def test_inventory_eleven_seven_zero_zero(self):
        from elliott_methodology_kernel import _structural_invalidity_certification as structural
        from elliott_methodology_kernel import _validated_internal_family_certification as family
        self.assertEqual(11, len(set(EXECUTABLE_BEHAVIOR_IDS)))
        self.assertIn(P005_BEHAVIOR_ID, EXECUTABLE_BEHAVIOR_IDS)
        self.assertEqual((7, 0, 0), (len(structural._PRODUCERS), len(family._PRODUCERS), len(family._ISSUED)))


class P005RuntimeBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = (evaluate(parent_bridge()), evaluate(child_result()))

    def test_parent_child_exact_role_binding_and_snapshot_identity(self):
        for result in self.results:
            for e in result.evaluations:
                h = e.hypothesis
                self.assertIs(e.p005_input.five_slot_view, h.five_slot_view)
                self.assertIs(e.bounded_request.child_binding, h.five_slot_view.binding)
                self.assertIs(e.p005_input.observation_snapshot, h.generated_candidate.source_observations)
                for i, role in enumerate(h.role_bindings[::2]):
                    self.assertIs(e.p005_input.endpoint_pairs[i].subject, role.child_subject)
                    self.assertIs(e.p005_input.observation_binding.geometry_windows[2*i].provenance_ref, role.start_boundary)
                    self.assertIs(e.p005_input.observation_binding.geometry_windows[2*i+1].provenance_ref, role.end_boundary)
                    self.assertTrue(any(e.p005_input.endpoint_identity_refs[2*i] is bar for bar in h.generated_candidate.source_observations.bars))
                self.assertIs(e.p005_result.input_snapshot, e.p005_input)
                e._validated()

    def test_parent_child_nested_substitutions_and_mutations_fail_closed(self):
        for result in self.results:
            e = result.evaluations[0]
            h = e.hypothesis
            binding = h.five_slot_view.binding
            for obj, field, replacement in (
                (h.five_slot_view, "binding", OrderedChildBinding(binding.binding_id, binding.parent_subject, binding.ordered_children)),
                (binding, "parent_subject", AnalyzedWaveSubject("foreign", "foreign")),
                (binding, "ordered_children", tuple(reversed(binding.ordered_children))),
                (e.p005_input.endpoint_pairs[0].proposed_start, "price", 12345.),
                (h.role_bindings[0].start_boundary, "observed_price", 23456.),
                (h.role_bindings[0].start_boundary, "state", None),
                (e.p005_input, "endpoint_pairs", tuple(reversed(e.p005_input.endpoint_pairs))),
                (e.p005_input, "observation_snapshot", market_observations(8)),
            ):
                original = getattr(obj, field)
                try:
                    object.__setattr__(obj, field, replacement)
                    with self.assertRaises(ValueError): e._validated()
                    with self.assertRaises(ValueError): e.p005_result.validated()
                    with self.assertRaises(ValueError): result._validated()
                finally:
                    object.__setattr__(obj, field, original)
                e._validated()

    def test_p004_invalidity_is_still_hypothesis_local_and_fatal(self):
        seen = False
        for result in self.results:
            for e in result.evaluations:
                if e.p004_result.fatal_to_candidate:
                    seen = True
                    self.assertIs(e.structural_invalidity_certificate.origin, e.p004_result)
                    self.assertTrue(e.structural_invalidity_certificate.fatal_to_candidate)
                    self.assertIn(e.hypothesis, result.structurally_invalid_hypotheses)
                    self.assertFalse(e.p005_result.fatal_to_candidate)
                    self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, e.p005_result.status)
        self.assertTrue(seen)

    def test_p004_equality_unchanged_both_directions(self):
        from elliott_methodology_kernel import RuleCheckStatus
        for invert in (False, True):
            result = evaluate(equality_bridge(invert=invert))
            self.assertTrue(all(e.p004_result.status is RuleCheckStatus.RULE_SATISFIED for e in result.evaluations))

    def test_runtime_contains_no_percentage_comparison_or_private_kernel_import(self):
        import elliott_runtime.analysis.normal_impulse_partial_evaluation as runtime
        tree = ast.parse(Path(runtime.__file__).read_text())
        self.assertFalse(any(isinstance(n, ast.Name) and n.id == "Fraction" for n in ast.walk(tree)))
        self.assertFalse(any(isinstance(n, ast.ImportFrom) and n.module and "elliott_methodology_kernel." in n.module for n in ast.walk(tree)))
        self.assertTrue(any(isinstance(n, ast.Attribute) and n.attr == "evaluate_p005_percentage_sufficiency" for n in ast.walk(tree)))


if __name__ == "__main__":
    unittest.main()
