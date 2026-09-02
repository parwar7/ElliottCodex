import ast
import copy
from dataclasses import asdict, fields, replace
import inspect
import json
import pickle
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    OrderedChildBinding,
    P003OneLargerDegreeRelation,
    P003OneLargerDegreeThemeInput,
    P007CandidateScope,
    P007CardinalityStatus,
    P007ExecutionRole,
    P007SingleZigzagCardinalityInput,
    P007SingleZigzagCardinalityResult,
    StructuralInvalidityCertificationError,
    ValidatedInternalFamilyCertificationError,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p007_single_zigzag_cardinality,
    map_p003_one_larger_degree_theme,
)
from elliott_methodology_kernel.models import SourceClassification, StructuralValidity


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"source:{name}")


def binding_with_children(count: int) -> OrderedChildBinding:
    return OrderedChildBinding(
        binding_id=f"binding-{count}",
        parent_subject=subject("parent"),
        ordered_children=tuple(subject(f"child-{index}") for index in range(count)),
    )


def result_for(count: int, scope=P007CandidateScope.SINGLE_ZIGZAG):
    binding = binding_with_children(count)
    result = check_p007_single_zigzag_cardinality(
        P007SingleZigzagCardinalityInput(scope, binding)
    )
    return binding, result


class P007SingleZigzagCardinalityTests(unittest.TestCase):
    def test_exactly_three_satisfies_and_retains_binding_and_order_identity(self) -> None:
        binding, result = result_for(3)
        self.assertIs(P007CardinalityStatus.CARDINALITY_SATISFIED, result.status)
        self.assertIs(binding, result.binding)
        self.assertIs(binding.parent_subject, result.binding.parent_subject)
        for expected, observed in zip(
            binding.ordered_children, result.binding.ordered_children, strict=True
        ):
            self.assertIs(expected, observed)
        self.assertIs(result.fatal_to_candidate, False)
        self.assertIn("no child family, label, or broader pattern validity", result.reason)

    def test_exact_raw_scope_token_matches_enum_scope(self) -> None:
        binding = binding_with_children(3)
        enum_result = check_p007_single_zigzag_cardinality(
            P007SingleZigzagCardinalityInput(
                P007CandidateScope.SINGLE_ZIGZAG, binding
            )
        )
        raw_result = check_p007_single_zigzag_cardinality(
            P007SingleZigzagCardinalityInput("SINGLE_ZIGZAG", binding)
        )
        self.assertIs(enum_result.status, raw_result.status)
        self.assertIs(binding, raw_result.binding)

    def test_every_resolved_wrong_cardinality_violates_and_is_fatal(self) -> None:
        for count in (0, 1, 2, 4, 5, 6, 20):
            with self.subTest(count=count):
                binding, result = result_for(count)
                self.assertIs(P007CardinalityStatus.CARDINALITY_VIOLATED, result.status)
                self.assertIs(result.fatal_to_candidate, True)
                self.assertIs(binding, result.binding)

    def test_missing_scope_is_unresolved_missing_input(self) -> None:
        result = check_p007_single_zigzag_cardinality(
            P007SingleZigzagCardinalityInput(None, binding_with_children(3))
        )
        self.assertIs(P007CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
        self.assertIs(result.fatal_to_candidate, False)

    def test_unsupported_scope_forms_are_unresolved_and_never_violations(self) -> None:
        p003_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.AGAINST)
        )
        unsupported = (
            "single_zigzag",
            " SINGLE_ZIGZAG",
            "SINGLE_ZIGZAG ",
            "ZIGZAG",
            "FLAT",
            P003OneLargerDegreeRelation.AGAINST,
            p003_result,
            True,
        )
        for scope in unsupported:
            with self.subTest(scope=scope):
                result = check_p007_single_zigzag_cardinality(
                    P007SingleZigzagCardinalityInput(scope, binding_with_children(2))
                )
                self.assertIs(
                    P007CardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
                    result.status,
                )
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_missing_wrong_mapping_and_duck_binding_fail_closed(self) -> None:
        class BindingDuck:
            ordered_children = tuple(subject(str(index)) for index in range(3))

        for supplied in (None, object(), {}, {"ordered_children": ()}, BindingDuck()):
            with self.subTest(supplied_type=type(supplied).__name__):
                result = check_p007_single_zigzag_cardinality(
                    P007SingleZigzagCardinalityInput(
                        P007CandidateScope.SINGLE_ZIGZAG, supplied
                    )
                )
                self.assertIs(
                    P007CardinalityStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_wrong_input_object_and_input_subclass_fail_closed(self) -> None:
        class InputSubclass(P007SingleZigzagCardinalityInput):
            __slots__ = ()

        subclass = InputSubclass(
            P007CandidateScope.SINGLE_ZIGZAG, binding_with_children(3)
        )
        for candidate in (None, {}, object(), subclass):
            result = check_p007_single_zigzag_cardinality(candidate)
            self.assertIs(P007CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_binding_copy_and_reconstruction_follow_exact_input_contract(self) -> None:
        original = binding_with_children(3)
        self.assertIs(original, copy.copy(original))
        self.assertIs(original, copy.deepcopy(original))
        copied_result = check_p007_single_zigzag_cardinality(
            P007SingleZigzagCardinalityInput(
                P007CandidateScope.SINGLE_ZIGZAG, copy.copy(original)
            )
        )
        self.assertIs(original, copied_result.binding)

        reconstructed = OrderedChildBinding(
            "reconstructed",
            original.parent_subject,
            original.ordered_children,
        )
        reconstructed_result = check_p007_single_zigzag_cardinality(
            P007SingleZigzagCardinalityInput(
                P007CandidateScope.SINGLE_ZIGZAG, reconstructed
            )
        )
        self.assertIs(P007CardinalityStatus.CARDINALITY_SATISFIED, reconstructed_result.status)
        self.assertIs(reconstructed, reconstructed_result.binding)

    def test_every_status_family_has_locked_traceability_and_outcome(self) -> None:
        results = (
            result_for(3)[1],
            result_for(2)[1],
            check_p007_single_zigzag_cardinality(
                P007SingleZigzagCardinalityInput(None, binding_with_children(3))
            ),
            check_p007_single_zigzag_cardinality(
                P007SingleZigzagCardinalityInput("FLAT", binding_with_children(3))
            ),
        )
        self.assertEqual(set(P007CardinalityStatus), {result.status for result in results})
        for result in results:
            with self.subTest(status=result.status):
                self.assertEqual("P007", result.principle_id)
                self.assertIs(SourceClassification.DEFINITION, result.source_class)
                self.assertIs(P007ExecutionRole.HARD_VALIDATION, result.execution_role)
                self.assertEqual(
                    "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                    result.behavior_id,
                )
                self.assertTrue(result.protected_sources)
                self.assertTrue(result.reason)
                self.assertEqual(result.status.value, result.outcome)
                self.assertIs(
                    result.fatal_to_candidate,
                    result.status is P007CardinalityStatus.CARDINALITY_VIOLATED,
                )

    def test_genuine_violation_certifies_with_exact_identity_and_invalidity(self) -> None:
        binding, origin = result_for(2)
        certificate = certify_structural_invalidity(origin)
        self.assertIs(origin, certificate.origin)
        self.assertIs(binding, certificate.origin.binding)
        self.assertEqual("P007", certificate.origin_principle_id)
        self.assertEqual(
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            certificate.origin_behavior_id,
        )
        self.assertIs(SourceClassification.DEFINITION, certificate.origin_source_class)
        self.assertIs(P007ExecutionRole.HARD_VALIDATION, certificate.origin_execution_role)
        self.assertIs(P007CardinalityStatus.CARDINALITY_VIOLATED, certificate.origin_status)
        self.assertIs(certificate.fatal_to_candidate, True)
        self.assertIs(StructuralValidity.INVALID, certificate.structural_validity)

    def test_satisfied_and_unresolved_results_cannot_certify(self) -> None:
        cases = (
            result_for(3)[1],
            check_p007_single_zigzag_cardinality(
                P007SingleZigzagCardinalityInput(None, binding_with_children(3))
            ),
            check_p007_single_zigzag_cardinality(
                P007SingleZigzagCardinalityInput("FLAT", binding_with_children(3))
            ),
        )
        for result in cases:
            with self.subTest(status=result.status):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    certify_structural_invalidity(result)

    def test_manual_copied_replaced_and_deserialized_lookalikes_cannot_certify(self) -> None:
        _, genuine = result_for(2)
        manual = type(genuine)(
            **{field.name: getattr(genuine, field.name) for field in fields(genuine)}
        )
        with self.assertRaises(TypeError):
            pickle.dumps(genuine)
        lookalikes = (
            manual,
            copy.copy(genuine),
            copy.deepcopy(genuine),
            replace(genuine),
        )
        for lookalike in lookalikes:
            with self.subTest(kind=type(lookalike).__name__):
                self.assertIsNot(genuine, lookalike)
                with self.assertRaises(StructuralInvalidityCertificationError):
                    certify_structural_invalidity(lookalike)

    def test_mapping_duck_and_result_subclass_cannot_certify(self) -> None:
        _, genuine = result_for(2)

        class Duck:
            pass

        class ResultSubclass(P007SingleZigzagCardinalityResult):
            __slots__ = ()

        subclass = ResultSubclass(
            **{field.name: getattr(genuine, field.name) for field in fields(genuine)}
        )
        for lookalike in (asdict(genuine), Duck(), subclass):
            with self.assertRaises(StructuralInvalidityCertificationError):
                certify_structural_invalidity(lookalike)

    def test_core_provenance_tamper_invalidates_certificate(self) -> None:
        for field_name, replacement in (
            ("status", P007CardinalityStatus.CARDINALITY_SATISFIED),
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

    def test_p007_remains_registered_after_seventh_structural_producer(self) -> None:
        self.assertIs(structural_private._REGISTRY_SEALED, True)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(7, len(structural_private._BEHAVIOR_IDS))
        self.assertIn(P007SingleZigzagCardinalityResult, structural_private._PRODUCERS)
        self.assertIn(
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            structural_private._BEHAVIOR_IDS,
        )

    def test_p007_cannot_certify_a_validated_internal_family(self) -> None:
        for result in (result_for(3)[1], result_for(2)[1]):
            with self.assertRaises(ValidatedInternalFamilyCertificationError):
                certify_validated_internal_family(result)
        self.assertIs(family_private._REGISTRY_SEALED, True)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)

    def test_result_surface_contains_no_family_or_pattern_validity_claim(self) -> None:
        expected = (
            "status",
            "principle_id",
            "source_class",
            "execution_role",
            "protected_sources",
            "behavior_id",
            "outcome",
            "reason",
            "fatal_to_candidate",
            "binding",
        )
        self.assertEqual(expected, tuple(P007SingleZigzagCardinalityResult.__dataclass_fields__))
        self.assertEqual(expected, tuple(inspect.signature(P007SingleZigzagCardinalityResult).parameters))
        forbidden = {"family", "pattern_valid", "complete", "degree", "chronology", "wave_a", "wave_b", "wave_c"}
        self.assertTrue(forbidden.isdisjoint(P007SingleZigzagCardinalityResult.__dataclass_fields__))

    def test_module_has_narrow_imports_and_no_prohibited_capabilities(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "p007_single_zigzag_cardinality.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add("." * node.level + (node.module or ""))
        self.assertEqual(
            {"__future__", "dataclasses", "enum", "._structural_invalidity_certification", ".models", ".subject_binding"},
            imported,
        )
        for forbidden in (
            "P005", "P006", "P008", "P009", "P010", "5-3-5", "OHLCV",
            "Fibonacci", "breadth", "psychology", "fundamentals",
            "TradingView", "provider", "socket", "subprocess", "requests",
            "urllib", "playwright", "selenium", "ranking", "Preferred",
            "Alternative", "pivot", "timeframe",
        ):
            self.assertNotIn(forbidden, source_text)


if __name__ == "__main__":
    unittest.main()
