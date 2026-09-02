import ast
import copy
from dataclasses import asdict, fields, replace
from enum import StrEnum
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
    P009CandidateScope,
    P009CardinalityStatus,
    P009ExecutionRole,
    P009TriangleCardinalityInput,
    P009TriangleCardinalityResult,
    StructuralInvalidityCertificationError,
    ValidatedInternalFamilyCertificationError,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p009_triangle_cardinality,
    map_p003_one_larger_degree_theme,
)
from elliott_methodology_kernel.models import SourceClassification, StructuralValidity


EXPECTED_PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P009",
    "docs/elliott/PATTERN_BRAIN.md#H-triangle",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
    "docs/elliott/MASTER_PROTOCOL.md#step-5",
    "Sources_LOCKED/volume_04/volume_04@00:25:03.650-00:25:22.670",
    "Sources_LOCKED/volume_04/volume_04@00:28:39.220-00:28:48.560",
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"source:{name}")


def binding_with_children(count: int) -> OrderedChildBinding:
    return OrderedChildBinding(
        binding_id=f"triangle-binding-{count}",
        parent_subject=subject("triangle-parent"),
        ordered_children=tuple(
            subject(f"triangle-child-{index}") for index in range(count)
        ),
    )


def result_for(count: int, scope=P009CandidateScope.TRIANGLE):
    binding = binding_with_children(count)
    result = check_p009_triangle_cardinality(
        P009TriangleCardinalityInput(scope, binding)
    )
    return binding, result


