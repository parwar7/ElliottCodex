"""Public-API regressions for independently fabricated P005 endpoint evidence."""
from dataclasses import replace
from dataclasses import fields
import pickle
import unittest
import support
from elliott_methodology_kernel import (
    MethodologyKernel, AnalyzedWaveSubject, OrderedChildBinding,
    NormalImpulseFiveSlotCandidateView, ImpulseDirection,
    SubjectBoundObservedPriceObservation as Observation,
    SubjectBoundObservedPriceEndpointPair as Pair,
    P005PercentageSufficiencyInput as Input,
    P005ObservationBinding, P005PriceBasis, P005GeometryWindow,
    bind_p005_observations, P005PercentageSufficiencyStatus as Status,
)
from test_candidate_generation import market_observations
from test_p005_percentage_sufficiency import metric_input


def naked_input(*, snapshot=None, refs=None, eligibility=None):
    parent = AnalyzedWaveSubject("untrusted-parent", "untrusted-parent")
    children = tuple(AnalyzedWaveSubject(str(i), str(i)) for i in range(5))
    view = NormalImpulseFiveSlotCandidateView(OrderedChildBinding("untrusted", parent, children))
    pairs = tuple(Pair(Observation(children[i], 100., "arbitrary"),
                       Observation(children[i], end, "arbitrary"))
                  for i, end in zip((0, 2, 4), (110., 120., 110.)))
    return Input(view, ImpulseDirection.UP, pairs, snapshot or market_observations(8),
                 (True,) * 6 if eligibility is None else eligibility, ("untrusted",),
                 tuple(object() for _ in range(6)) if refs is None else refs)


class P005PublicVulnerabilityRegressions(unittest.TestCase):
    def setUp(self):
        # Real adopted protected policy; no mock or private evaluator.
        self.kernel = MethodologyKernel(support.PROTECTED_ROOT)

    def test_public_api_rejects_six_arbitrary_object_references(self):
        with self.assertRaises(ValueError):
            self.kernel.evaluate_p005_percentage_sufficiency(naked_input())

    def test_public_api_rejects_unrelated_observations_and_independent_prices(self):
        with self.assertRaises(ValueError):
            self.kernel.evaluate_p005_percentage_sufficiency(naked_input(snapshot=market_observations(12)))

    def test_public_api_rejects_fabricated_nondeveloping_eligibility(self):
        with self.assertRaises(ValueError):
            self.kernel.evaluate_p005_percentage_sufficiency(naked_input(eligibility=(True,) * 6))


