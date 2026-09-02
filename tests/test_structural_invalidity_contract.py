import ast
import copy
from dataclasses import FrozenInstanceError, asdict, dataclass, fields, replace
import gc
import inspect
import json
from pathlib import Path
import pickle
import unittest
from unittest import mock
import weakref

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as private_contract
import elliott_methodology_kernel.contracts as public_contracts
from elliott_methodology_kernel import (
    CandidateScope,
    CertifiedStructuralInvalidity,
    DegreePeerCheckStatus,
    DegreePeerConsistencyInput,
    DegreePeerConsistencyResult,
    DegreePeerExecutionRole,
    ExecutionRole,
    ImpulseDirection,
    P004Input,
    P004Result,
    P023VisibilityInput,
    P023VisibilityState,
    ParentChildDegreeCheckStatus,
    ParentChildDegreeExecutionRole,
    ParentChildDegreeInput,
    ParentChildDegreeResult,
    RuleCheckStatus,
    StructuralInvalidityCertificationError,
    StructuralValidatorResult,
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
    SourceClassification,
    StructuralValidity,
)


def p004_result(*, violated: bool = True) -> P004Result:
    return check_p004(
        P004Input(
            candidate_scope=CandidateScope.NORMAL_IMPULSE,
            direction=ImpulseDirection.UP,
            wave1_origin=100.0,
            wave2_retracement_extreme=99.0 if violated else 101.0,
        )
    )


def degree_child(label: str, degree: str | None, *, resolved: bool = True):
    return DegreeTreeNode(
        label=label,
        degree=degree,
        degree_status=DegreeStatus.RESOLVED if resolved else DegreeStatus.UNRESOLVED,
        internal_status=InternalStatus.UNRESOLVED,
        parent_label="parent",
    )


def degree_peer_result(*, violated: bool = True) -> DegreePeerConsistencyResult:
    return check_degree_peer_consistency(
        DegreePeerConsistencyInput(
            parent_node_id="parent",
            direct_child_degrees=(
                degree_child("1", "Minor"),
                degree_child("2", "Minute" if violated else "Minor"),
            ),
        )
    )


def parent_child_result(*, violated: bool = True) -> ParentChildDegreeResult:
    return check_parent_child_degree_adjacency(
        ParentChildDegreeInput(
            parent_degree="Primary",
            parent_degree_status=DegreeStatus.RESOLVED,
            child_degree="Minor" if violated else "Intermediate",
            child_degree_status=DegreeStatus.RESOLVED,
        )
    )


def exact_manual_copy(result):
    return type(result)(
        **{field.name: getattr(result, field.name) for field in fields(result)}
    )


def read_certificate_through_public_contract(certificate):
    """A consumer using only the public certificate surface."""
    return (
        certificate.origin,
        certificate.origin_id,
        certificate.origin_behavior_id,
        certificate.origin_principle_id,
        certificate.origin_source_class,
        certificate.origin_execution_role,
        certificate.origin_status,
        certificate.origin_outcome,
        certificate.origin_reason,
        certificate.origin_protected_sources,
        certificate.fatal_to_candidate,
        certificate.structural_validity,
    )


