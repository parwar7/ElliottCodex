import ast
import copy
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from decimal import Decimal
import hashlib
import inspect
import json
import math
import pickle
import types
import unittest
import weakref

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.contracts as public_contracts
import elliott_methodology_kernel.observed_price_binding as price_binding_module
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    SubjectBoundObservedPriceEndpointPair,
    SubjectBoundObservedPriceObservation,
)
from elliott_methodology_kernel.contracts import (
    StructuralInvalidityCertificationError,
    ValidatedInternalFamilyCertificationError,
    certify_structural_invalidity,
    certify_validated_internal_family,
)


def subject(identifier: str = "subject") -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(
        subject_id=identifier,
        observation_provenance_ref="subject-observations:sha256:example",
    )


def observation(
    observed_subject: AnalyzedWaveSubject,
    price: int | float = 100.0,
    provenance: str = "price-observation:sha256:example",
) -> SubjectBoundObservedPriceObservation:
    return SubjectBoundObservedPriceObservation(
        subject=observed_subject,
        price=price,
        observation_provenance_ref=provenance,
    )


class SubjectBoundObservedPriceEndpointPairTests(unittest.TestCase):
    def assert_no_certification_authority(self, value: object) -> None:
        with self.assertRaises(ValidatedInternalFamilyCertificationError):
            certify_validated_internal_family(value)
        with self.assertRaises(StructuralInvalidityCertificationError):
            certify_structural_invalidity(value)

    def test_observation_surface_retains_exact_subject_and_value(self) -> None:
        observed_subject = subject()
        supplied_price = 123456789
        candidate = observation(observed_subject, supplied_price)
        self.assertEqual(
            {"subject", "price", "observation_provenance_ref"},
            {field.name for field in fields(candidate)},
        )
        self.assertIs(observed_subject, candidate.subject)
        self.assertIs(supplied_price, candidate.price)
        self.assertTrue(is_dataclass(candidate))
        self.assertTrue(
            SubjectBoundObservedPriceObservation.__dataclass_params__.frozen
        )
        self.assertFalse(
            SubjectBoundObservedPriceObservation.__dataclass_params__.eq
        )
        self.assertFalse(hasattr(candidate, "__dict__"))
        self.assertIs(candidate, weakref.ref(candidate)())

    def test_approved_finite_numeric_domain_is_transport_only(self) -> None:
        observed_subject = subject()
        values = (0, -0.0, 7, -11, 1.25, -999.5)
        for value in values:
            with self.subTest(value=value):
                candidate = observation(observed_subject, value)
                self.assertIs(value, candidate.price)
                self.assertIs(observed_subject, candidate.subject)

    def test_boolean_is_rejected(self) -> None:
        observed_subject = subject()
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    observation(observed_subject, value)

    def test_nonfinite_prices_are_rejected(self) -> None:
        observed_subject = subject()
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    observation(observed_subject, value)

    def test_numeric_strings_decimal_and_malformed_prices_are_rejected(self) -> None:
        observed_subject = subject()
        invalid = ("100.0", "", Decimal("100.0"), None, object(), 1 + 2j)
        for value in invalid:
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    observation(observed_subject, value)
        with self.assertRaises(ValueError):
            observation(observed_subject, 10**1000)

    def test_provenance_is_exact_opaque_metadata(self) -> None:
        observed_subject = subject()
        provenance = "  opaque caller text  "
        candidate = observation(observed_subject, provenance=provenance)
        self.assertIs(provenance, candidate.observation_provenance_ref)
        self.assertNotEqual(
            observed_subject.observation_provenance_ref,
            candidate.observation_provenance_ref,
        )
        for invalid in (None, "", "   ", 1, True, object()):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    SubjectBoundObservedPriceObservation(
                        observed_subject,
                        100.0,
                        invalid,
                    )

    def test_subject_requires_exact_analyzed_subject_type(self) -> None:
        class SubjectSubclass(AnalyzedWaveSubject):
            pass

        subclass = SubjectSubclass("same", "provenance")
        for invalid in (None, object(), "subject", subclass):
            with self.subTest(value=type(invalid).__name__):
                with self.assertRaises(TypeError):
                    observation(invalid)

    def test_distinct_observations_with_equal_fields_keep_distinct_identity(self) -> None:
        observed_subject = subject()
        first = observation(observed_subject, 100.0, "same")
        second = observation(observed_subject, 100.0, "same")
        self.assertIsNot(first, second)
        self.assertNotEqual(first, second)
        self.assertIs(first.subject, second.subject)

    def test_pair_surface_retains_exact_subject_and_endpoint_roles(self) -> None:
        observed_subject = subject()
        proposed_start = observation(observed_subject, 100.0, "start")
        proposed_end = observation(observed_subject, 120.0, "end")
        pair = SubjectBoundObservedPriceEndpointPair(
            proposed_start,
            proposed_end,
        )
        self.assertEqual(
            {"proposed_start", "proposed_end"},
            {field.name for field in fields(pair)},
        )
        self.assertIs(proposed_start, pair.proposed_start)
        self.assertIs(proposed_end, pair.proposed_end)
        self.assertIs(observed_subject, pair.subject)
        self.assertIs(pair.subject, pair.proposed_start.subject)
        self.assertIs(pair.subject, pair.proposed_end.subject)
        self.assertTrue(
            SubjectBoundObservedPriceEndpointPair.__dataclass_params__.frozen
        )
        self.assertFalse(
            SubjectBoundObservedPriceEndpointPair.__dataclass_params__.eq
        )
        self.assertFalse(hasattr(pair, "__dict__"))
        self.assertIs(pair, weakref.ref(pair)())

    def test_same_subject_id_on_distinct_subject_object_is_rejected(self) -> None:
        first_subject = subject("same-id")
        second_subject = subject("same-id")
        self.assertIsNot(first_subject, second_subject)
        with self.assertRaises(ValueError):
            SubjectBoundObservedPriceEndpointPair(
                observation(first_subject, 100.0),
                observation(second_subject, 120.0),
            )

    def test_pair_requires_exact_observation_types(self) -> None:
        observed_subject = subject()
        exact = observation(observed_subject)
        invalid = (None, object(), "observation", {}, (observed_subject, 100.0))
        for value in invalid:
            with self.subTest(role="start", value=type(value).__name__):
                with self.assertRaises(TypeError):
                    SubjectBoundObservedPriceEndpointPair(value, exact)
            with self.subTest(role="end", value=type(value).__name__):
                with self.assertRaises(TypeError):
                    SubjectBoundObservedPriceEndpointPair(exact, value)

    def test_equal_prices_and_same_observation_are_allowed_without_meaning(self) -> None:
        observed_subject = subject()
        first = observation(observed_subject, 100.0, "first")
        second = observation(observed_subject, 100.0, "second")
        equal_value_pair = SubjectBoundObservedPriceEndpointPair(first, second)
        repeated_identity_pair = SubjectBoundObservedPriceEndpointPair(first, first)
        self.assertEqual(
            equal_value_pair.proposed_start.price,
            equal_value_pair.proposed_end.price,
        )
        self.assertIs(first, repeated_identity_pair.proposed_start)
        self.assertIs(first, repeated_identity_pair.proposed_end)
        self.assert_no_certification_authority(equal_value_pair)
        self.assert_no_certification_authority(repeated_identity_pair)

    def test_endpoint_reversal_requires_a_distinct_pair(self) -> None:
        observed_subject = subject()
        first = observation(observed_subject, 100.0, "first")
        second = observation(observed_subject, 120.0, "second")
        original = SubjectBoundObservedPriceEndpointPair(first, second)
        reversed_pair = SubjectBoundObservedPriceEndpointPair(second, first)
        self.assertIs(first, original.proposed_start)
        self.assertIs(second, original.proposed_end)
        self.assertIs(second, reversed_pair.proposed_start)
        self.assertIs(first, reversed_pair.proposed_end)
        self.assertIsNot(original, reversed_pair)

    def test_observation_and_pair_are_ordinary_api_immutable(self) -> None:
        observed_subject = subject()
        proposed_start = observation(observed_subject, 100.0)
        proposed_end = observation(observed_subject, 120.0)
        pair = SubjectBoundObservedPriceEndpointPair(proposed_start, proposed_end)
        with self.assertRaises(FrozenInstanceError):
            proposed_start.subject = subject("replacement")
        with self.assertRaises(FrozenInstanceError):
            proposed_start.price = 200.0
        with self.assertRaises(FrozenInstanceError):
            pair.proposed_start = proposed_end
        with self.assertRaises((FrozenInstanceError, TypeError)):
            pair.subject = subject("replacement")

    def test_observation_reinitialization_cannot_rebind_or_partially_mutate(self) -> None:
        original_subject = subject("original")
        candidate = observation(original_subject, 100.0, "original-provenance")
        other_subject = subject("other")
        for replacement_price in (9.0, math.nan):
            with self.subTest(replacement_price=replacement_price):
                with self.assertRaises(TypeError):
                    candidate.__init__(
                        other_subject,
                        replacement_price,
                        "replacement-provenance",
                    )
                self.assertIs(original_subject, candidate.subject)
                self.assertEqual(100.0, candidate.price)
                self.assertEqual(
                    "original-provenance",
                    candidate.observation_provenance_ref,
                )

    def test_pair_reinitialization_cannot_replace_or_reorder_roles(self) -> None:
        observed_subject = subject("original")
        proposed_start = observation(observed_subject, 100.0, "start")
        proposed_end = observation(observed_subject, 120.0, "end")
        pair = SubjectBoundObservedPriceEndpointPair(proposed_start, proposed_end)
        other_endpoint = observation(subject("other"), 130.0, "other")
        for replacement in (
            (proposed_end, proposed_start),
            (proposed_start, other_endpoint),
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(TypeError):
                    pair.__init__(*replacement)
                self.assertIs(proposed_start, pair.proposed_start)
                self.assertIs(proposed_end, pair.proposed_end)
                self.assertIs(observed_subject, pair.subject)

    def test_direct_dynamic_and_multiple_inheritance_subclasses_are_sealed(self) -> None:
        for base in (
            SubjectBoundObservedPriceObservation,
            SubjectBoundObservedPriceEndpointPair,
        ):
            with self.subTest(base=base.__name__, route="direct"):
                with self.assertRaises(TypeError):
                    type("Forged", (base,), {})
            with self.subTest(base=base.__name__, route="dynamic"):
                with self.assertRaises(TypeError):
                    types.new_class("ForgedDynamic", (base,))

        class SwallowSubclassHook:
            def __init_subclass__(cls, **kwargs: object) -> None:
                pass

        for base in (
            SubjectBoundObservedPriceObservation,
            SubjectBoundObservedPriceEndpointPair,
        ):
            with self.subTest(base=base.__name__, route="multiple"):
                with self.assertRaises(TypeError):
                    types.new_class("ForgedMultiple", (SwallowSubclassHook, base))

    def test_copy_deepcopy_and_replacement_follow_identity_policy(self) -> None:
        observed_subject = subject()
        proposed_start = observation(observed_subject, 100.0)
        proposed_end = observation(observed_subject, 120.0)
        pair = SubjectBoundObservedPriceEndpointPair(proposed_start, proposed_end)
        for value in (proposed_start, proposed_end, pair):
            self.assertIs(value, copy.copy(value))
            self.assertIs(value, copy.deepcopy(value))

        replaced_observation = replace(proposed_start)
        replaced_pair = replace(pair)
        self.assertIsNot(proposed_start, replaced_observation)
        self.assertIs(proposed_start.subject, replaced_observation.subject)
        self.assertIsNot(pair, replaced_pair)
        self.assertIs(proposed_start, replaced_pair.proposed_start)
        with self.assertRaises(ValueError):
            replace(pair, proposed_end=observation(subject("other"), 120.0))
        with self.assertRaises(ValueError):
            replace(proposed_start, price=math.nan)

    def test_pickle_is_rejected(self) -> None:
        observed_subject = subject()
        candidate = observation(observed_subject)
        pair = SubjectBoundObservedPriceEndpointPair(candidate, candidate)
        for value in (candidate, pair):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    pickle.dumps(value)

    def test_json_is_audit_only_and_reconstruction_is_untrusted(self) -> None:
        original_subject = subject()
        original_start = observation(original_subject, 100.0, "start")
        original_end = observation(original_subject, 120.0, "end")
        original = SubjectBoundObservedPriceEndpointPair(
            original_start,
            original_end,
        )
        audit_record = json.loads(json.dumps(asdict(original)))
        self.assertIsInstance(audit_record, dict)
        self.assertEqual(100.0, audit_record["proposed_start"]["price"])
        with self.assertRaises(TypeError):
            SubjectBoundObservedPriceEndpointPair(**audit_record)
        self.assert_no_certification_authority(audit_record)

        subject_record = audit_record["proposed_start"]["subject"]
        rehydrated_subject = AnalyzedWaveSubject(**subject_record)
        rehydrated_start = SubjectBoundObservedPriceObservation(
            subject=rehydrated_subject,
            price=audit_record["proposed_start"]["price"],
            observation_provenance_ref=audit_record["proposed_start"][
                "observation_provenance_ref"
            ],
        )
        rehydrated_end = SubjectBoundObservedPriceObservation(
            subject=rehydrated_subject,
            price=audit_record["proposed_end"]["price"],
            observation_provenance_ref=audit_record["proposed_end"][
                "observation_provenance_ref"
            ],
        )
        rehydrated = SubjectBoundObservedPriceEndpointPair(
            rehydrated_start,
            rehydrated_end,
        )
        self.assertIsNot(original, rehydrated)
        self.assertIsNot(original.subject, rehydrated.subject)
        self.assertIsNot(original.proposed_start, rehydrated.proposed_start)
        self.assert_no_certification_authority(rehydrated)

    def test_contract_has_no_arithmetic_or_methodology_outputs(self) -> None:
        observed_subject = subject()
        candidate = observation(observed_subject)
        pair = SubjectBoundObservedPriceEndpointPair(candidate, candidate)
        forbidden = (
            "length",
            "span",
            "delta",
            "distance",
            "change",
            "return",
            "ratio",
            "direction",
            "overlap",
            "pivot",
            "extreme",
            "orthodox_end",
            "timeframe",
            "degree",
            "completion",
            "family",
            "family_kind",
            "pattern",
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
            "certify",
            "issue",
            "register",
        )
        for value in (candidate, pair):
            for name in forbidden:
                self.assertFalse(hasattr(value, name), name)

    def test_contract_is_not_a_validator_result_or_certificate(self) -> None:
        observed_subject = subject()
        candidate = observation(observed_subject)
        pair = SubjectBoundObservedPriceEndpointPair(candidate, candidate)
        for value in (candidate, pair):
            self.assertNotIsInstance(value, structural_private.StructuralValidatorResult)
            self.assertNotIsInstance(value, family_private.InternalFamilyValidatorResult)
            self.assertNotIsInstance(
                value,
                structural_private.CertifiedStructuralInvalidity,
            )
            self.assertNotIsInstance(
                value,
                family_private.CertifiedValidatedInternalFamily,
            )
            self.assert_no_certification_authority(value)

    def test_public_exports_are_exact_and_non_certifying(self) -> None:
        expected = [
            "SubjectBoundObservedPriceObservation",
            "SubjectBoundObservedPriceEndpointPair",
        ]
        self.assertEqual(expected, price_binding_module.__all__)
        for name in expected:
            self.assertIn(name, public_contracts.__all__)
            self.assertIn(name, kernel.__all__)
            self.assertIs(
                getattr(price_binding_module, name),
                getattr(public_contracts, name),
            )
            self.assertIs(getattr(price_binding_module, name), getattr(kernel, name))
        for forbidden in (
            "calculate_length",
            "calculate_span",
            "validate_endpoint_pair",
            "certify_endpoint_pair",
            "register_endpoint_pair",
            "EndpointPairCertificate",
        ):
            self.assertFalse(hasattr(price_binding_module, forbidden))

    def test_module_ast_has_no_market_arithmetic_or_external_dependency(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "observed_price_binding.py"
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
            {"__future__", "dataclasses", "math", ".subject_binding"},
            imported_modules,
        )
        forbidden_operators = (
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                self.assertNotIsInstance(node.op, forbidden_operators)
            if isinstance(node, ast.Compare):
                for operator in node.ops:
                    self.assertNotIsInstance(operator, forbidden_operators)
        for forbidden in (
            "P004",
            "P005",
            "P006",
            "P010",
            "StructuralValidity",
            "InternalFamilyKind",
            "elliott_runtime",
            "TradingView",
            "provider",
            "ranking",
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

    def test_protected_foundation_and_runtime_files_are_unchanged(self) -> None:
        expected = {
            support.SRC / "elliott_methodology_kernel" / "subject_binding.py": (
                3441,
                "063de9702dd3837dbc4d1de3efa5633481eb6834991f066d418d042fe119f4aa",
            ),
            support.SRC
            / "elliott_methodology_kernel"
            / "normal_impulse_five_slot_view.py": (
                3459,
                "8e401d2eb0f1b683ebfc9845f3a1f16f1a75bd125ef1825b0274ee68f63d31fa",
            ),
            support.RUNTIME_ROOT / "tests" / "test_normal_impulse_five_slot_view.py": (
                19617,
                "a847b4334cc1e1b6e2dab4fcc45a8f43f488b70ba84f5f23c222f0729e2325af",
            ),
            support.SRC / "elliott_methodology_kernel" / "models.py": (
                5341,
                "3a724315d0c30dd54d404a3c0ae516945532366643039c8eb15d7e922d9ca56f",
            ),
            support.SRC / "elliott_runtime" / "market_data" / "ingestion.py": (
                6530,
                "f4f2319df74744444f98f96cbac7247ef675648ee6b68e995bd062d5a536aed4",
            ),
            support.SRC
            / "elliott_methodology_kernel"
            / "_structural_invalidity_certification.py": (
                20580,
                "b3f321a3e76f93ff37e995e9a1694a058fce68d0adbb20f6572ba2fc2082f615",
            ),
            support.SRC
            / "elliott_methodology_kernel"
            / "_validated_internal_family_certification.py": (
                29951,
                "88588fd60ec247d18c7f89ae4c8eda360f0b3f8d75272fe4d18a38a10201bdbc",
            ),
        }
        for path, (expected_bytes, expected_hash) in expected.items():
            payload = path.read_bytes()
            with self.subTest(path=str(path)):
                self.assertEqual(expected_bytes, len(payload))
                self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest())

    def test_family_registry_and_methodology_inventory_remain_unchanged(self) -> None:
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)
        family_private._seal_internal_family_validator_registry(
            expected_result_types=()
        )

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
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
                "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )
        self.assertEqual([], registration_calls)

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        source_text = inspect.getsource(kernel.MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertNotIn("SubjectBoundObservedPrice", source_text)


if __name__ == "__main__":
    unittest.main()
