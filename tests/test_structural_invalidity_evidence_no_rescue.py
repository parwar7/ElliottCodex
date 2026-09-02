import ast
from dataclasses import FrozenInstanceError, fields
import hashlib
import inspect
import unittest

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as private_contract
from elliott_methodology_kernel import (
    CandidateScope,
    CertifiedStructuralInvalidity,
    DegreePeerConsistencyInput,
    ImpulseDirection,
    MethodologyKernel,
    P004Input,
    P023VisibilityInput,
    P023VisibilityState,
    ParentChildDegreeInput,
    StructuralInvalidityCertificationError,
    StructuralInvalidityEvidenceNoRescueExecutionRole,
    StructuralInvalidityEvidenceNoRescuePolicyStatus,
    StructuralInvalidityEvidenceNoRescueResult,
    StructuralValidatorResult,
    apply_structural_invalidity_evidence_no_rescue,
    certify_structural_invalidity,
    check_degree_peer_consistency,
    check_p004,
    check_p023_visibility_guard,
    check_parent_child_degree_adjacency,
)
from elliott_methodology_kernel.models import (
    DegreeStatus,
    DegreeTreeNode,
    InternalStatus,
    KernelStatus,
    SourceClassification,
    StructuralValidity,
)
from elliott_methodology_kernel.structural_invalidity_evidence_no_rescue import (
    NO_RESCUE_BEHAVIOR,
    NO_RESCUE_PROTECTED_SOURCES,
)


def p004_violation():
    return check_p004(
        P004Input(
            candidate_scope=CandidateScope.NORMAL_IMPULSE,
            direction=ImpulseDirection.UP,
            wave1_origin=100.0,
            wave2_retracement_extreme=99.0,
        )
    )


def degree_child(label: str, degree: str):
    return DegreeTreeNode(
        label=label,
        degree=degree,
        degree_status=DegreeStatus.RESOLVED,
        internal_status=InternalStatus.UNRESOLVED,
        parent_label="parent",
    )


def degree_peer_violation():
    return check_degree_peer_consistency(
        DegreePeerConsistencyInput(
            parent_node_id="parent",
            direct_child_degrees=(
                degree_child("1", "Minor"),
                degree_child("2", "Minute"),
            ),
        )
    )


def parent_child_violation():
    return check_parent_child_degree_adjacency(
        ParentChildDegreeInput(
            parent_degree="Primary",
            parent_degree_status=DegreeStatus.RESOLVED,
            child_degree="Minor",
            child_degree_status=DegreeStatus.RESOLVED,
        )
    )


def valid_certificates():
    return tuple(
        certify_structural_invalidity(origin)
        for origin in (
            p004_violation(),
            degree_peer_violation(),
            parent_child_violation(),
        )
    )


