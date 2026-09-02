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
import elliott_methodology_kernel.subject_binding as subject_binding_module
from elliott_methodology_kernel import AnalyzedWaveSubject, OrderedChildBinding
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


def binding(
    *children: AnalyzedWaveSubject,
    parent: AnalyzedWaveSubject | None = None,
    identifier: str = "binding-1",
) -> OrderedChildBinding:
    return OrderedChildBinding(
        binding_id=identifier,
        parent_subject=parent or subject("parent"),
        ordered_children=children,
    )


class SubjectOrderedChildBindingTests(unittest.TestCase):
    def assert_no_certification_authority(self, value: object) -> None:
        with self.assertRaises(ValidatedInternalFamilyCertificationError):
            certify_validated_internal_family(value)
        with self.assertRaises(StructuralInvalidityCertificationError):
            certify_structural_invalidity(value)

    def test_subject_surface_is_minimum_non_authoritative_identity(self) -> None:
        self.assertEqual(
            {"subject_id", "observation_provenance_ref"},
            {field.name for field in fields(AnalyzedWaveSubject)},
        )
        candidate = subject("candidate")
        self.assertEqual("candidate", candidate.subject_id)
        self.assertEqual(
            "observations:sha256:example",
            candidate.observation_provenance_ref,
        )
        self.assertTrue(is_dataclass(candidate))
        self.assertTrue(AnalyzedWaveSubject.__dataclass_params__.frozen)
        self.assertFalse(AnalyzedWaveSubject.__dataclass_params__.eq)
        self.assertFalse(hasattr(candidate, "__dict__"))
        self.assertIs(candidate, weakref.ref(candidate)())

    def test_subject_rejects_missing_or_malformed_audit_references(self) -> None:
        invalid_values = (None, "", "   ", 1, True, object())
        for value in invalid_values:
            with self.subTest(field="subject_id", value=value):
                with self.assertRaises(ValueError):
                    AnalyzedWaveSubject(value, "provenance")
            with self.subTest(field="observation_provenance_ref", value=value):
                with self.assertRaises(ValueError):
                    AnalyzedWaveSubject("subject", value)

    def test_subject_identity_is_object_identity_not_field_equality(self) -> None:
        first = subject("same-audit-id")
        second = subject("same-audit-id")
        self.assertIsNot(first, second)
        self.assertNotEqual(first, second)

    def test_subject_is_ordinary_api_immutable(self) -> None:
        candidate = subject("candidate")
        with self.assertRaises(FrozenInstanceError):
            candidate.subject_id = "replacement"
        with self.assertRaises(FrozenInstanceError):
            candidate.observation_provenance_ref = "replacement"

    def test_binding_surface_retains_exact_parent_and_ordered_references(self) -> None:
        parent = subject("parent")
        first = subject("first")
        second = subject("second")
        candidate_binding = binding(first, second, parent=parent)
        self.assertEqual(
            {"binding_id", "parent_subject", "ordered_children"},
            {field.name for field in fields(OrderedChildBinding)},
        )
        self.assertIs(parent, candidate_binding.parent_subject)
        self.assertIs(first, candidate_binding.ordered_children[0])
        self.assertIs(second, candidate_binding.ordered_children[1])
        self.assertEqual((first, second), candidate_binding.ordered_children)
        self.assertTrue(OrderedChildBinding.__dataclass_params__.frozen)
        self.assertFalse(OrderedChildBinding.__dataclass_params__.eq)
        self.assertFalse(hasattr(candidate_binding, "__dict__"))
        self.assertIs(candidate_binding, weakref.ref(candidate_binding)())

    def test_binding_id_rejects_missing_or_malformed_audit_references(self) -> None:
        parent = subject("parent")
        invalid_values = (None, "", "   ", 1, True, object())
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    OrderedChildBinding(value, parent, ())

    def test_tuple_order_is_deterministic_and_purely_ordinal(self) -> None:
        children = tuple(subject(f"child-{index}") for index in range(1, 6))
        candidate_binding = binding(*children)
        for index, expected in enumerate(children):
            self.assertIs(expected, candidate_binding.ordered_children[index])
        self.assertFalse(hasattr(subject_binding_module, "WavePosition"))
        self.assertFalse(hasattr(subject_binding_module, "WAVE_1"))
        self.assert_no_certification_authority(candidate_binding)

    def test_zero_children_is_explicitly_allowed_without_completeness_claim(self) -> None:
        candidate_binding = binding()
        self.assertEqual((), candidate_binding.ordered_children)
        self.assert_no_certification_authority(candidate_binding)

    def test_one_child_is_explicitly_allowed_without_completeness_claim(self) -> None:
        only_child = subject("only-child")
        candidate_binding = binding(only_child)
        self.assertEqual(1, len(candidate_binding.ordered_children))
        self.assertIs(only_child, candidate_binding.ordered_children[0])
        self.assert_no_certification_authority(candidate_binding)

    def test_ordered_children_requires_an_exact_tuple(self) -> None:
        parent = subject("parent")
        child = subject("child")
        with self.assertRaises(TypeError):
            OrderedChildBinding("binding", parent, [child])
        with self.assertRaises(TypeError):
            OrderedChildBinding("binding", parent, iter((child,)))

    def test_parent_and_children_require_exact_subject_type(self) -> None:
        class SubjectSubclass(AnalyzedWaveSubject):
            pass

        subclass = SubjectSubclass("subclass", "provenance")
        exact = subject("exact")
        with self.assertRaises(TypeError):
            OrderedChildBinding("binding", subclass, (exact,))
        with self.assertRaises(TypeError):
            OrderedChildBinding("binding", exact, (subclass,))
        with self.assertRaises(TypeError):
            OrderedChildBinding("binding", exact, (object(),))

    def test_parent_cannot_be_reused_as_its_own_child(self) -> None:
        parent = subject("parent")
        with self.assertRaises(ValueError):
            binding(parent, parent=parent)

    def test_same_child_object_cannot_occupy_multiple_positions(self) -> None:
        repeated = subject("repeated")
        with self.assertRaises(ValueError):
            binding(repeated, repeated)

    def test_duplicate_subject_ids_are_rejected_within_one_binding(self) -> None:
        first = subject("duplicate")
        second = subject("duplicate")
        self.assertIsNot(first, second)
        with self.assertRaises(ValueError):
            binding(first, second)
        with self.assertRaises(ValueError):
            binding(subject("parent"), parent=subject("parent"))

    def test_distinct_child_identities_with_shared_provenance_are_allowed(self) -> None:
        first = subject("first")
        second = subject("second")
        candidate_binding = binding(first, second)
        self.assertEqual(
            first.observation_provenance_ref,
            second.observation_provenance_ref,
        )
        self.assertIsNot(first, second)
        self.assertEqual((first, second), candidate_binding.ordered_children)

    def test_child_reuse_across_separate_untrusted_bindings_is_allowed(self) -> None:
        shared = subject("shared-child")
        first = binding(
            shared,
            parent=subject("first-parent"),
            identifier="first-binding",
        )
        second = binding(
            shared,
            parent=subject("second-parent"),
            identifier="second-binding",
        )
        self.assertIs(shared, first.ordered_children[0])
        self.assertIs(shared, second.ordered_children[0])
        self.assertIsNot(first, second)
        self.assert_no_certification_authority(first)
        self.assert_no_certification_authority(second)

    def test_same_parent_can_have_distinct_untrusted_ordering_assertions(self) -> None:
        parent = subject("parent")
        first_child = subject("first-child")
        second_child = subject("second-child")
        first = binding(
            first_child,
            second_child,
            parent=parent,
            identifier="first-binding",
        )
        reordered = binding(
            second_child,
            first_child,
            parent=parent,
            identifier="reordered-binding",
        )
        self.assertIs(parent, first.parent_subject)
        self.assertIs(parent, reordered.parent_subject)
        self.assertIsNot(first, reordered)
        self.assertNotEqual(first.ordered_children, reordered.ordered_children)
        self.assert_no_certification_authority(first)
        self.assert_no_certification_authority(reordered)

    def test_binding_is_ordinary_api_immutable_and_parent_specific(self) -> None:
        parent = subject("parent")
        child = subject("child")
        candidate_binding = binding(child, parent=parent)
        with self.assertRaises(FrozenInstanceError):
            candidate_binding.parent_subject = subject("other-parent")
        with self.assertRaises(FrozenInstanceError):
            candidate_binding.ordered_children = ()
        self.assertIs(parent, candidate_binding.parent_subject)
        self.assertEqual((child,), candidate_binding.ordered_children)

    def test_copy_and_deepcopy_preserve_exact_immutable_identity(self) -> None:
        parent = subject("parent")
        child = subject("child")
        candidate_binding = binding(child, parent=parent)
        for value in (parent, child, candidate_binding):
            self.assertIs(value, copy.copy(value))
            self.assertIs(value, copy.deepcopy(value))

    def test_dataclass_replacement_is_a_new_untrusted_identity(self) -> None:
        original_parent = subject("parent")
        original_child = subject("child")
        original = binding(original_child, parent=original_parent)
        replaced_parent = replace(original_parent)
        replacement = replace(
            original,
            binding_id="replacement-binding",
            parent_subject=replaced_parent,
        )
        self.assertIsNot(original_parent, replaced_parent)
        self.assertNotEqual(original_parent, replaced_parent)
        self.assertIsNot(original, replacement)
        self.assertNotEqual(original, replacement)
        self.assertIs(original_parent, original.parent_subject)
        self.assertIs(replaced_parent, replacement.parent_subject)
        self.assert_no_certification_authority(replacement)

    def test_pickle_is_rejected_for_subject_and_binding(self) -> None:
        candidate = subject("candidate")
        candidate_binding = binding(candidate)
        for value in (candidate, candidate_binding):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    pickle.dumps(value)

    def test_json_is_audit_data_only_and_cannot_rehydrate_authority(self) -> None:
        parent = subject("parent")
        child = subject("child")
        original = binding(child, parent=parent)
        audit_record = json.loads(json.dumps(asdict(original)))
        self.assertIsInstance(audit_record, dict)
        self.assertEqual("binding-1", audit_record["binding_id"])
        self.assertEqual("parent", audit_record["parent_subject"]["subject_id"])
        self.assertIsInstance(audit_record["ordered_children"], list)
        self.assert_no_certification_authority(audit_record)
        with self.assertRaises(TypeError):
            OrderedChildBinding(**audit_record)

        rehydrated_parent = AnalyzedWaveSubject(**audit_record["parent_subject"])
        rehydrated_children = tuple(
            AnalyzedWaveSubject(**item)
            for item in audit_record["ordered_children"]
        )
        rehydrated = OrderedChildBinding(
            binding_id=audit_record["binding_id"],
            parent_subject=rehydrated_parent,
            ordered_children=rehydrated_children,
        )
        self.assertIsNot(original, rehydrated)
        self.assertIsNot(original.parent_subject, rehydrated.parent_subject)
        self.assert_no_certification_authority(rehydrated)

    def test_types_have_no_methodology_or_authority_fields(self) -> None:
        candidate = subject("candidate")
        candidate_binding = binding(candidate)
        forbidden = (
            "family",
            "family_kind",
            "pattern",
            "position",
            "degree",
            "timeframe",
            "pivot",
            "start_anchor",
            "end_anchor",
            "status",
            "outcome",
            "structural_validity",
            "fatal_to_candidate",
            "principle_id",
            "source_class",
            "execution_role",
            "certify",
            "issue",
            "register",
        )
        for value in (candidate, candidate_binding):
            for name in forbidden:
                self.assertFalse(hasattr(value, name), name)

    def test_types_are_not_validator_results_or_certificates(self) -> None:
        candidate = subject("candidate")
        candidate_binding = binding(candidate)
        for value in (candidate, candidate_binding):
            self.assertNotIsInstance(
                value,
                family_private.InternalFamilyValidatorResult,
            )
            self.assertNotIsInstance(
                value,
                structural_private.StructuralValidatorResult,
            )
            self.assert_no_certification_authority(value)

    def test_public_surface_exports_only_the_two_binding_types(self) -> None:
        self.assertEqual(
            ["AnalyzedWaveSubject", "OrderedChildBinding"],
            subject_binding_module.__all__,
        )
        for name in subject_binding_module.__all__:
            self.assertIn(name, public_contracts.__all__)
            self.assertIn(name, kernel.__all__)
            self.assertIs(getattr(public_contracts, name), getattr(kernel, name))
        for forbidden in (
            "bind_ordered_children",
            "certify_subject",
            "register_subject",
            "issue_subject",
            "SubjectBindingCertificate",
        ):
            self.assertFalse(hasattr(subject_binding_module, forbidden))
            self.assertFalse(hasattr(public_contracts, forbidden))
            self.assertFalse(hasattr(kernel, forbidden))

    def test_module_has_no_certification_or_external_capabilities(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "subject_binding.py"
        )
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add("." * node.level + (node.module or ""))
        self.assertEqual({"__future__", "dataclasses"}, imported_modules)
        for forbidden in (
            "InternalFamilyKind",
            "InternalFamilyValidatorResult",
            "StructuralValidatorResult",
            "StructuralValidity",
            "P003SearchTheme",
            "P005",
            "P006",
            "P010",
            "elliott_runtime",
            "TradingView",
            "market_data",
            "candidate_generation",
            "ranking",
            "evidence",
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

    def test_certification_algorithms_and_registries_remain_unchanged(self) -> None:
        expected = {
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
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(5, len(structural_private._PRODUCERS))
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)

    def test_no_family_producer_or_new_methodology_behavior_exists(self) -> None:
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
                            node.value.value,
                            str,
                        ):
                            observed.add(node.value.value)
                if (
                    path.name
                    != "_validated_internal_family_certification.py"
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
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )
        self.assertEqual([], registration_calls)

    def test_methodology_kernel_remains_not_implemented(self) -> None:
        source_text = inspect.getsource(kernel.MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertNotIn("OrderedChildBinding", source_text)


if __name__ == "__main__":
    unittest.main()