class StructuralInvalidityCertificationTests(unittest.TestCase):
    def assert_rejected(self, origin: object) -> None:
        with self.assertRaises(StructuralInvalidityCertificationError):
            certify_structural_invalidity(origin)

    def test_p004_fatal_violation_certifies_with_exact_origin(self) -> None:
        origin = p004_result(violated=True)
        certificate = certify_structural_invalidity(origin)

        self.assertIs(origin, certificate.origin)
        self.assertEqual("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", certificate.origin_behavior_id)
        self.assertEqual("P004", certificate.origin_principle_id)
        self.assertIs(SourceClassification.RULE, certificate.origin_source_class)
        self.assertIs(ExecutionRole.HARD_VALIDATION, certificate.origin_execution_role)
        self.assertIs(RuleCheckStatus.RULE_VIOLATED, certificate.origin_status)
        self.assertEqual(origin.outcome, certificate.origin_outcome)
        self.assertEqual(origin.reason, certificate.origin_reason)
        self.assertIs(origin.protected_sources, certificate.origin_protected_sources)
        self.assertIs(certificate.fatal_to_candidate, True)
        self.assertIs(StructuralValidity.INVALID, certificate.structural_validity)

    def test_p004_satisfied_and_unresolved_results_are_rejected(self) -> None:
        satisfied = p004_result(violated=False)
        missing = check_p004(
            P004Input(
                candidate_scope=CandidateScope.NORMAL_IMPULSE,
                direction=ImpulseDirection.UP,
                wave1_origin=None,
                wave2_retracement_extreme=101.0,
            )
        )
        unsupported = check_p004(
            P004Input(
                candidate_scope="DIAGONAL",
                direction=ImpulseDirection.UP,
                wave1_origin=100.0,
                wave2_retracement_extreme=101.0,
            )
        )
        for result in (satisfied, missing, unsupported):
            with self.subTest(status=result.status):
                self.assert_rejected(result)

    def test_degree_peer_fatal_violation_certifies(self) -> None:
        origin = degree_peer_result(violated=True)
        certificate = certify_structural_invalidity(origin)

        self.assertIs(origin, certificate.origin)
        self.assertEqual(
            "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
            certificate.origin_behavior_id,
        )
        self.assertIsNone(certificate.origin_principle_id)
        self.assertIs(SourceClassification.DEFINITION, certificate.origin_source_class)
        self.assertIs(
            DegreePeerExecutionRole.HARD_VALIDATION,
            certificate.origin_execution_role,
        )
        self.assertIs(DegreePeerCheckStatus.RULE_VIOLATED, certificate.origin_status)
        self.assertIs(certificate.fatal_to_candidate, True)

    def test_degree_peer_satisfied_and_unresolved_results_are_rejected(self) -> None:
        satisfied = degree_peer_result(violated=False)
        missing = check_degree_peer_consistency(
            DegreePeerConsistencyInput(
                parent_node_id="parent",
                direct_child_degrees=(
                    degree_child("1", "Minor"),
                    degree_child("2", None, resolved=False),
                ),
            )
        )
        insufficient = check_degree_peer_consistency(
            DegreePeerConsistencyInput(
                parent_node_id="parent", direct_child_degrees=()
            )
        )
        for result in (satisfied, missing, insufficient):
            with self.subTest(status=result.status):
                self.assert_rejected(result)

    def test_parent_child_fatal_violation_certifies(self) -> None:
        origin = parent_child_result(violated=True)
        certificate = certify_structural_invalidity(origin)

        self.assertIs(origin, certificate.origin)
        self.assertEqual(
            "PARENT_CHILD_DEGREE_ADJACENCY", certificate.origin_behavior_id
        )
        self.assertIsNone(certificate.origin_principle_id)
        self.assertIs(SourceClassification.DEFINITION, certificate.origin_source_class)
        self.assertIs(
            ParentChildDegreeExecutionRole.HARD_VALIDATION,
            certificate.origin_execution_role,
        )
        self.assertIs(
            ParentChildDegreeCheckStatus.RULE_VIOLATED, certificate.origin_status
        )
        self.assertIs(certificate.fatal_to_candidate, True)

    def test_parent_child_satisfied_and_every_unresolved_family_are_rejected(self) -> None:
        satisfied = parent_child_result(violated=False)
        missing = check_parent_child_degree_adjacency(
            ParentChildDegreeInput(
                parent_degree="Primary",
                parent_degree_status=DegreeStatus.UNRESOLVED,
                child_degree="Intermediate",
                child_degree_status=DegreeStatus.RESOLVED,
            )
        )
        unknown = check_parent_child_degree_adjacency(
            ParentChildDegreeInput(
                parent_degree="UNKNOWN",
                parent_degree_status=DegreeStatus.RESOLVED,
                child_degree="Intermediate",
                child_degree_status=DegreeStatus.RESOLVED,
            )
        )
        no_subordinate = check_parent_child_degree_adjacency(
            ParentChildDegreeInput(
                parent_degree="Subminuette",
                parent_degree_status=DegreeStatus.RESOLVED,
                child_degree="Subminuette",
                child_degree_status=DegreeStatus.RESOLVED,
            )
        )
        self.assertEqual(
            {
                ParentChildDegreeCheckStatus.RULE_SATISFIED,
                ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT,
                ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE,
                ParentChildDegreeCheckStatus.UNRESOLVED_NO_DEFINED_SUBORDINATE,
            },
            {result.status for result in (satisfied, missing, unknown, no_subordinate)},
        )
        for result in (satisfied, missing, unknown, no_subordinate):
            with self.subTest(status=result.status):
                self.assert_rejected(result)

    def test_every_p023_result_is_rejected(self) -> None:
        results = (
            check_p023_visibility_guard(P023VisibilityInput(P023VisibilityState.VISIBLE)),
            check_p023_visibility_guard(
                P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
            ),
            check_p023_visibility_guard(P023VisibilityInput(P023VisibilityState.UNKNOWN)),
            check_p023_visibility_guard(P023VisibilityInput()),
            check_p023_visibility_guard(P023VisibilityInput("MALFORMED")),
        )
        for result in results:
            with self.subTest(status=result.status, reason=result.reason):
                self.assertIs(result.fatal_to_candidate, False)
                self.assert_rejected(result)

    def test_duck_typed_and_nominal_unregistered_fakes_are_rejected_without_access(self) -> None:
        genuine = p004_result()

        class CompleteDuck:
            status = genuine.status
            principle_id = genuine.principle_id
            source_class = genuine.source_class
            execution_role = genuine.execution_role
            protected_sources = genuine.protected_sources
            behavior_id = genuine.behavior_id
            outcome = genuine.outcome
            reason = genuine.reason
            fatal_to_candidate = genuine.fatal_to_candidate

        class HostileFake(StructuralValidatorResult):
            __slots__ = ()

            def __getattribute__(self, name):
                raise AssertionError(f"unexpected field access: {name}")

            def __eq__(self, other):
                raise AssertionError("unexpected equality")

        self.assert_rejected(CompleteDuck())
        self.assert_rejected(HostileFake())

    def test_invalid_looking_nonfatal_and_fatal_nonviolation_fakes_are_rejected(self) -> None:
        class InvalidLooking(StructuralValidatorResult):
            structural_status = StructuralValidity.INVALID
            fatal_to_candidate = False

        fatal_nonviolation = P004Result(
            status=RuleCheckStatus.RULE_SATISFIED,
            principle_id="P004",
            source_class=SourceClassification.RULE,
            execution_role=ExecutionRole.HARD_VALIDATION,
            protected_sources=p004_result().protected_sources,
            behavior_id="P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            outcome=RuleCheckStatus.RULE_SATISFIED.value,
            reason="A manually inconsistent fatal non-violation.",
            fatal_to_candidate=True,
        )
        self.assert_rejected(InvalidLooking())
        self.assert_rejected(fatal_nonviolation)

    def test_exact_manually_constructed_violation_lookalikes_are_rejected(self) -> None:
        for genuine in (
            p004_result(),
            degree_peer_result(),
            parent_child_result(),
        ):
            lookalike = exact_manual_copy(genuine)
            with self.subTest(result_type=type(genuine).__name__):
                self.assertIs(type(genuine), type(lookalike))
                self.assertEqual(genuine, lookalike)
                self.assertIsNot(genuine, lookalike)
                self.assert_rejected(lookalike)

    def test_copied_replaced_and_deserialized_origins_are_rejected(self) -> None:
        for genuine in (
            p004_result(),
            degree_peer_result(),
            parent_child_result(),
        ):
            copies = (
                copy.copy(genuine),
                copy.deepcopy(genuine),
                replace(genuine),
                pickle.loads(pickle.dumps(genuine)),
            )
            for copied in copies:
                with self.subTest(
                    origin_type=type(genuine).__name__,
                    copy_type=type(copied).__name__,
                ):
                    self.assertEqual(genuine, copied)
                    self.assertIsNot(genuine, copied)
                    self.assert_rejected(copied)

    def test_mapping_and_json_rehydrated_provenance_cannot_mint_certificate(self) -> None:
        genuine = p004_result()
        provenance_mapping = asdict(genuine)
        self.assert_rejected(provenance_mapping)

        encoded = json.dumps(provenance_mapping, sort_keys=True)
        rehydrated_fields = json.loads(encoded)
        rehydrated_fields.update(
            status=RuleCheckStatus(rehydrated_fields["status"]),
            source_class=SourceClassification(rehydrated_fields["source_class"]),
            execution_role=ExecutionRole(rehydrated_fields["execution_role"]),
            protected_sources=tuple(rehydrated_fields["protected_sources"]),
        )
        rehydrated = P004Result(**rehydrated_fields)
        self.assertEqual(genuine, rehydrated)
        self.assertIsNot(genuine, rehydrated)
        self.assert_rejected(rehydrated)

    def test_registered_result_subclasses_are_rejected(self) -> None:
        class P004ResultSubclass(P004Result):
            __slots__ = ()

        class DegreePeerResultSubclass(DegreePeerConsistencyResult):
            __slots__ = ()

        class ParentChildResultSubclass(ParentChildDegreeResult):
            __slots__ = ()

        for genuine, subclass_type in (
            (p004_result(), P004ResultSubclass),
            (degree_peer_result(), DegreePeerResultSubclass),
            (parent_child_result(), ParentChildResultSubclass),
        ):
            subclass = subclass_type(
                **{
                    field.name: getattr(genuine, field.name)
                    for field in fields(genuine)
                }
            )
            with self.subTest(subclass_type=subclass_type.__name__):
                self.assertIsInstance(subclass, StructuralValidatorResult)
                self.assert_rejected(subclass)

    def test_result_fields_signatures_equality_and_repr_are_preserved(self) -> None:
        cases = (
            (
                p004_result(),
                (
                    "status",
                    "principle_id",
                    "source_class",
                    "execution_role",
                    "protected_sources",
                    "behavior_id",
                    "outcome",
                    "reason",
                    "fatal_to_candidate",
                ),
            ),
            (
                degree_peer_result(),
                (
                    "status",
                    "source_principle_id",
                    "source_class",
                    "execution_role",
                    "protected_sources",
                    "behavior_id",
                    "outcome",
                    "reason",
                    "fatal_to_candidate",
                ),
            ),
            (
                parent_child_result(),
                (
                    "status",
                    "source_principle_id",
                    "source_class",
                    "execution_role",
                    "protected_sources",
                    "behavior_id",
                    "outcome",
                    "reason",
                    "fatal_to_candidate",
                ),
            ),
        )
        for genuine, expected_fields in cases:
            manual = exact_manual_copy(genuine)
            with self.subTest(result_type=type(genuine).__name__):
                self.assertEqual(expected_fields, tuple(type(genuine).__dataclass_fields__))
                self.assertEqual(expected_fields, tuple(inspect.signature(type(genuine)).parameters))
                self.assertEqual(genuine, manual)
                self.assertEqual(repr(genuine), repr(manual))
                self.assertEqual(asdict(genuine), asdict(manual))

    def test_origin_provenance_is_unchanged_and_delegated_by_reference(self) -> None:
        origin = p004_result()
        before = asdict(origin)
        certificate = certify_structural_invalidity(origin)

        self.assertEqual(before, asdict(origin))
        self.assertIs(origin, certificate.origin)
        self.assertIs(origin.protected_sources, certificate.origin_protected_sources)
        self.assertIs(origin.status, certificate.origin_status)
        self.assertIs(origin.execution_role, certificate.origin_execution_role)
        self.assertIs(origin.source_class, certificate.origin_source_class)
        self.assertEqual(origin.reason, certificate.origin_reason)
        self.assertNotIn("structural_validity", origin.__dataclass_fields__)

    def test_certificate_fields_are_private_and_derived_values_are_immutable(self) -> None:
        certificate = certify_structural_invalidity(p004_result())
        self.assertEqual(("_origin", "_attestation"), tuple(field.name for field in fields(certificate)))
        self.assertFalse(hasattr(certificate, "source_class"))
        self.assertFalse(hasattr(certificate, "principle_id"))
        for attribute, value in (
            ("origin", object()),
            ("origin_id", "REWRITTEN"),
            ("origin_behavior_id", "REWRITTEN"),
            ("origin_principle_id", "P999"),
            ("origin_source_class", SourceClassification.OBSERVATION),
            ("origin_execution_role", "REWRITTEN"),
            ("origin_status", "REWRITTEN"),
            ("origin_outcome", "REWRITTEN"),
            ("origin_reason", "REWRITTEN"),
            ("origin_protected_sources", ("REWRITTEN",)),
            ("fatal_to_candidate", False),
            ("structural_validity", StructuralValidity.VALID),
        ):
            with self.subTest(attribute=attribute):
                with self.assertRaises(
                    (FrozenInstanceError, AttributeError, TypeError)
                ):
                    setattr(certificate, attribute, value)

    def test_repeated_certification_preserves_origin_and_issuance_identity(self) -> None:
        origin = p004_result()
        first = certify_structural_invalidity(origin)
        second = certify_structural_invalidity(origin)
        self.assertIs(first.origin, second.origin)
        self.assertEqual(first.origin_id, second.origin_id)
        self.assertRegex(first.origin_id, r"^[0-9a-f]{32}$")

    def test_certificate_copy_is_identity_and_certificate_pickle_is_rejected(self) -> None:
        certificate = certify_structural_invalidity(p004_result())
        self.assertIs(certificate, copy.copy(certificate))
        self.assertIs(certificate, copy.deepcopy(certificate))
        with self.assertRaises(TypeError):
            pickle.dumps(certificate)

    def test_attestation_cannot_be_reused_with_another_origin(self) -> None:
        first = certify_structural_invalidity(p004_result())
        second = certify_structural_invalidity(p004_result())
        forged = object.__new__(CertifiedStructuralInvalidity)
        object.__setattr__(forged, "_origin", second.origin)
        object.__setattr__(
            forged,
            "_attestation",
            object.__getattribute__(first, "_attestation"),
        )
        with self.assertRaises(StructuralInvalidityCertificationError):
            _ = forged.origin

    def test_malformed_certificate_created_without_factory_is_rejected(self) -> None:
        malformed = object.__new__(CertifiedStructuralInvalidity)
        with self.assertRaises(StructuralInvalidityCertificationError):
            _ = malformed.origin

    def test_low_level_origin_mutation_invalidates_every_certificate_view(self) -> None:
        origin = p004_result()
        certificate = certify_structural_invalidity(origin)
        object.__setattr__(origin, "reason", "tampered after issuance")

        accessors = (
            lambda: certificate.origin,
            lambda: certificate.origin_id,
            lambda: certificate.origin_behavior_id,
            lambda: certificate.origin_principle_id,
            lambda: certificate.origin_source_class,
            lambda: certificate.origin_execution_role,
            lambda: certificate.origin_status,
            lambda: certificate.origin_outcome,
            lambda: certificate.origin_reason,
            lambda: certificate.origin_protected_sources,
            lambda: certificate.fatal_to_candidate,
            lambda: certificate.structural_validity,
        )
        for accessor in accessors:
            with self.subTest(accessor=accessor):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    accessor()

    def test_every_certified_origin_field_is_covered_by_fail_closed_validation(self) -> None:
        mutations = {
            "status": RuleCheckStatus.RULE_SATISFIED,
            "principle_id": "P999",
            "source_class": SourceClassification.DEFINITION,
            "execution_role": "HARD_VALIDATION",
            "protected_sources": ("tampered/source",),
            "behavior_id": "TAMPERED_BEHAVIOR",
            "outcome": RuleCheckStatus.RULE_SATISFIED.value,
            "reason": "tampered reason",
            "fatal_to_candidate": False,
        }
        for field_name, replacement in mutations.items():
            origin = p004_result()
            certificate = certify_structural_invalidity(origin)
            object.__setattr__(origin, field_name, replacement)
            with self.subTest(field=field_name):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    _ = certificate.structural_validity

    def test_nullable_degree_principle_provenance_is_digest_protected(self) -> None:
        for origin in (degree_peer_result(), parent_child_result()):
            certificate = certify_structural_invalidity(origin)
            self.assertIsNone(certificate.origin_principle_id)
            object.__setattr__(origin, "source_principle_id", "P999")
            with self.subTest(origin_type=type(origin).__name__):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    _ = certificate.structural_validity

    def test_direct_construction_and_late_or_duplicate_registration_fail(self) -> None:
        with self.assertRaises(TypeError):
            CertifiedStructuralInvalidity()
        with self.assertRaises(TypeError):
            CertifiedStructuralInvalidity(p004_result())

        with self.assertRaises(StructuralInvalidityCertificationError):
            private_contract._register_structural_validator(
                P004Result,
                violation_statuses=(RuleCheckStatus.RULE_VIOLATED,),
                hard_validation_role=ExecutionRole.HARD_VALIDATION,
                principle_attribute="principle_id",
                behavior_id="P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                principle_id="P004",
                source_class=SourceClassification.RULE,
                protected_sources=p004_result().protected_sources,
            )

        p004_sources = p004_result().protected_sources
        with mock.patch.object(private_contract, "_REGISTRY_SEALED", False):
            with self.assertRaisesRegex(
                StructuralInvalidityCertificationError, "already registered"
            ):
                private_contract._register_structural_validator(
                    P004Result,
                    violation_statuses=(RuleCheckStatus.RULE_VIOLATED,),
                    hard_validation_role=ExecutionRole.HARD_VALIDATION,
                    principle_attribute="principle_id",
                    behavior_id="P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                    principle_id="P004",
                    source_class=SourceClassification.RULE,
                    protected_sources=p004_sources,
                )

        @dataclass(frozen=True, slots=True, weakref_slot=True)
        class LateResult(StructuralValidatorResult):
            status: RuleCheckStatus

        with self.assertRaises(StructuralInvalidityCertificationError):
            private_contract._register_structural_validator(
                LateResult,
                violation_statuses=(RuleCheckStatus.RULE_VIOLATED,),
                hard_validation_role=ExecutionRole.HARD_VALIDATION,
                principle_attribute="principle_id",
                behavior_id="UNREGISTERED_TEST_BEHAVIOR",
                principle_id=None,
                source_class=SourceClassification.RULE,
                protected_sources=("test-only",),
            )

    def test_issuance_registry_uses_weak_origin_references(self) -> None:
        origin = p004_result()
        origin_key = id(origin)
        certificate = certify_structural_invalidity(origin)
        reference = weakref.ref(origin)
        self.assertIn(origin_key, private_contract._ISSUED)

        del certificate
        del origin
        gc.collect()

        self.assertIsNone(reference())
        self.assertNotIn(origin_key, private_contract._ISSUED)

    def test_public_api_exports_only_public_contract_names(self) -> None:
        expected = {
            "CertifiedStructuralInvalidity",
            "StructuralInvalidityCertificationError",
            "StructuralValidatorResult",
            "certify_structural_invalidity",
        }
        self.assertTrue(expected.issubset(set(public_contracts.__all__)))
        self.assertTrue(expected.issubset(set(kernel.__all__)))
        for name in expected:
            self.assertIs(getattr(public_contracts, name), getattr(kernel, name))
        for private_name in (
            "_ProducerSpec",
            "_ProducerIssuer",
            "_OriginAttestation",
            "_PRODUCERS",
            "_ISSUED",
            "_register_structural_validator",
            "_seal_structural_validator_registry",
        ):
            self.assertNotIn(private_name, public_contracts.__all__)
            self.assertNotIn(private_name, kernel.__all__)
            self.assertFalse(hasattr(public_contracts, private_name))
            self.assertFalse(hasattr(kernel, private_name))

    def test_certification_api_has_one_input_and_no_public_registration_api(self) -> None:
        self.assertEqual(
            ("origin",), tuple(inspect.signature(certify_structural_invalidity).parameters)
        )
        self.assertFalse(hasattr(public_contracts, "register_structural_validator"))
        self.assertFalse(hasattr(public_contracts, "issue_structural_invalidity"))

    def test_public_only_consumer_reads_complete_origin_provenance(self) -> None:
        origin = p004_result()
        certificate = public_contracts.certify_structural_invalidity(origin)
        observed = read_certificate_through_public_contract(certificate)
        self.assertEqual(
            (
                origin,
                certificate.origin_id,
                origin.behavior_id,
                origin.principle_id,
                origin.source_class,
                origin.execution_role,
                origin.status,
                origin.outcome,
                origin.reason,
                origin.protected_sources,
                origin.fatal_to_candidate,
                StructuralValidity.INVALID,
            ),
            observed,
        )
        helper_source = inspect.getsource(read_certificate_through_public_contract)
        self.assertNotIn("_structural_invalidity", helper_source)

    def test_contract_has_no_forbidden_dependencies_or_logic(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "_structural_invalidity_certification.py"
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
            ".models",
        }
        self.assertEqual(set(), imported_modules - allowed)
        model_imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "models"
            for alias in node.names
        }
        self.assertEqual(
            {"SourceClassification", "StructuralValidity"}, model_imports
        )
        for forbidden in (
            "elliott_runtime",
            "TradingView",
            "market_data",
            "provider",
            "EvidenceState",
            "CountRank",
            "candidate_generation",
            "ranking",
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
        ):
            self.assertNotIn(forbidden, source)

    def test_structural_methodology_inventory_includes_exactly_eight_behaviors(self) -> None:
        observed = set()
        kernel_root = support.SRC / "elliott_methodology_kernel"
        for path in kernel_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                if not any(
                    isinstance(target, ast.Name)
                    and target.id.endswith("_BEHAVIOR_ID")
                    for target in node.targets
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
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
                "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )

    def test_contract_does_not_create_source_class_principle_or_fatality(self) -> None:
        for origin in (p004_result(), degree_peer_result(), parent_child_result()):
            certificate = certify_structural_invalidity(origin)
            with self.subTest(behavior=origin.behavior_id):
                expected_principle = getattr(
                    origin,
                    "principle_id",
                    getattr(origin, "source_principle_id", None),
                )
                self.assertEqual(expected_principle, certificate.origin_principle_id)
                self.assertIs(origin.source_class, certificate.origin_source_class)
                self.assertIs(origin.execution_role, certificate.origin_execution_role)
                self.assertIs(origin.fatal_to_candidate, certificate.fatal_to_candidate)
                self.assertFalse(hasattr(certificate, "source_class"))


if __name__ == "__main__":
    unittest.main()