class StructuralInvalidityEvidenceNoRescueTests(unittest.TestCase):
    def assert_policy_rejected(self, value: object) -> None:
        with self.assertRaises(StructuralInvalidityCertificationError):
            apply_structural_invalidity_evidence_no_rescue(value)

    def test_all_three_approved_certified_origins_are_accepted(self) -> None:
        expected_origins = {
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
            "PARENT_CHILD_DEGREE_ADJACENCY",
        }
        observed_origins = set()
        for certificate in valid_certificates():
            result = apply_structural_invalidity_evidence_no_rescue(certificate)
            observed_origins.add(result.originating_invalidity.origin_behavior_id)
            self.assertIs(
                StructuralInvalidityEvidenceNoRescuePolicyStatus
                .EVIDENCE_OVERRIDE_PROHIBITED,
                result.policy_status,
            )
        self.assertEqual(expected_origins, observed_origins)

    def test_exact_certificate_and_original_result_identity_are_preserved(self) -> None:
        origin = p004_violation()
        certificate = certify_structural_invalidity(origin)
        result = apply_structural_invalidity_evidence_no_rescue(certificate)

        self.assertIs(certificate, result.originating_invalidity)
        self.assertIs(origin, result.originating_invalidity.origin)

    def test_policy_provenance_is_distinct_from_origin_provenance(self) -> None:
        certificate = certify_structural_invalidity(degree_peer_violation())
        origin_sources = certificate.origin_protected_sources
        result = apply_structural_invalidity_evidence_no_rescue(certificate)

        self.assertEqual(NO_RESCUE_BEHAVIOR, result.behavior_id)
        self.assertIsNone(result.source_principle_id)
        self.assertIs(SourceClassification.RULE, result.source_class)
        self.assertIs(
            StructuralInvalidityEvidenceNoRescueExecutionRole.HARD_VALIDATION,
            result.execution_role,
        )
        self.assertIs(NO_RESCUE_PROTECTED_SOURCES, result.protected_sources)
        self.assertIsNot(origin_sources, result.protected_sources)
        self.assertNotEqual(origin_sources, result.protected_sources)
        self.assertIs(SourceClassification.DEFINITION, certificate.origin_source_class)
        self.assertTrue(result.reason)

    def test_structural_validity_and_fatality_are_derived_from_certificate(self) -> None:
        for certificate in valid_certificates():
            result = apply_structural_invalidity_evidence_no_rescue(certificate)
            with self.subTest(origin=certificate.origin_behavior_id):
                self.assertIs(
                    certificate.structural_validity, result.structural_validity
                )
                self.assertIs(
                    certificate.fatal_to_candidate, result.fatal_to_candidate
                )
                self.assertIs(StructuralValidity.INVALID, result.structural_validity)
                self.assertIs(result.fatal_to_candidate, True)
                self.assertIs(result.evidence_override_allowed, False)

    def test_result_and_function_accept_no_independent_validity_or_fatality(self) -> None:
        certificate = valid_certificates()[0]
        self.assertEqual(
            ("originating_invalidity",),
            tuple(
                inspect.signature(
                    StructuralInvalidityEvidenceNoRescueResult
                ).parameters
            ),
        )
        with self.assertRaises(TypeError):
            StructuralInvalidityEvidenceNoRescueResult(
                certificate, fatal_to_candidate=False
            )
        with self.assertRaises(TypeError):
            StructuralInvalidityEvidenceNoRescueResult(
                certificate, structural_validity=StructuralValidity.VALID
            )

    def test_raw_structural_results_are_rejected(self) -> None:
        for raw_origin in (
            p004_violation(),
            degree_peer_violation(),
            parent_child_violation(),
        ):
            with self.subTest(origin=raw_origin.behavior_id):
                self.assert_policy_rejected(raw_origin)

    def test_p023_mapping_duck_and_wrong_types_are_rejected(self) -> None:
        p023 = check_p023_visibility_guard(
            P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        )

        class DuckCertificate:
            origin = p004_violation()
            structural_validity = StructuralValidity.INVALID
            fatal_to_candidate = True

        for value in (
            p023,
            {"origin": p004_violation(), "fatal_to_candidate": True},
            DuckCertificate(),
            object(),
            None,
            "CertifiedStructuralInvalidity",
        ):
            with self.subTest(value_type=type(value).__name__):
                self.assert_policy_rejected(value)

    def test_malformed_and_subclassed_certificates_are_rejected(self) -> None:
        malformed = object.__new__(CertifiedStructuralInvalidity)

        class CertificateSubclass(CertifiedStructuralInvalidity):
            __slots__ = ()

        subclassed = object.__new__(CertificateSubclass)
        for value in (malformed, subclassed):
            with self.subTest(value_type=type(value).__name__):
                self.assert_policy_rejected(value)

    def test_low_level_origin_mutation_fails_closed_for_apply_and_existing_result(self) -> None:
        origin = p004_violation()
        certificate = certify_structural_invalidity(origin)
        result = apply_structural_invalidity_evidence_no_rescue(certificate)
        object.__setattr__(origin, "reason", "tampered after certification")

        with self.assertRaises(StructuralInvalidityCertificationError):
            apply_structural_invalidity_evidence_no_rescue(certificate)

        accessors = (
            lambda: result.policy_status,
            lambda: result.behavior_id,
            lambda: result.source_principle_id,
            lambda: result.source_class,
            lambda: result.execution_role,
            lambda: result.protected_sources,
            lambda: result.reason,
            lambda: result.originating_invalidity,
            lambda: result.structural_validity,
            lambda: result.fatal_to_candidate,
            lambda: result.evidence_override_allowed,
            lambda: repr(result),
        )
        for accessor in accessors:
            with self.subTest(accessor=accessor):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    accessor()

    def test_function_uses_exact_one_argument_python_signature(self) -> None:
        function = apply_structural_invalidity_evidence_no_rescue
        certificate = valid_certificates()[0]
        self.assertEqual(
            ("originating_invalidity",),
            tuple(inspect.signature(function).parameters),
        )
        with self.assertRaises(TypeError):
            function()
        with self.assertRaises(TypeError):
            function(certificate, certificate)
        with self.assertRaises(TypeError):
            function(certificate, unexpected=True)
        with self.assertRaises(TypeError):
            function(certificate, evidence_state="SUPPORTS")

    def test_policy_result_is_frozen_slotted_and_provenance_is_immutable(self) -> None:
        result = apply_structural_invalidity_evidence_no_rescue(
            valid_certificates()[0]
        )
        self.assertEqual(
            ("_originating_invalidity",),
            tuple(field.name for field in fields(result)),
        )
        self.assertFalse(hasattr(result, "__dict__"))
        replacements = {
            "policy_status": "REWRITTEN",
            "behavior_id": "REWRITTEN",
            "source_principle_id": "P999",
            "source_class": SourceClassification.OBSERVATION,
            "execution_role": "REWRITTEN",
            "protected_sources": ("rewritten",),
            "reason": "rewritten",
            "originating_invalidity": valid_certificates()[1],
            "structural_validity": StructuralValidity.VALID,
            "fatal_to_candidate": False,
            "evidence_override_allowed": True,
        }
        for attribute, replacement in replacements.items():
            with self.subTest(attribute=attribute):
                with self.assertRaises(
                    (FrozenInstanceError, AttributeError, TypeError)
                ):
                    setattr(result, attribute, replacement)

    def test_policy_result_is_not_a_structural_origin_and_cannot_certify(self) -> None:
        result = apply_structural_invalidity_evidence_no_rescue(
            valid_certificates()[0]
        )
        self.assertNotIsInstance(result, StructuralValidatorResult)
        self.assertNotIn(type(result), private_contract._PRODUCERS)
        self.assertNotIn(result.behavior_id, private_contract._BEHAVIOR_IDS)
        with self.assertRaises(StructuralInvalidityCertificationError):
            certify_structural_invalidity(result)

    def test_public_exports_are_behavior_local_and_complete(self) -> None:
        expected = {
            "StructuralInvalidityEvidenceNoRescueExecutionRole",
            "StructuralInvalidityEvidenceNoRescuePolicyStatus",
            "StructuralInvalidityEvidenceNoRescueResult",
            "apply_structural_invalidity_evidence_no_rescue",
        }
        self.assertTrue(expected.issubset(set(kernel.__all__)))
        for name in expected:
            self.assertTrue(hasattr(kernel, name))

    def test_module_has_no_forbidden_dependency_or_evidence_calculation(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "structural_invalidity_evidence_no_rescue.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add("." * node.level + (node.module or ""))
        self.assertEqual(
            {"__future__", "dataclasses", "enum", "typing", ".contracts"},
            imported_modules,
        )
        forbidden = (
            "EvidenceState",
            "CountRank",
            "Fibonacci",
            "volume",
            "breadth",
            "sentiment",
            "psychology",
            "fundamentals",
            "channeling",
            "right_look",
            "evidence_score",
            "evidence_weight",
            "confidence",
            "check_p004",
            "check_degree_peer_consistency",
            "check_parent_child_degree_adjacency",
            "check_p023_visibility_guard",
            "elliott_runtime",
            "provider",
            "TradingView",
            "orchestration",
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
            "_structural_invalidity_certification",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)
        self.assertFalse(any(isinstance(node, ast.BinOp) for node in ast.walk(tree)))

    def test_no_downstream_runtime_or_orchestration_wiring_exists(self) -> None:
        behavior_name = "structural_invalidity_evidence_no_rescue"
        runtime_root = support.SRC / "elliott_runtime"
        references = []
        for path in runtime_root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if behavior_name in source or NO_RESCUE_BEHAVIOR in source:
                references.append(str(path))
        self.assertEqual([], references)

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        source = inspect.getsource(MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source)
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, kernel.KernelStatus.NOT_IMPLEMENTED)

    def test_executable_methodology_inventory_is_exactly_five(self) -> None:
        policy = apply_structural_invalidity_evidence_no_rescue(
            valid_certificates()[0]
        )
        observed = {
            p004_violation().behavior_id,
            degree_peer_violation().behavior_id,
            parent_child_violation().behavior_id,
            check_p023_visibility_guard(
                P023VisibilityInput(P023VisibilityState.VISIBLE)
            ).behavior_id,
            policy.behavior_id,
        }
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P023_INTERNAL_VISIBILITY_GUARD",
                "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
            },
            observed,
        )

    def test_shared_contract_files_remain_at_approved_baseline_hashes(self) -> None:
        expected = {
            "_structural_invalidity_certification.py": (
                20580,
                "b3f321a3e76f93ff37e995e9a1694a058fce68d0adbb20f6572ba2fc2082f615",
            ),
            "contracts.py": (
                2551,
                "9e6537102992e725cc999542c90bba28f23b117612d6191e21d599b4f455c237",
            ),
        }
        kernel_root = support.SRC / "elliott_methodology_kernel"
        for filename, (expected_bytes, expected_hash) in expected.items():
            payload = (kernel_root / filename).read_bytes()
            with self.subTest(filename=filename):
                self.assertEqual(expected_bytes, len(payload))
                self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest())

    def test_runtime_policy_vocabulary_is_explicitly_documented_as_runtime_only(self) -> None:
        module = inspect.getmodule(
            apply_structural_invalidity_evidence_no_rescue
        )
        self.assertIsNotNone(module)
        self.assertIn("Runtime policy vocabulary", module.__doc__)
        self.assertEqual(
            "EVIDENCE_OVERRIDE_PROHIBITED",
            StructuralInvalidityEvidenceNoRescuePolicyStatus
            .EVIDENCE_OVERRIDE_PROHIBITED.value,
        )


if __name__ == "__main__":
    unittest.main()
