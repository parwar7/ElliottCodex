import ast
import copy
from dataclasses import asdict, fields, replace
import hashlib
import inspect
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    KernelStatus,
    MethodologyKernel,
    OrderedChildBinding,
    P003OneLargerDegreeRelation,
    P003OneLargerDegreeThemeInput,
    P008CandidateScope,
    P008CardinalityStatus,
    P008ExecutionRole,
    P008FlatCardinalityInput,
    P008FlatCardinalityResult,
    StructuralInvalidityCertificationError,
    ValidatedInternalFamilyCertificationError,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p008_flat_cardinality,
    map_p003_one_larger_degree_theme,
)
from elliott_methodology_kernel.models import SourceClassification, StructuralValidity


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"source:{name}")


def binding_with_children(count: int) -> OrderedChildBinding:
    return OrderedChildBinding(
        binding_id=f"flat-binding-{count}",
        parent_subject=subject("flat-parent"),
        ordered_children=tuple(subject(f"flat-child-{index}") for index in range(count)),
    )


def result_for(count: int, scope=P008CandidateScope.FLAT):
    binding = binding_with_children(count)
    result = check_p008_flat_cardinality(P008FlatCardinalityInput(scope, binding))
    return binding, result


class P008FlatCardinalityTests(unittest.TestCase):
    def test_exactly_three_satisfies_and_retains_binding_and_order_identity(self) -> None:
        binding, result = result_for(3)
        self.assertIs(P008CardinalityStatus.CARDINALITY_SATISFIED, result.status)
        self.assertIs(binding, result.binding)
        self.assertIs(binding.parent_subject, result.binding.parent_subject)
        for expected, observed in zip(
            binding.ordered_children, result.binding.ordered_children, strict=True
        ):
            self.assertIs(expected, observed)
        self.assertIs(result.fatal_to_candidate, False)
        self.assertIn("no child family, label, subtype, or broader pattern validity", result.reason)

    def test_exact_raw_flat_scope_matches_enum_scope(self) -> None:
        binding = binding_with_children(3)
        enum_result = check_p008_flat_cardinality(
            P008FlatCardinalityInput(P008CandidateScope.FLAT, binding)
        )
        raw_result = check_p008_flat_cardinality(
            P008FlatCardinalityInput("FLAT", binding)
        )
        self.assertIs(enum_result.status, raw_result.status)
        self.assertIs(binding, raw_result.binding)

    def test_every_resolved_wrong_cardinality_violates_and_is_fatal(self) -> None:
        for count in (0, 1, 2, 4, 5, 6, 20):
            with self.subTest(count=count):
                binding, result = result_for(count)
                self.assertIs(P008CardinalityStatus.CARDINALITY_VIOLATED, result.status)
                self.assertIs(result.fatal_to_candidate, True)
                self.assertIs(binding, result.binding)

    def test_missing_scope_is_unresolved_missing_input(self) -> None:
        result = check_p008_flat_cardinality(
            P008FlatCardinalityInput(None, binding_with_children(3))
        )
        self.assertIs(P008CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
        self.assertIs(result.fatal_to_candidate, False)

    def test_unsupported_scope_forms_are_unresolved_and_never_violate(self) -> None:
        class FlatStringSubclass(str):
            pass

        p003_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.AGAINST)
        )
        unsupported = (
            "flat",
            " FLAT",
            "FLAT ",
            "REGULAR_FLAT",
            "EXPANDED_FLAT",
            "RUNNING_FLAT",
            "SINGLE_ZIGZAG",
            P003OneLargerDegreeRelation.AGAINST,
            p003_result,
            True,
            FlatStringSubclass("FLAT"),
        )
        for scope in unsupported:
            with self.subTest(scope=scope):
                result = check_p008_flat_cardinality(
                    P008FlatCardinalityInput(scope, binding_with_children(2))
                )
                self.assertIs(
                    P008CardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
                    result.status,
                )
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_missing_wrong_mapping_and_duck_binding_fail_closed(self) -> None:
        class BindingDuck:
            ordered_children = tuple(subject(str(index)) for index in range(3))

        for supplied in (None, object(), {}, {"ordered_children": ()}, BindingDuck()):
            with self.subTest(supplied_type=type(supplied).__name__):
                result = check_p008_flat_cardinality(
                    P008FlatCardinalityInput(P008CandidateScope.FLAT, supplied)
                )
                self.assertIs(P008CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_ordered_child_binding_subclass_is_rejected(self) -> None:
        class BindingSubclass(OrderedChildBinding):
            __slots__ = ()

        genuine = binding_with_children(3)
        subclass = BindingSubclass(
            genuine.binding_id,
            genuine.parent_subject,
            genuine.ordered_children,
        )
        result = check_p008_flat_cardinality(
            P008FlatCardinalityInput(P008CandidateScope.FLAT, subclass)
        )
        self.assertIs(P008CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
        self.assertIsNone(result.binding)
        self.assertIs(result.fatal_to_candidate, False)

    def test_permuted_three_child_binding_satisfies_cardinality_only(self) -> None:
        original = binding_with_children(3)
        permuted = OrderedChildBinding(
            "permuted-flat",
            original.parent_subject,
            tuple(reversed(original.ordered_children)),
        )
        result = check_p008_flat_cardinality(
            P008FlatCardinalityInput(P008CandidateScope.FLAT, permuted)
        )
        self.assertIs(P008CardinalityStatus.CARDINALITY_SATISFIED, result.status)
        self.assertIs(permuted, result.binding)
        self.assertEqual(tuple(reversed(original.ordered_children)), result.binding.ordered_children)
        self.assertIn("no child family, label, subtype, or broader pattern validity", result.reason)

    def test_wrong_input_object_and_input_subclass_fail_closed(self) -> None:
        class InputSubclass(P008FlatCardinalityInput):
            __slots__ = ()

        subclass = InputSubclass(P008CandidateScope.FLAT, binding_with_children(3))
        for candidate in (None, {}, object(), subclass):
            result = check_p008_flat_cardinality(candidate)
            self.assertIs(P008CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_binding_copy_and_reconstruction_obey_exact_input_contract(self) -> None:
        original = binding_with_children(3)
        self.assertIs(original, copy.copy(original))
        self.assertIs(original, copy.deepcopy(original))
        copied = check_p008_flat_cardinality(
            P008FlatCardinalityInput(P008CandidateScope.FLAT, copy.copy(original))
        )
        self.assertIs(original, copied.binding)

        reconstructed = OrderedChildBinding(
            "reconstructed-flat", original.parent_subject, original.ordered_children
        )
        result = check_p008_flat_cardinality(
            P008FlatCardinalityInput(P008CandidateScope.FLAT, reconstructed)
        )
        self.assertIs(P008CardinalityStatus.CARDINALITY_SATISFIED, result.status)
        self.assertIs(reconstructed, result.binding)

    def test_every_status_family_has_exact_traceability_and_fatality(self) -> None:
        results = (
            result_for(3)[1],
            result_for(2)[1],
            check_p008_flat_cardinality(
                P008FlatCardinalityInput(None, binding_with_children(3))
            ),
            check_p008_flat_cardinality(
                P008FlatCardinalityInput("TRIANGLE", binding_with_children(3))
            ),
        )
        self.assertEqual(set(P008CardinalityStatus), {result.status for result in results})
        for result in results:
            with self.subTest(status=result.status):
                self.assertEqual("P008", result.principle_id)
                self.assertIs(SourceClassification.DEFINITION, result.source_class)
                self.assertIs(P008ExecutionRole.HARD_VALIDATION, result.execution_role)
                self.assertEqual("P008_FLAT_DIRECT_CHILD_CARDINALITY", result.behavior_id)
                self.assertTrue(result.protected_sources)
                self.assertTrue(result.reason)
                self.assertEqual(result.status.value, result.outcome)
                self.assertIs(
                    result.fatal_to_candidate,
                    result.status is P008CardinalityStatus.CARDINALITY_VIOLATED,
                )

    def test_genuine_violation_certifies_with_exact_origin_and_invalidity(self) -> None:
        binding, origin = result_for(2)
        certificate = certify_structural_invalidity(origin)
        self.assertIs(origin, certificate.origin)
        self.assertIs(binding, certificate.origin.binding)
        self.assertEqual("P008", certificate.origin_principle_id)
        self.assertEqual("P008_FLAT_DIRECT_CHILD_CARDINALITY", certificate.origin_behavior_id)
        self.assertIs(SourceClassification.DEFINITION, certificate.origin_source_class)
        self.assertIs(P008ExecutionRole.HARD_VALIDATION, certificate.origin_execution_role)
        self.assertIs(P008CardinalityStatus.CARDINALITY_VIOLATED, certificate.origin_status)
        self.assertIs(certificate.fatal_to_candidate, True)
        self.assertIs(StructuralValidity.INVALID, certificate.structural_validity)

    def test_satisfied_and_unresolved_results_cannot_certify(self) -> None:
        results = (
            result_for(3)[1],
            check_p008_flat_cardinality(
                P008FlatCardinalityInput(None, binding_with_children(3))
            ),
            check_p008_flat_cardinality(
                P008FlatCardinalityInput("TRIANGLE", binding_with_children(3))
            ),
        )
        for result in results:
            with self.subTest(status=result.status):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    certify_structural_invalidity(result)

    def test_manual_copied_replaced_serialized_and_fake_results_do_not_certify(self) -> None:
        _, genuine = result_for(2)
        manual = type(genuine)(
            **{field.name: getattr(genuine, field.name) for field in fields(genuine)}
        )
        with self.assertRaises(TypeError):
            pickle.dumps(genuine)

        class Duck:
            pass

        class ResultSubclass(P008FlatCardinalityResult):
            __slots__ = ()

        subclass = ResultSubclass(
            **{field.name: getattr(genuine, field.name) for field in fields(genuine)}
        )
        for lookalike in (
            manual,
            copy.copy(genuine),
            copy.deepcopy(genuine),
            replace(genuine),
            asdict(genuine),
            Duck(),
            subclass,
        ):
            with self.subTest(kind=type(lookalike).__name__):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    certify_structural_invalidity(lookalike)

    def test_certified_core_field_tamper_fails_closed(self) -> None:
        for field_name, replacement in (
            ("status", P008CardinalityStatus.CARDINALITY_SATISFIED),
            ("principle_id", "P999"),
            ("source_class", SourceClassification.RULE),
            ("execution_role", "HARD_VALIDATION"),
            ("protected_sources", ("tampered",)),
            ("behavior_id", "TAMPERED"),
            ("outcome", "TAMPERED"),
            ("reason", "tampered"),
            ("fatal_to_candidate", False),
        ):
            _, origin = result_for(2)
            certificate = certify_structural_invalidity(origin)
            object.__setattr__(origin, field_name, replacement)
            with self.subTest(field=field_name):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    _ = certificate.structural_validity

    def test_p008_is_exactly_fifth_structural_producer_and_prior_four_unchanged(self) -> None:
        self.assertIs(structural_private._REGISTRY_SEALED, True)
        self.assertEqual(5, len(structural_private._PRODUCERS))
        self.assertEqual(5, len(structural_private._BEHAVIOR_IDS))
        self.assertIn(P008FlatCardinalityResult, structural_private._PRODUCERS)
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            },
            structural_private._BEHAVIOR_IDS,
        )
        expected = {
            "_structural_invalidity_certification.py": "b3f321a3e76f93ff37e995e9a1694a058fce68d0adbb20f6572ba2fc2082f615",
            "p004.py": "397a438f5710a5a138b112c473a512a0df930e33ed7f10279e74589501500d1c",
            "degree_peer_consistency.py": "faf0fb3761d23190f2a5719ae2c62a2cb6c2aa64a739fd8761e709e9be7b4b07",
            "parent_child_degree_adjacency.py": "a4fca4714c850c3ee2d20dbb245c6929119789b7fa10097c661b8c09db497131",
            "p007_single_zigzag_cardinality.py": "c8f288de9619c5decd6b99c82cee1d21a72ad0824921e9326472b0de35a3973f",
        }
        root = support.SRC / "elliott_methodology_kernel"
        for name, expected_hash in expected.items():
            self.assertEqual(expected_hash, hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_p008_is_not_validated_family_proof_and_registry_remains_empty(self) -> None:
        for result in (result_for(3)[1], result_for(2)[1]):
            with self.assertRaises(ValidatedInternalFamilyCertificationError):
                certify_validated_internal_family(result)
        self.assertIs(family_private._REGISTRY_SEALED, True)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)

    def test_result_surface_claims_cardinality_only(self) -> None:
        expected = (
            "status", "principle_id", "source_class", "execution_role",
            "protected_sources", "behavior_id", "outcome", "reason",
            "fatal_to_candidate", "binding",
        )
        self.assertEqual(expected, tuple(P008FlatCardinalityResult.__dataclass_fields__))
        self.assertEqual(expected, tuple(inspect.signature(P008FlatCardinalityResult).parameters))
        forbidden = {
            "family", "subtype", "pattern_valid", "complete", "degree",
            "chronology", "wave_a", "wave_b", "wave_c", "three_three_five",
        }
        self.assertTrue(forbidden.isdisjoint(P008FlatCardinalityResult.__dataclass_fields__))

    def test_module_dependencies_and_capabilities_remain_narrow(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "p008_flat_cardinality.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imported = set()
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add("." * node.level + (node.module or ""))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
        self.assertEqual(
            {"__future__", "dataclasses", "enum", "._structural_invalidity_certification", ".models", ".subject_binding"},
            imported,
        )
        self.assertTrue({"open", "exec", "eval", "__import__"}.isdisjoint(called_names))
        for forbidden in (
            "P005", "P006", "P009", "P010", "3-3-5", "regular flat",
            "expanded flat", "running flat", "zigzag logic", "triangle logic",
            "Fibonacci", "breadth", "psychology", "fundamentals", "TradingView",
            "socket", "subprocess", "requests", "urllib", "playwright", "selenium",
            "ranking", "Preferred", "Alternative", "pivot", "timeframe",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_executable_inventory_is_exactly_eight_and_analyze_is_not_implemented(self) -> None:
        observed = set()
        special_names = {"NO_RESCUE_BEHAVIOR", "P003_BEHAVIOR"}
        root = support.SRC / "elliott_methodology_kernel"
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
                    continue
                if not isinstance(node.value.value, str):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and (
                        target.id.endswith("_BEHAVIOR_ID") or target.id in special_names
                    ):
                        observed.add(node.value.value)
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P023_INTERNAL_VISIBILITY_GUARD",
                "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
                "P003_ONE_LARGER_DEGREE_SEARCH_THEME",
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )
        source_text = inspect.getsource(MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, kernel.KernelStatus.NOT_IMPLEMENTED)


if __name__ == "__main__":
    unittest.main()
