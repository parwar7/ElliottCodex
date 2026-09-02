import ast
import copy
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
import hashlib
import inspect
import json
import pickle
import unittest
import weakref

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.contracts as public_contracts
import elliott_methodology_kernel.normal_impulse_five_slot_view as view_module
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    NormalImpulseFiveSlotCandidateView,
    NormalImpulseFiveSlotCardinalityError,
    OrderedChildBinding,
    P003SearchTheme,
)
from elliott_methodology_kernel.contracts import (
    StructuralInvalidityCertificationError,
    ValidatedInternalFamilyCertificationError,
    certify_structural_invalidity,
    certify_validated_internal_family,
)


def subject(identifier: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(
        subject_id=identifier,
        observation_provenance_ref="observations:sha256:example",
    )


def binding_with_children(
    child_count: int = 5,
    *,
    parent: AnalyzedWaveSubject | None = None,
    identifier: str = "binding-1",
) -> OrderedChildBinding:
    return OrderedChildBinding(
        binding_id=identifier,
        parent_subject=parent or subject("parent"),
        ordered_children=tuple(
            subject(f"child-{index}") for index in range(1, child_count + 1)
        ),
    )


class NormalImpulseFiveSlotCandidateViewTests(unittest.TestCase):
    def assert_no_certification_authority(self, value: object) -> None:
        with self.assertRaises(ValidatedInternalFamilyCertificationError):
            certify_validated_internal_family(value)
        with self.assertRaises(StructuralInvalidityCertificationError):
            certify_structural_invalidity(value)

    def test_public_surface_is_one_exact_binding_input(self) -> None:
        signature = inspect.signature(NormalImpulseFiveSlotCandidateView)
        self.assertEqual(["binding"], list(signature.parameters))
        self.assertEqual(
            {"binding"},
            {field.name for field in fields(NormalImpulseFiveSlotCandidateView)},
        )
        candidate_binding = binding_with_children()
        view = NormalImpulseFiveSlotCandidateView(candidate_binding)
        self.assertIs(candidate_binding, view.binding)
        self.assertTrue(is_dataclass(view))
        self.assertTrue(NormalImpulseFiveSlotCandidateView.__dataclass_params__.frozen)
        self.assertFalse(NormalImpulseFiveSlotCandidateView.__dataclass_params__.eq)
        self.assertFalse(hasattr(view, "__dict__"))
        self.assertIs(view, weakref.ref(view)())

    def test_exact_parent_child_and_tuple_identities_are_preserved(self) -> None:
        parent = subject("parent")
        candidate_binding = binding_with_children(parent=parent)
        children = candidate_binding.ordered_children
        view = NormalImpulseFiveSlotCandidateView(candidate_binding)
        self.assertIs(candidate_binding, view.binding)
        self.assertIs(parent, view.binding.parent_subject)
        self.assertIs(children, view.binding.ordered_children)
        for index, child in enumerate(children):
            self.assertIs(child, view.binding.ordered_children[index])

    def test_all_five_positions_are_derived_from_exact_tuple_order(self) -> None:
        candidate_binding = binding_with_children()
        view = NormalImpulseFiveSlotCandidateView(candidate_binding)
        self.assertIs(candidate_binding.ordered_children[0], view.position_1)
        self.assertIs(candidate_binding.ordered_children[1], view.position_2)
        self.assertIs(candidate_binding.ordered_children[2], view.position_3)
        self.assertIs(candidate_binding.ordered_children[3], view.position_4)
        self.assertIs(candidate_binding.ordered_children[4], view.position_5)
        self.assertIsNot(view.position_1, view.position_5)

    def test_reordered_binding_retains_its_own_exact_proposed_order(self) -> None:
        parent = subject("parent")
        original = binding_with_children(parent=parent, identifier="original")
        reordered = OrderedChildBinding(
            binding_id="reordered",
            parent_subject=parent,
            ordered_children=tuple(reversed(original.ordered_children)),
        )
        original_view = NormalImpulseFiveSlotCandidateView(original)
        reordered_view = NormalImpulseFiveSlotCandidateView(reordered)
        self.assertIs(original.ordered_children[0], original_view.position_1)
        self.assertIs(original.ordered_children[4], reordered_view.position_1)
        self.assertIs(original.ordered_children[0], reordered_view.position_5)
        self.assertIsNot(original_view, reordered_view)

    def test_every_wrong_cardinality_is_rejected_by_contract(self) -> None:
        for child_count in (0, 1, 2, 3, 4, 6, 7, 10):
            with self.subTest(child_count=child_count):
                with self.assertRaises(NormalImpulseFiveSlotCardinalityError):
                    NormalImpulseFiveSlotCandidateView(
                        binding_with_children(child_count)
                    )

    def test_cardinality_failure_is_not_methodology_invalidity(self) -> None:
        with self.assertRaises(NormalImpulseFiveSlotCardinalityError) as raised:
            NormalImpulseFiveSlotCandidateView(binding_with_children(4))
        error = raised.exception
        self.assertIsInstance(error, ValueError)
        for name in (
            "status",
            "outcome",
            "structural_validity",
            "fatal_to_candidate",
            "principle_id",
            "source_class",
            "execution_role",
            "behavior_id",
        ):
            self.assertFalse(hasattr(error, name), name)
        self.assertNotIsInstance(error, structural_private.StructuralValidatorResult)
        self.assertNotIsInstance(error, family_private.InternalFamilyValidatorResult)

    def test_only_exact_ordered_child_binding_is_accepted(self) -> None:
        class BindingSubclass(OrderedChildBinding):
            pass

        exact = binding_with_children()
        subclass = BindingSubclass(
            exact.binding_id,
            exact.parent_subject,
            exact.ordered_children,
        )
        wrong_inputs = (
            None,
            "binding",
            ["one", "two", "three", "four", "five"],
            ("one", "two", "three", "four", "five"),
            {"ordered_children": exact.ordered_children},
            P003SearchTheme.MOTIVE,
            subclass,
        )
        for value in wrong_inputs:
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    NormalImpulseFiveSlotCandidateView(value)

    def test_view_cannot_be_subclassed_to_bypass_construction(self) -> None:
        with self.assertRaises(TypeError):
            class ForgedView(NormalImpulseFiveSlotCandidateView):
                def __init__(self) -> None:
                    pass

        class SwallowSubclassHook:
            def __init_subclass__(cls, **kwargs: object) -> None:
                pass

        with self.assertRaises(TypeError):
            class MultipleInheritanceBypass(
                SwallowSubclassHook,
                NormalImpulseFiveSlotCandidateView,
            ):
                def __post_init__(self) -> None:
                    pass

    def test_five_detached_ids_cannot_substitute_for_one_binding(self) -> None:
        with self.assertRaises(TypeError):
            NormalImpulseFiveSlotCandidateView("1", "2", "3", "4", "5")

    def test_view_and_source_order_are_ordinary_api_immutable(self) -> None:
        candidate_binding = binding_with_children()
        view = NormalImpulseFiveSlotCandidateView(candidate_binding)
        with self.assertRaises(FrozenInstanceError):
            view.binding = binding_with_children()
        with self.assertRaises((FrozenInstanceError, TypeError)):
            view.position_1 = subject("replacement")
        with self.assertRaises(FrozenInstanceError):
            candidate_binding.ordered_children = tuple(
                reversed(candidate_binding.ordered_children)
            )
        with self.assertRaises(TypeError):
            candidate_binding.ordered_children[0] = subject("replacement")

    def test_copy_and_deepcopy_preserve_exact_non_authoritative_identity(self) -> None:
        candidate_binding = binding_with_children()
        view = NormalImpulseFiveSlotCandidateView(candidate_binding)
        self.assertIs(view, copy.copy(view))
        self.assertIs(view, copy.deepcopy(view))
        self.assertIs(candidate_binding, copy.copy(view).binding)
        self.assert_no_certification_authority(view)

    def test_dataclass_replacement_is_a_distinct_untrusted_view(self) -> None:
        original = NormalImpulseFiveSlotCandidateView(binding_with_children())
        replacement = replace(original)
        self.assertIsNot(original, replacement)
        self.assertNotEqual(original, replacement)
        self.assertIs(original.binding, replacement.binding)
        self.assert_no_certification_authority(replacement)
        with self.assertRaises(NormalImpulseFiveSlotCardinalityError):
            replace(original, binding=binding_with_children(4))

    def test_pickle_is_rejected(self) -> None:
        view = NormalImpulseFiveSlotCandidateView(binding_with_children())
        with self.assertRaises(TypeError):
            pickle.dumps(view)

    def test_json_is_audit_only_and_cannot_reconstruct_binding_authority(self) -> None:
        original = NormalImpulseFiveSlotCandidateView(binding_with_children())
        audit_record = json.loads(json.dumps(asdict(original)))
        self.assertIsInstance(audit_record, dict)
        self.assertEqual("binding-1", audit_record["binding"]["binding_id"])
        with self.assertRaises(TypeError):
            NormalImpulseFiveSlotCandidateView(**audit_record)
        self.assert_no_certification_authority(audit_record)

        binding_record = audit_record["binding"]
        rehydrated_parent = AnalyzedWaveSubject(
            **binding_record["parent_subject"]
        )
        rehydrated_children = tuple(
            AnalyzedWaveSubject(**item)
            for item in binding_record["ordered_children"]
        )
        rehydrated_binding = OrderedChildBinding(
            binding_id=binding_record["binding_id"],
            parent_subject=rehydrated_parent,
            ordered_children=rehydrated_children,
        )
        rehydrated_view = NormalImpulseFiveSlotCandidateView(rehydrated_binding)
        self.assertIsNot(original, rehydrated_view)
        self.assertIsNot(original.binding, rehydrated_view.binding)
        self.assertIsNot(original.position_1, rehydrated_view.position_1)
        self.assert_no_certification_authority(rehydrated_view)

    def test_view_has_no_methodology_or_authority_fields(self) -> None:
        view = NormalImpulseFiveSlotCandidateView(binding_with_children())
        forbidden = (
            "family",
            "family_kind",
            "pattern",
            "degree",
            "timeframe",
            "pivot",
            "bars",
            "start_anchor",
            "end_anchor",
            "status",
            "outcome",
            "structural_validity",
            "fatal_to_candidate",
            "principle_id",
            "source_class",
            "execution_role",
            "behavior_id",
            "evidence",
            "rank",
            "preferred",
            "alternative",
            "certify",
            "issue",
            "register",
        )
        for name in forbidden:
            self.assertFalse(hasattr(view, name), name)

    def test_view_is_not_a_validator_result_or_certificate(self) -> None:
        view = NormalImpulseFiveSlotCandidateView(binding_with_children())
        self.assertNotIsInstance(view, structural_private.StructuralValidatorResult)
        self.assertNotIsInstance(view, family_private.InternalFamilyValidatorResult)
        self.assertNotIsInstance(
            view, structural_private.CertifiedStructuralInvalidity
        )
        self.assertNotIsInstance(
            view, family_private.CertifiedValidatedInternalFamily
        )
        self.assert_no_certification_authority(view)

    def test_p003_search_theme_cannot_substitute_or_convert_to_view(self) -> None:
        with self.assertRaises(TypeError):
            NormalImpulseFiveSlotCandidateView(P003SearchTheme.MOTIVE)
        self.assertFalse(hasattr(view_module, "from_p003_theme"))
        self.assertFalse(hasattr(view_module, "map_search_theme"))

    def test_public_exports_are_exact_and_non_certifying(self) -> None:
        expected = [
            "NormalImpulseFiveSlotCandidateView",
            "NormalImpulseFiveSlotCardinalityError",
        ]
        self.assertEqual(expected, view_module.__all__)
        for name in expected:
            self.assertIn(name, public_contracts.__all__)
            self.assertIn(name, kernel.__all__)
            self.assertIs(getattr(view_module, name), getattr(public_contracts, name))
            self.assertIs(getattr(view_module, name), getattr(kernel, name))
        for forbidden in (
            "create_five_slot_view",
            "validate_five_slot_view",
            "certify_five_slot_view",
            "register_five_slot_view",
            "FiveSlotCertificate",
            "WavePosition",
        ):
            self.assertFalse(hasattr(view_module, forbidden))

    def test_module_has_only_contract_local_dependencies(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "normal_impulse_five_slot_view.py"
        )
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add("." * node.level + (node.module or ""))
        self.assertEqual(
            {"__future__", "dataclasses", ".subject_binding"},
            imported_modules,
        )
        for forbidden in (
            "5-3-5-3-5",
            "P004",
            "P005",
            "P006",
            "P010",
            "InternalFamilyKind",
            "StructuralValidity",
            "extension",
            "truncation",
            "diagonal",
            "pivot",
            "timeframe",
            "degree",
            "Fibonacci",
            "evidence",
            "ranking",
            "elliott_runtime",
            "TradingView",
            "provider",
            "monitoring",
            "alert",
            "subprocess",
            "socket",
            "urllib",
            "requests",
            "playwright",
            "selenium",
            "powershell",
            "cmd.exe",
            "pip install",
        ):
            self.assertNotIn(forbidden, source_text)
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(
            {"open", "exec", "eval", "__import__"}.isdisjoint(called_names)
        )

    def test_subject_binding_and_certification_algorithms_are_unchanged(self) -> None:
        expected = {
            "subject_binding.py": (
                3441,
                "063de9702dd3837dbc4d1de3efa5633481eb6834991f066d418d042fe119f4aa",
            ),
            "_structural_invalidity_certification.py": (
                20580,
                "b3f321a3e76f93ff37e995e9a1694a058fce68d0adbb20f6572ba2fc2082f615",
            ),
            "_validated_internal_family_certification.py": (
                29951,
                "88588fd60ec247d18c7f89ae4c8eda360f0b3f8d75272fe4d18a38a10201bdbc",
            ),
        }
        kernel_root = support.SRC / "elliott_methodology_kernel"
        for filename, (expected_bytes, expected_hash) in expected.items():
            payload = (kernel_root / filename).read_bytes()
            with self.subTest(filename=filename):
                self.assertEqual(expected_bytes, len(payload))
                self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest())

    def test_family_registry_remains_empty_and_sealed(self) -> None:
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)
        family_private._seal_internal_family_validator_registry(
            expected_result_types=()
        )
        self.assertEqual({}, family_private._PRODUCERS)

    def test_executable_methodology_inventory_remains_exactly_seven(self) -> None:
        kernel_root = support.SRC / "elliott_methodology_kernel"
        observed = set()
        special_names = {"NO_RESCUE_BEHAVIOR", "P003_BEHAVIOR"}
        registration_calls = []
        for path in kernel_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        if not (
                            target.id.endswith("_BEHAVIOR_ID")
                            or target.id in special_names
                        ):
                            continue
                        if isinstance(node.value, ast.Constant) and isinstance(
                            node.value.value, str
                        ):
                            observed.add(node.value.value)
                if (
                    path.name != "_validated_internal_family_certification.py"
                    and isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_register_internal_family_validator"
                ):
                    registration_calls.append(str(path))
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P023_INTERNAL_VISIBILITY_GUARD",
                "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
                "P003_ONE_LARGER_DEGREE_SEARCH_THEME",
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )
        self.assertEqual([], registration_calls)

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        source_text = inspect.getsource(kernel.MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertNotIn("NormalImpulseFiveSlotCandidateView", source_text)


if __name__ == "__main__":
    unittest.main()
