import ast
import copy
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import StrEnum
import hashlib
import inspect
import json
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.contracts as public_contracts
from elliott_methodology_kernel import (
    CertifiedValidatedInternalFamily,
    InternalFamilyKind,
    InternalFamilyValidatorResult,
    ValidatedInternalFamilyCertificationError,
    certify_validated_internal_family,
)
from elliott_methodology_kernel.contracts import certify_structural_invalidity
from elliott_methodology_kernel.degree_peer_consistency import (
    DegreePeerConsistencyInput,
    check_degree_peer_consistency,
)
from elliott_methodology_kernel.models import (
    CountRank,
    CountRepresentation,
    DegreeStatus,
    DegreeTreeNode,
    ForecastContract,
    InternalStatus,
    RightLook,
    StructuralValidity,
)
from elliott_methodology_kernel.p003_one_larger_degree_theme import (
    P003OneLargerDegreeThemeInput,
    P003SearchTheme,
    map_p003_one_larger_degree_theme,
)
from elliott_methodology_kernel.p004 import (
    CandidateScope,
    ImpulseDirection,
    P004Input,
    check_p004,
)
from elliott_methodology_kernel.p023_visibility_guard import (
    P023VisibilityInput,
    P023VisibilityState,
    check_p023_visibility_guard,
)
from elliott_methodology_kernel.parent_child_degree_adjacency import (
    ParentChildDegreeInput,
    check_parent_child_degree_adjacency,
)


def p003_result(relation: str = "WITH"):
    return map_p003_one_larger_degree_theme(
        P003OneLargerDegreeThemeInput(relation)
    )


def p004_result(*, violated: bool = False):
    return check_p004(
        P004Input(
            candidate_scope=CandidateScope.NORMAL_IMPULSE,
            direction=ImpulseDirection.UP,
            wave1_origin=100.0,
            wave2_retracement_extreme=99.0 if violated else 101.0,
        )
    )


def degree_peer_result():
    return check_degree_peer_consistency(
        DegreePeerConsistencyInput(
            parent_node_id="parent",
            direct_child_degrees=(
                DegreeTreeNode(
                    label="one",
                    degree="Minor",
                    degree_status=DegreeStatus.RESOLVED,
                    internal_status=InternalStatus.UNRESOLVED,
                    parent_label="parent",
                ),
                DegreeTreeNode(
                    label="two",
                    degree="Minute",
                    degree_status=DegreeStatus.RESOLVED,
                    internal_status=InternalStatus.UNRESOLVED,
                    parent_label="parent",
                ),
            ),
        )
    )


def parent_child_result():
    return check_parent_child_degree_adjacency(
        ParentChildDegreeInput(
            parent_degree="Primary",
            parent_degree_status=DegreeStatus.RESOLVED,
            child_degree="Minor",
            child_degree_status=DegreeStatus.RESOLVED,
        )
    )


def p023_result():
    return check_p023_visibility_guard(
        P023VisibilityInput(P023VisibilityState.VISIBLE)
    )


def count_representation() -> CountRepresentation:
    return CountRepresentation(
        rank=CountRank.PREFERRED,
        pattern="caller-label-only",
        current_position="UNRESOLVED",
        structural_validity=StructuralValidity.UNRESOLVED,
        internal_status=InternalStatus.UNRESOLVED,
        right_look=RightLook.UNRESOLVED,
        forecast=ForecastContract(
            expected_next_structure="UNRESOLVED",
            confirmation="UNRESOLVED",
            downgrade_condition="UNRESOLVED",
            structural_invalidation="UNRESOLVED",
            alternative_promotion_trigger="UNRESOLVED",
        ),
    )