class P005VerifiedObservationTests(unittest.TestCase):
    def setUp(self):
        self.kernel = MethodologyKernel(support.PROTECTED_ROOT)

    def call(self, request):
        return self.kernel.evaluate_p005_percentage_sufficiency(request)

    def rebind(self, evidence, **changes):
        values = {name: getattr(evidence, name) for name in (
            "five_slot_view", "observation_snapshot", "endpoint_bars", "price_fields", "geometry_windows")}
        values.update(changes)
        return bind_p005_observations(**values)

    def test_positive_api_uses_exact_observations_and_derived_eligibility(self):
        request = metric_input()
        evidence = request.observation_binding
        result = self.call(request)
        self.assertIs(Status.SUFFICIENT_CONDITION_ESTABLISHED, result.status)
        for index, bar in enumerate(evidence.endpoint_bars):
            self.assertTrue(any(bar is b for b in request.observation_snapshot.bars))
            self.assertEqual(evidence.endpoint_prices[index], getattr(bar, evidence.price_fields[index].value))
        self.assertEqual((True,) * 6, evidence.endpoint_eligibility)
        self.assertFalse(result.completion_authority)

    def test_same_value_different_snapshot_public_api_rejected(self):
        request = metric_input()
        clone = replace(request.observation_snapshot)
        self.assertEqual(clone, request.observation_snapshot)
        with self.assertRaises(ValueError): self.call(replace(request, observation_snapshot=clone))

    def test_unrelated_snapshot_public_api_rejected_with_genuine_evidence(self):
        request = metric_input()
        with self.assertRaises(ValueError): self.call(replace(request, observation_snapshot=market_observations(20)))

    def test_wrong_represented_price_public_api_rejected(self):
        request = metric_input()
        pair = request.endpoint_pairs[0]
        wrong = Pair(Observation(pair.subject, 101., "fake-price"), pair.proposed_end)
        with self.assertRaises(ValueError): self.call(replace(request, endpoint_pairs=(wrong, *request.endpoint_pairs[1:])))

    def test_low_value_cannot_substitute_for_bound_high(self):
        request = metric_input()
        pair = request.endpoint_pairs[0]
        wrong = Pair(Observation(pair.subject, request.endpoint_identity_refs[0].low, "wrong-basis"), pair.proposed_end)
        with self.assertRaises(ValueError): self.call(replace(request, endpoint_pairs=(wrong, *request.endpoint_pairs[1:])))

    def test_foreign_view_and_binding_public_api_rejected(self):
        request = metric_input()
        b = request.five_slot_view.binding
        foreign = NormalImpulseFiveSlotCandidateView(OrderedChildBinding(b.binding_id, b.parent_subject, b.ordered_children))
        with self.assertRaises(ValueError): self.call(replace(request, five_slot_view=foreign))

    def test_reordered_role_pairs_public_api_rejected(self):
        request = metric_input()
        with self.assertRaises(ValueError): self.call(replace(request, endpoint_pairs=tuple(reversed(request.endpoint_pairs))))

    def test_reordered_or_same_value_foreign_endpoint_references_rejected(self):
        request = metric_input()
        alternatives = (tuple(reversed(request.endpoint_identity_refs)),
                        (replace(request.endpoint_identity_refs[0]), *request.endpoint_identity_refs[1:]),
                        tuple(object() for _ in range(6)))
        for refs in alternatives:
            with self.assertRaises(ValueError): self.call(replace(request, endpoint_identity_refs=refs))

    def test_fabricated_nondeveloping_flag_cannot_override_actual_developing_window(self):
        request = metric_input(endpoint_eligibility=(False, True, True, True, True, True))
        self.assertIs(Status.UNRESOLVED, self.call(request).status)
        with self.assertRaises(ValueError): self.call(replace(request, endpoint_eligibility=(True,) * 6))

    def test_missing_geometry_cannot_be_promoted_by_boolean(self):
        request = metric_input(endpoint_eligibility=(None,) * 6)
        self.assertIs(Status.UNRESOLVED, self.call(request).status)
        with self.assertRaises(ValueError): self.call(replace(request, endpoint_eligibility=(True,) * 6))

    def test_mutation_and_repeated_public_api_validation_never_refresh_evidence(self):
        mutators = (
            lambda r: (r.observation_binding, "endpoint_eligibility", (False,) * 6),
            lambda r: (r.observation_binding, "price_fields", (P005PriceBasis.LOW,) * 6),
            lambda r: (r.endpoint_identity_refs[0], "high", 101.),
            lambda r: (r.endpoint_identity_refs[0].provenance, "source_timestamp", "foreign"),
            lambda r: (r.five_slot_view.binding, "parent_subject", AnalyzedWaveSubject("foreign", "foreign")),
            lambda r: (r.observation_binding.geometry_windows[0], "right_window_bars", 2),
            lambda r: (r, "observation_snapshot", replace(r.observation_snapshot)),
        )
        for mutate in mutators:
            request = metric_input()
            result = self.call(request)
            obj, field, value = mutate(request)
            object.__setattr__(obj, field, value)
            for _ in range(2):
                with self.assertRaises(ValueError): self.call(request)
                with self.assertRaises(ValueError): result.validated()

    def test_factory_rejects_foreign_bars_even_with_equivalent_values(self):
        evidence = metric_input().observation_binding
        with self.assertRaises(ValueError):
            self.rebind(evidence, endpoint_bars=(replace(evidence.endpoint_bars[0]), *evidence.endpoint_bars[1:]))

    def test_factory_rejects_reordered_endpoint_chronology(self):
        evidence = metric_input().observation_binding
        with self.assertRaises(ValueError): self.rebind(evidence, endpoint_bars=tuple(reversed(evidence.endpoint_bars)))

    def test_factory_rejects_wrong_field_and_unsupported_basis(self):
        evidence = metric_input().observation_binding
        for basis in ("close", "high", P005PriceBasis.LOW):
            with self.assertRaises(ValueError): self.rebind(evidence, price_fields=(basis,) * 6)

    def test_factory_checks_actual_extrema_not_just_full_window_availability(self):
        evidence = metric_input().observation_binding
        # The neighbor bar's high is NOT a selected maximum in this context.
        with self.assertRaises(ValueError):
            self.rebind(evidence, endpoint_bars=(evidence.observation_snapshot.bars[2], *evidence.endpoint_bars[1:]))

    def test_factory_rejects_foreign_scope_observations(self):
        evidence = metric_input().observation_binding
        wrong = P005GeometryWindow(1, 1, "FIRST", tuple(replace(b) for b in evidence.observation_snapshot.bars))
        with self.assertRaises(ValueError): self.rebind(evidence, geometry_windows=(wrong,) * 6)

    def test_factory_rejects_malformed_bar_provenance_before_issuance(self):
        evidence = metric_input().observation_binding
        object.__setattr__(evidence.endpoint_bars[0].provenance, "source_record_index", True)
        view = NormalImpulseFiveSlotCandidateView(evidence.five_slot_view.binding)
        with self.assertRaises(ValueError): self.rebind(evidence, five_slot_view=view)

    def test_factory_rejects_missing_source_identity_before_issuance(self):
        evidence = metric_input().observation_binding
        object.__setattr__(evidence.observation_snapshot.provenance, "source_identifier", "")
        view = NormalImpulseFiveSlotCandidateView(evidence.five_slot_view.binding)
        with self.assertRaises(ValueError): self.rebind(evidence, five_slot_view=view)

    def test_factory_rejects_unbounded_or_boolean_window_parameters(self):
        for value in (0, -1, True, 10001):
            evidence = metric_input().observation_binding
            with self.assertRaises(ValueError): self.rebind(evidence, geometry_windows=(P005GeometryWindow(1, value, "FIRST"),) * 6)

    def test_factory_cannot_refresh_a_mutated_view_or_snapshot(self):
        for field in ("binding", "snapshot"):
            request = metric_input()
            evidence = request.observation_binding
            if field == "binding":
                b = request.five_slot_view.binding
                object.__setattr__(request.five_slot_view, "binding", OrderedChildBinding(b.binding_id, b.parent_subject, b.ordered_children))
            else:
                object.__setattr__(request.observation_snapshot.provenance, "source_sha256", "changed")
            for _ in range(2):
                with self.assertRaises(ValueError): self.rebind(evidence)

    def test_same_view_cannot_be_reissued_for_another_snapshot(self):
        evidence = metric_input().observation_binding
        with self.assertRaises(ValueError): self.rebind(evidence, observation_snapshot=replace(evidence.observation_snapshot))

    def test_unissued_copied_subclassed_or_pickled_binding_cannot_restore_authority(self):
        request = metric_input()
        with self.assertRaises(TypeError): P005ObservationBinding()
        with self.assertRaises(TypeError): type("Fake", (P005ObservationBinding,), {})
        with self.assertRaises(TypeError): pickle.dumps(request.observation_binding)
        fake = object.__new__(P005ObservationBinding)
        for f in fields(fake): object.__setattr__(fake, f.name, getattr(request.observation_binding, f.name))
        with self.assertRaises(ValueError): self.call(replace(request, observation_binding=fake))

    def test_opaque_provenance_object_is_not_a_price_or_eligibility_source(self):
        # A decorative marker cannot substitute for real observation evidence.
        request = metric_input()
        evidence = request.observation_binding
        with self.assertRaises(ValueError): self.call(replace(request, endpoint_identity_refs=tuple(object() for _ in range(6))))
        self.assertEqual((True,) * 6, evidence.endpoint_eligibility)

    def test_opaque_nondeveloping_claim_does_not_override_verified_partial_window(self):
        from types import SimpleNamespace
        request = metric_input()
        evidence = request.observation_binding
        view = NormalImpulseFiveSlotCandidateView(request.five_slot_view.binding)
        windows = tuple(P005GeometryWindow(1, 1, "FIRST",
            (evidence.observation_snapshot.bars[3*i], bar), SimpleNamespace(state="CONFIRMED_BY_GEOMETRY"))
            for i, bar in enumerate(evidence.endpoint_bars))
        bound = bind_p005_observations(view, evidence.observation_snapshot, evidence.endpoint_bars, evidence.price_fields, windows)
        self.assertEqual((False,) * 6, bound.endpoint_eligibility)
        revised = replace(request, five_slot_view=view, observation_binding=bound, endpoint_eligibility=bound.endpoint_eligibility)
        self.assertIs(Status.UNRESOLVED, self.call(revised).status)

    def test_geometry_evidence_matches_existing_discovery_for_both_tie_policies_and_scopes(self):
        from elliott_runtime.market_data.geometric_pivots import (
            discover_geometric_pivots, GeometricPivotDiscoveryRequest,
            GeometricPivotDiscoveryConfig, GeometricPivotDiscoveryMethod,
            EqualExtremePolicy, GeometricPivotState, GeometricPivotKind,
        )
        data = market_observations(40)
        for policy in EqualExtremePolicy:
            for scope in (None, data.bars[3:-2]):
                config = GeometricPivotDiscoveryConfig(GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 1, 2, policy, True)
                discovered = discover_geometric_pivots(GeometricPivotDiscoveryRequest("parity", data, config, ("test:parity",), scope))
                pivots = discovered.pivots[-6:]
                self.assertEqual(6, len(pivots))
                parent = AnalyzedWaveSubject("parity", "test:parity")
                children = tuple(AnalyzedWaveSubject(str(i), "test:parity") for i in range(5))
                view = NormalImpulseFiveSlotCandidateView(OrderedChildBinding("parity", parent, children))
                selected = tuple(next(bar for bar in data.bars if bar.timestamp_utc == pivot.timestamp_utc) for pivot in pivots)
                bases = tuple(P005PriceBasis.HIGH if p.pivot_kind is GeometricPivotKind.HIGH else P005PriceBasis.LOW for p in pivots)
                windows = tuple(P005GeometryWindow(1, 2, policy.value, scope, p) for p in pivots)
                bound = bind_p005_observations(view, data, selected, bases, windows)
                self.assertEqual(tuple(p.state is GeometricPivotState.CONFIRMED_BY_GEOMETRY for p in pivots), bound.endpoint_eligibility)
                self.assertEqual(tuple(p.observed_price for p in pivots), bound.endpoint_prices)


if __name__ == "__main__":
    unittest.main()