class P009TriangleCardinalityTests(unittest.TestCase):
    def test_exactly_five_satisfies_and_retains_binding_and_order_identity(self) -> None:
        binding, result = result_for(5)
        self.assertIs(P009CardinalityStatus.CARDINALITY_SATISFIED, result.status)
        self.assertIs(binding, result.binding)
        self.assertIs(binding.parent_subject, result.binding.parent_subject)
        for expected, observed in zip(
            binding.ordered_children, result.binding.ordered_children, strict=True
        ):
            self.assertIs(expected, observed)
        self.assertIs(result.fatal_to_candidate, False)
        for excluded_claim in (
            "no child family",
            "label",
            "subtype",
            "position",
            "geometry",
            "broader pattern validity",
        ):
            self.assertIn(excluded_claim, result.reason)

    def test_exact_raw_triangle_scope_matches_enum_scope(self) -> None:
        binding = binding_with_children(5)
        enum_result = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding)
        )
        raw_result = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput("TRIANGLE", binding)
        )
        self.assertIs(enum_result.status, raw_result.status)
        self.assertIs(binding, raw_result.binding)

    def test_every_resolved_wrong_cardinality_violates_and_is_fatal(self) -> None:
        for count in (0, 1, 2, 3, 4, 6, 7, 20):
            with self.subTest(count=count):
                binding, result = result_for(count)
                self.assertIs(P009CardinalityStatus.CARDINALITY_VIOLATED, result.status)
                self.assertIs(result.fatal_to_candidate, True)
                self.assertIs(binding, result.binding)

    def test_missing_scope_is_unresolved_missing_input(self) -> None:
        result = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(None, binding_with_children(5))
        )
        self.assertIs(P009CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
        self.assertIs(result.fatal_to_candidate, False)
        self.assertIsNone(result.binding)

    def test_unsupported_scope_forms_are_unresolved_and_never_violate(self) -> None:
        class TriangleStringSubclass(str):
            pass

        class ForeignTriangleScope(StrEnum):
            TRIANGLE = "TRIANGLE"

        p003_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.AGAINST)
        )
        unsupported = (
            "triangle",
            " TRIANGLE",
            "TRIANGLE ",
            "CONTRACTING_TRIANGLE",
            "ASCENDING_TRIANGLE",
            "DESCENDING_TRIANGLE",
            "EXPANDING_TRIANGLE",
            "ENDING_DIAGONAL",
            "LEADING_DIAGONAL",
            "FLAT",
            "SINGLE_ZIGZAG",
            P003OneLargerDegreeRelation.AGAINST,
            p003_result,
            True,
            TriangleStringSubclass("TRIANGLE"),
            ForeignTriangleScope.TRIANGLE,
        )
        for scope in unsupported:
            with self.subTest(scope=scope):
                result = check_p009_triangle_cardinality(
                    P009TriangleCardinalityInput(scope, binding_with_children(4))
                )
                self.assertIs(
                    P009CardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
                    result.status,
                )
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_missing_wrong_mapping_and_duck_binding_fail_closed(self) -> None:
        class BindingDuck:
            ordered_children = tuple(subject(str(index)) for index in range(5))

        for supplied in (None, object(), {}, {"ordered_children": ()}, BindingDuck()):
            with self.subTest(supplied_type=type(supplied).__name__):
                result = check_p009_triangle_cardinality(
                    P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, supplied)
                )
                self.assertIs(P009CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_ordered_child_binding_subclass_is_rejected(self) -> None:
        class BindingSubclass(OrderedChildBinding):
            __slots__ = ()

        genuine = binding_with_children(5)
        subclass = BindingSubclass(
            genuine.binding_id,
            genuine.parent_subject,
            genuine.ordered_children,
        )
        result = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, subclass)
        )
        self.assertIs(P009CardinalityStatus.UNRESOLVED_MISSING_INPUT, result.status)
        self.assertIsNone(result.binding)
        self.assertIs(result.fatal_to_candidate, False)

    def test_permuted_five_child_bindings_satisfy_cardinality_only(self) -> None:
        original = binding_with_children(5)
        orders = (
            tuple(reversed(original.ordered_children)),
            original.ordered_children[1:] + original.ordered_children[:1],
            (
                original.ordered_children[2],
                original.ordered_children[0],
                original.ordered_children[4],
                original.ordered_children[1],
                original.ordered_children[3],
            ),
        )
        for index, ordered_children in enumerate(orders):
            with self.subTest(index=index):
                permuted = OrderedChildBinding(
                    f"permuted-triangle-{index}",
                    original.parent_subject,
                    ordered_children,
                )
                result = check_p009_triangle_cardinality(
                    P009TriangleCardinalityInput(
                        P009CandidateScope.TRIANGLE,
                        permuted,
                    )
                )
                self.assertIs(
                    P009CardinalityStatus.CARDINALITY_SATISFIED,
                    result.status,
                )
                self.assertIs(permuted, result.binding)
                self.assertEqual(ordered_children, result.binding.ordered_children)
                self.assertIn("no child family", result.reason)
                self.assertIn("label", result.reason)

    def test_wrong_input_object_and_input_subclass_fail_closed(self) -> None:
        class InputSubclass(P009TriangleCardinalityInput):
            __slots__ = ()

        subclass = InputSubclass(
            P009CandidateScope.TRIANGLE,
            binding_with_children(5),
        )
        for candidate in (None, {}, object(), subclass):
            with self.subTest(candidate_type=type(candidate).__name__):
                result = check_p009_triangle_cardinality(candidate)
                self.assertIs(
                    P009CardinalityStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertIs(result.fatal_to_candidate, False)
                self.assertIsNone(result.binding)

    def test_binding_copy_and_reconstruction_obey_exact_input_contract(self) -> None:
        original = binding_with_children(5)
        self.assertIs(original, copy.copy(original))
        self.assertIs(original, copy.deepcopy(original))
        copied = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(
                P009CandidateScope.TRIANGLE,
                copy.copy(original),
            )
        )
        self.assertIs(original, copied.binding)

        reconstructed = OrderedChildBinding(
            "reconstructed-triangle",
            original.parent_subject,
            original.ordered_children,
        )
        result = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, reconstructed)
        )
        self.assertIs(P009CardinalityStatus.CARDINALITY_SATISFIED, result.status)
        self.assertIs(reconstructed, result.binding)

    def test_every_status_family_has_exact_traceability_and_fatality(self) -> None:
        results = (
            result_for(5)[1],
            result_for(4)[1],
            check_p009_triangle_cardinality(
                P009TriangleCardinalityInput(None, binding_with_children(5))
            ),
            check_p009_triangle_cardinality(
                P009TriangleCardinalityInput("FLAT", binding_with_children(5))
            ),
        )
        self.assertEqual(set(P009CardinalityStatus), {result.status for result in results})
        for result in results:
            with self.subTest(status=result.status):
                self.assertEqual("P009", result.principle_id)
                self.assertIs(SourceClassification.DEFINITION, result.source_class)
                self.assertIs(P009ExecutionRole.HARD_VALIDATION, result.execution_role)
                self.assertEqual(
                    "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
                    result.behavior_id,
                )
                self.assertEqual(EXPECTED_PROTECTED_SOURCES, result.protected_sources)
                self.assertTrue(result.reason)
                self.assertEqual(result.status.value, result.outcome)
                self.assertIs(
                    result.fatal_to_candidate,
                    result.status is P009CardinalityStatus.CARDINALITY_VIOLATED,
                )

    def test_genuine_violation_certifies_with_exact_origin_and_invalidity(self) -> None:
        binding, origin = result_for(4)
        certificate = certify_structural_invalidity(origin)
        self.assertIs(origin, certificate.origin)
        self.assertIs(binding, certificate.origin.binding)
        self.assertEqual("P009", certificate.origin_principle_id)
        self.assertEqual(
            "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            certificate.origin_behavior_id,
        )
        self.assertIs(SourceClassification.DEFINITION, certificate.origin_source_class)
        self.assertIs(P009ExecutionRole.HARD_VALIDATION, certificate.origin_execution_role)
        self.assertIs(P009CardinalityStatus.CARDINALITY_VIOLATED, certificate.origin_status)
        self.assertIs(certificate.fatal_to_candidate, True)
        self.assertIs(StructuralValidity.INVALID, certificate.structural_validity)

    def test_satisfied_and_unresolved_results_cannot_certify(self) -> None:
        results = (
            result_for(5)[1],
            check_p009_triangle_cardinality(
                P009TriangleCardinalityInput(None, binding_with_children(5))
            ),
            check_p009_triangle_cardinality(
                P009TriangleCardinalityInput("FLAT", binding_with_children(5))
            ),
        )
        for result in results:
            with self.subTest(status=result.status):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    certify_structural_invalidity(result)

    def test_manual_copied_replaced_serialized_and_fake_results_do_not_certify(self) -> None:
        _, genuine = result_for(4)
        manual = type(genuine)(
            **{field.name: getattr(genuine, field.name) for field in fields(genuine)}
        )
        with self.assertRaises(TypeError):
            pickle.dumps(genuine)

        class Duck:
            pass

        class ResultSubclass(P009TriangleCardinalityResult):
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
            ("status", P009CardinalityStatus.CARDINALITY_SATISFIED),
            ("principle_id", "P999"),
            ("source_class", SourceClassification.RULE),
            ("execution_role", "HARD_VALIDATION"),
            ("protected_sources", ("tampered",)),
            ("behavior_id", "TAMPERED"),
            ("outcome", "TAMPERED"),
            ("reason", "tampered"),
            ("fatal_to_candidate", False),
        ):
            _, origin = result_for(4)
            certificate = certify_structural_invalidity(origin)
            object.__setattr__(origin, field_name, replacement)
            with self.subTest(field=field_name):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    _ = certificate.structural_validity

    def test_p009_is_exactly_sixth_structural_producer_and_prior_code_unchanged(self) -> None:
        self.assertIs(structural_private._REGISTRY_SEALED, True)
        self.assertEqual(6, len(structural_private._PRODUCERS))
        self.assertEqual(6, len(structural_private._BEHAVIOR_IDS))
        self.assertIn(P009TriangleCardinalityResult, structural_private._PRODUCERS)
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            },
            structural_private._BEHAVIOR_IDS,
        )
        expected = {
            "_structural_invalidity_certification.py": (
                20580,
                "b3f321a3e76f93ff37e995e9a1694a058fce68d0adbb20f6572ba2fc2082f615",
            ),
            "p004.py": (
                4509,
                "397a438f5710a5a138b112c473a512a0df930e33ed7f10279e74589501500d1c",
            ),
            "degree_peer_consistency.py": (
                4615,
                "faf0fb3761d23190f2a5719ae2c62a2cb6c2aa64a739fd8761e709e9be7b4b07",
            ),
            "parent_child_degree_adjacency.py": (
                5250,
                "a4fca4714c850c3ee2d20dbb245c6929119789b7fa10097c661b8c09db497131",
            ),
            "p007_single_zigzag_cardinality.py": (
                5104,
                "c8f288de9619c5decd6b99c82cee1d21a72ad0824921e9326472b0de35a3973f",
            ),
            "p008_flat_cardinality.py": (
                4924,
                "824fdec5f57c813b1d2345a90d21ee2dc21cca0359bd64139f8f55dee22f7a08",
            ),
        }
        root = support.SRC / "elliott_methodology_kernel"
        for name, (expected_length, expected_hash) in expected.items():
            payload = (root / name).read_bytes()
            with self.subTest(name=name):
                self.assertEqual(expected_length, len(payload))
                self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest())

    def test_p009_is_not_validated_family_proof_and_registry_remains_empty(self) -> None:
        for result in (result_for(5)[1], result_for(4)[1]):
            with self.subTest(status=result.status):
                with self.assertRaises(ValidatedInternalFamilyCertificationError):
                    certify_validated_internal_family(result)
        self.assertIs(family_private._REGISTRY_SEALED, True)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)

    def test_input_and_result_surfaces_claim_cardinality_only(self) -> None:
        expected_input = ("candidate_scope", "binding")
        self.assertEqual(
            expected_input,
            tuple(P009TriangleCardinalityInput.__dataclass_fields__),
        )
        self.assertEqual(
            expected_input,
            tuple(inspect.signature(P009TriangleCardinalityInput).parameters),
        )

        expected_result = (
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
        self.assertEqual(
            expected_result,
            tuple(P009TriangleCardinalityResult.__dataclass_fields__),
        )
        self.assertEqual(
            expected_result,
            tuple(inspect.signature(P009TriangleCardinalityResult).parameters),
        )
        forbidden = {
            "family",
            "leg_family",
            "subtype",
            "pattern_valid",
            "complete",
            "degree",
            "chronology",
            "position",
            "geometry",
            "wave_a",
            "wave_b",
            "wave_c",
            "wave_d",
            "wave_e",
            "three_three_five",
            "evidence_state",
        }
        self.assertTrue(
            forbidden.isdisjoint(P009TriangleCardinalityInput.__dataclass_fields__)
        )
        self.assertTrue(
            forbidden.isdisjoint(P009TriangleCardinalityResult.__dataclass_fields__)
        )

    def test_module_dependencies_and_capabilities_remain_narrow(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "p009_triangle_cardinality.py"
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
            {
                "__future__",
                "dataclasses",
                "enum",
                "._structural_invalidity_certification",
                ".models",
                ".subject_binding",
            },
            imported,
        )
        self.assertTrue({"open", "exec", "eval", "__import__"}.isdisjoint(called_names))
        for forbidden in (
            "P005",
            "P006",
            "P007",
            "P008",
            "P010",
            "3-3-5",
            "three-three-five",
            "contracting triangle",
            "ascending triangle",
            "descending triangle",
            "expanding triangle",
            "ending diagonal",
            "leading diagonal",
            "corrective/three-wave",
            "Wave E",
            "trend line",
            "trendline",
            "wave four",
            "Fibonacci",
            "breadth",
            "psychology",
            "fundamentals",
            "TradingView",
            "socket",
            "subprocess",
            "requests",
            "urllib",
            "playwright",
            "selenium",
            "ranking",
            "Preferred",
            "Alternative",
            "pivot",
            "timeframe",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_executable_inventory_is_exactly_nine_and_analyze_is_not_implemented(self) -> None:
        observed = set()
        special_names = {"NO_RESCUE_BEHAVIOR", "P003_BEHAVIOR"}
        root = support.SRC / "elliott_methodology_kernel"
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign) or not isinstance(
                    node.value, ast.Constant
                ):
                    continue
                if not isinstance(node.value.value, str):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and (
                        target.id.endswith("_BEHAVIOR_ID")
                        or target.id in special_names
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
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )
        source_text = inspect.getsource(MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, kernel.KernelStatus.NOT_IMPLEMENTED)


if __name__ == "__main__":
    unittest.main()