class ValidatedInternalFamilyFoundationTests(unittest.TestCase):
    def assert_not_proof(self, value: object) -> None:
        with self.assertRaises(ValidatedInternalFamilyCertificationError):
            certify_validated_internal_family(value)

    def test_family_vocabulary_is_exact_and_has_no_aliases(self) -> None:
        self.assertEqual(
            {
                "MOTIVE_FIVE_WAVE_FAMILY",
                "CORRECTIVE_THREE_WAVE_FAMILY",
            },
            {member.value for member in InternalFamilyKind},
        )
        self.assertEqual(2, len(InternalFamilyKind.__members__))
        for forbidden in (
            "OTHER",
            "UNKNOWN",
            "IMPULSE",
            "ZIGZAG",
            "FLAT",
            "TRIANGLE",
            "DIAGONAL",
        ):
            self.assertFalse(hasattr(InternalFamilyKind, forbidden))

    def test_registry_is_exactly_empty_and_sealed(self) -> None:
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)
        self.assertIs(True, family_private._REGISTRY_SEALED)
        family_private._seal_internal_family_validator_registry(
            expected_result_types=()
        )
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertIs(True, family_private._REGISTRY_SEALED)

    def test_late_registration_is_rejected_without_creating_a_producer(self) -> None:
        class LateStatus(StrEnum):
            VALIDATED = "VALIDATED"

        class LateRole(StrEnum):
            STRUCTURAL_VALIDATION = "STRUCTURAL_VALIDATION"

        class LateSubject:
            pass

        @dataclass(frozen=True, slots=True, weakref_slot=True)
        class UnregisteredResult(InternalFamilyValidatorResult):
            status: LateStatus
            execution_role: LateRole
            behavior_id: str
            outcome: str
            reason: str

        def source_extractor(origin):
            raise AssertionError("sealed registration must not invoke callbacks")

        def source_verifier(origin, provenance):
            raise AssertionError("sealed registration must not invoke callbacks")

        def subject_extractor(origin):
            raise AssertionError("sealed registration must not invoke callbacks")

        def subject_verifier(origin, binding):
            raise AssertionError("sealed registration must not invoke callbacks")

        for _ in range(2):
            with self.assertRaisesRegex(
                ValidatedInternalFamilyCertificationError, "registry is sealed"
            ):
                family_private._register_internal_family_validator(
                    UnregisteredResult,
                    success_statuses=(LateStatus.VALIDATED,),
                    family_kind=InternalFamilyKind.MOTIVE_FIVE_WAVE_FAMILY,
                    execution_role=LateRole.STRUCTURAL_VALIDATION,
                    behavior_id="UNREGISTERED_TEST_ONLY",
                    subject_type=LateSubject,
                    source_provenance_extractor=source_extractor,
                    source_provenance_verifier=source_verifier,
                    subject_binding_extractor=subject_extractor,
                    subject_provenance_verifier=subject_verifier,
                )
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)

    def test_duplicate_and_unexpected_expected_inventory_are_rejected(self) -> None:
        @dataclass(frozen=True, slots=True, weakref_slot=True)
        class UnregisteredResult(InternalFamilyValidatorResult):
            marker: str = "not-a-producer"

        with self.assertRaisesRegex(
            ValidatedInternalFamilyCertificationError, "incomplete or unexpected"
        ):
            family_private._seal_internal_family_validator_registry(
                expected_result_types=(UnregisteredResult,)
            )
        with self.assertRaisesRegex(
            ValidatedInternalFamilyCertificationError, "must be unique"
        ):
            family_private._seal_internal_family_validator_registry(
                expected_result_types=(UnregisteredResult, UnregisteredResult)
            )
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertIs(True, family_private._REGISTRY_SEALED)

    def test_certificate_is_frozen_slotted_guarded_and_not_serializable(self) -> None:
        self.assertTrue(is_dataclass(CertifiedValidatedInternalFamily))
        self.assertTrue(CertifiedValidatedInternalFamily.__dataclass_params__.frozen)
        self.assertEqual(
            {"_origin", "_attestation"},
            {field.name for field in fields(CertifiedValidatedInternalFamily)},
        )
        with self.assertRaises(TypeError):
            CertifiedValidatedInternalFamily()
        with self.assertRaises(TypeError):
            CertifiedValidatedInternalFamily("origin")
        with self.assertRaises(TypeError):
            CertifiedValidatedInternalFamily(origin="origin")

        malformed = object.__new__(CertifiedValidatedInternalFamily)
        self.assertFalse(hasattr(malformed, "__dict__"))
        for operation in (
            lambda: malformed.origin,
            lambda: malformed.family_kind,
            lambda: repr(malformed),
            lambda: copy.copy(malformed),
            lambda: copy.deepcopy(malformed),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(ValidatedInternalFamilyCertificationError):
                    operation()
        with self.assertRaises(TypeError):
            pickle.dumps(malformed)

    def test_raw_strings_and_family_enum_values_are_not_proof(self) -> None:
        for value in (
            "MOTIVE_FIVE_WAVE_FAMILY",
            "CORRECTIVE_THREE_WAVE_FAMILY",
            InternalFamilyKind.MOTIVE_FIVE_WAVE_FAMILY,
            InternalFamilyKind.CORRECTIVE_THREE_WAVE_FAMILY,
        ):
            with self.subTest(value=value):
                self.assert_not_proof(value)

    def test_p003_themes_and_complete_results_are_not_proof(self) -> None:
        for value in (
            P003SearchTheme.MOTIVE,
            P003SearchTheme.CORRECTIVE,
            p003_result("WITH"),
            p003_result("AGAINST"),
        ):
            with self.subTest(value=value):
                self.assert_not_proof(value)

    def test_internal_status_and_count_representation_are_not_proof(self) -> None:
        for value in (*tuple(InternalStatus), count_representation()):
            with self.subTest(value=value):
                self.assert_not_proof(value)

    def test_all_existing_methodology_results_are_not_family_proof(self) -> None:
        for result in (
            p004_result(),
            p004_result(violated=True),
            degree_peer_result(),
            parent_child_result(),
            p023_result(),
        ):
            with self.subTest(result=type(result).__name__):
                self.assert_not_proof(result)

    def test_genuine_structural_invalidity_certificate_is_not_family_proof(self) -> None:
        origin = p004_result(violated=True)
        certificate = certify_structural_invalidity(origin)
        self.assertIs(origin, certificate.origin)
        self.assert_not_proof(certificate)

    def test_mapping_and_json_rehydrated_lookalikes_are_not_proof(self) -> None:
        payload = {
            "family_kind": "MOTIVE_FIVE_WAVE_FAMILY",
            "origin": {"behavior_id": "CALLER_LABEL"},
            "subject": "caller-subject",
            "status": "VALIDATED",
            "protected_sources": ["caller-source"],
        }
        self.assert_not_proof(payload)
        self.assert_not_proof(json.loads(json.dumps(payload)))

    def test_duck_marker_and_certificate_subclasses_are_not_proof(self) -> None:
        class HostileDuck:
            @property
            def family_kind(self):
                raise AssertionError("empty registry must reject before field access")

        class UnregisteredMarker(InternalFamilyValidatorResult):
            pass

        class CertificateSubclass(CertifiedValidatedInternalFamily):
            pass

        for value in (
            HostileDuck(),
            InternalFamilyValidatorResult(),
            UnregisteredMarker(),
            object.__new__(CertificateSubclass),
        ):
            with self.subTest(value=type(value).__name__):
                self.assert_not_proof(value)

    def test_copy_deepcopy_and_dataclass_replace_cannot_gain_authority(self) -> None:
        raw_results = (p003_result(), p004_result(), p023_result())
        for raw in raw_results:
            variants = (copy.copy(raw), copy.deepcopy(raw), replace(raw))
            for variant in variants:
                with self.subTest(result=type(raw).__name__, variant=variant):
                    self.assert_not_proof(variant)

    def test_public_api_is_exact_and_certifier_accepts_only_origin(self) -> None:
        public_names = {
            "CertifiedValidatedInternalFamily",
            "InternalFamilyKind",
            "InternalFamilyValidatorResult",
            "ValidatedInternalFamilyCertificationError",
            "certify_validated_internal_family",
        }
        self.assertTrue(public_names.issubset(set(public_contracts.__all__)))
        self.assertTrue(public_names.issubset(set(kernel.__all__)))
        for name in public_names:
            self.assertIs(getattr(public_contracts, name), getattr(kernel, name))
        self.assertEqual(
            ("origin",),
            tuple(inspect.signature(certify_validated_internal_family).parameters),
        )

    def test_private_authority_is_absent_from_public_surfaces(self) -> None:
        private_names = (
            "_ProducerSpec",
            "_ProducerIssuer",
            "_OriginAttestation",
            "_SourceProvenanceView",
            "_SubjectBindingView",
            "_PRODUCERS",
            "_ISSUED",
            "_register_internal_family_validator",
            "_seal_internal_family_validator_registry",
            "_issue_validated_internal_family",
            "_new_certificate",
        )
        for name in private_names:
            self.assertNotIn(name, public_contracts.__all__)
            self.assertNotIn(name, kernel.__all__)
            self.assertFalse(hasattr(public_contracts, name))
            self.assertFalse(hasattr(kernel, name))
        for public_prefix in ("register_", "issue_", "seal_"):
            self.assertFalse(
                any(name.startswith(public_prefix) for name in public_contracts.__all__)
            )

    def test_mutable_runtime_has_no_private_family_authority_import(self) -> None:
        forbidden = (
            "_validated_internal_family_certification",
            "_register_internal_family_validator",
            "_ProducerIssuer",
            "_seal_internal_family_validator_registry",
            "_issue_validated_internal_family",
        )
        references = []
        for path in (support.SRC / "elliott_runtime").rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                if token in source:
                    references.append((str(path), token))
        self.assertEqual([], references)

    def test_structural_invalidity_contract_is_byte_exact_and_operational(self) -> None:
        contract_path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "_structural_invalidity_certification.py"
        )
        contract_bytes = contract_path.read_bytes()
        self.assertEqual(20580, len(contract_bytes))
        self.assertEqual(
            "b3f321a3e76f93ff37e995e9a1694a058fce68d0adbb20f6572ba2fc2082f615",
            hashlib.sha256(contract_bytes).hexdigest(),
        )
        structural_test = (
            support.RUNTIME_ROOT / "tests" / "test_structural_invalidity_contract.py"
        )
        test_bytes = structural_test.read_bytes()
        self.assertEqual(33043, len(test_bytes))
        self.assertEqual(
            "4da83bdd2973c65353c72306aec1d95fa92410d973a2539f3db44a548f025157",
            hashlib.sha256(test_bytes).hexdigest(),
        )
        self.assertIs(True, structural_private._REGISTRY_SEALED)
        self.assertEqual(6, len(structural_private._PRODUCERS))
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            },
            {spec.behavior_id for spec in structural_private._PRODUCERS.values()},
        )
        origin = p004_result(violated=True)
        self.assertIs(origin, certify_structural_invalidity(origin).origin)

    def test_executable_methodology_inventory_remains_exactly_nine(self) -> None:
        observed = set()
        special_names = {"NO_RESCUE_BEHAVIOR", "P003_BEHAVIOR"}
        kernel_root = support.SRC / "elliott_methodology_kernel"
        for path in kernel_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
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
        self.assertEqual({}, family_private._PRODUCERS)
        for path in kernel_root.glob("*.py"):
            self.assertNotIn("P010_", path.read_text(encoding="utf-8"))

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        source = inspect.getsource(kernel.MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source)
        self.assertNotIn("certify_validated_internal_family", source)

    def test_private_contract_has_no_methodology_or_external_capabilities(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "_validated_internal_family_certification.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add("." * node.level + (node.module or ""))
        allowed = {
            "__future__",
            "dataclasses",
            "enum",
            "hashlib",
            "json",
            "threading",
            "typing",
            "uuid",
            "weakref",
        }
        self.assertEqual(set(), imported_modules - allowed)
        for forbidden in (
            "elliott_runtime",
            "_structural_invalidity_certification",
            "P003SearchTheme",
            "InternalStatus",
            "CountRepresentation",
            "EvidenceState",
            "CountRank",
            "TradingView",
            "market_data",
            "candidate_generation",
            "ranking",
            "pivot",
            "OHLCV",
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
            self.assertNotIn(forbidden, source)
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"open", "exec", "eval", "__import__"}.isdisjoint(called_names))

    def test_future_subject_and_source_authority_is_private_and_dormant(self) -> None:
        spec_fields = {field.name for field in fields(family_private._ProducerSpec)}
        self.assertEqual(
            {
                "result_type",
                "success_statuses",
                "family_kind",
                "execution_role",
                "behavior_id",
                "subject_type",
                "source_provenance_extractor",
                "source_provenance_verifier",
                "subject_binding_extractor",
                "subject_provenance_verifier",
            },
            spec_fields,
        )
        self.assertTrue(family_private._ProducerSpec.__dataclass_params__.frozen)
        self.assertTrue(family_private._OriginAttestation.__dataclass_params__.frozen)
        source = inspect.getsource(family_private._read_origin_view)
        self.assertIn("family_kind=spec.family_kind", source)
        self.assertNotIn('"family_kind"', source)
        self.assertNotIn("origin.family", source)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual({}, family_private._ISSUED)

    def test_no_family_validator_or_positive_issuance_path_is_active(self) -> None:
        kernel_root = support.SRC / "elliott_methodology_kernel"
        marker_subclasses = []
        registration_calls = []
        for path in kernel_root.glob("*.py"):
            if path.name == "_validated_internal_family_certification.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "InternalFamilyValidatorResult":
                            marker_subclasses.append((str(path), node.name))
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_register_internal_family_validator"
                ):
                    registration_calls.append(str(path))
        self.assertEqual([], marker_subclasses)
        self.assertEqual([], registration_calls)
        for value in (
            None,
            object(),
            InternalFamilyValidatorResult,
            CertifiedValidatedInternalFamily,
        ):
            self.assert_not_proof(value)


if __name__ == "__main__":
    unittest.main()
