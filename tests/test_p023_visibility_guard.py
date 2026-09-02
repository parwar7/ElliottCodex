import ast
import json
import inspect
import unittest
from dataclasses import MISSING, asdict
from enum import StrEnum

import support
from elliott_methodology_kernel import (
    MethodologyKernel,
    P023VisibilityCheckStatus,
    P023VisibilityExecutionRole,
    P023VisibilityInput,
    P023VisibilityResult,
    P023VisibilityState,
    check_p023_visibility_guard,
)
from elliott_methodology_kernel.models import InternalStatus, SourceClassification


def visibility(value=None) -> P023VisibilityInput:
    return P023VisibilityInput(visibility_state=value)


class UnrelatedVisibilityState(StrEnum):
    VISIBLE = "VISIBLE"
    NOT_VISIBLE = "NOT_VISIBLE"
    UNKNOWN = "UNKNOWN"


class ExactVisibilityString(str):
    pass


class EqualitySpoof:
    def __init__(self, target: str) -> None:
        self.target = target

    def __eq__(self, other: object) -> bool:
        return getattr(other, "value", other) == self.target


class RaisingEquality:
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("custom equality must not be called")


class SpoofingString(str):
    def __eq__(self, other: object) -> bool:
        return True


class RaisingString(str):
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("custom string equality must not be called")


class P023VisibilityGuardTests(unittest.TestCase):
    def test_visibility_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            {"VISIBLE", "NOT_VISIBLE", "UNKNOWN"},
            {state.value for state in P023VisibilityState},
        )
        self.assertNotIn("PARTIALLY_VISIBLE", P023VisibilityState.__members__)

    def test_status_vocabulary_is_exact_and_has_no_stronger_status(self) -> None:
        statuses = {status.value for status in P023VisibilityCheckStatus}
        self.assertEqual(
            {
                "VISIBILITY_GUARD_PASSED",
                "INTERNALS_UNRESOLVED",
                "UNRESOLVED_MISSING_INPUT",
            },
            statuses,
        )
        self.assertTrue(
            statuses.isdisjoint(
                {
                    "INTERNALS_CONFIRMED",
                    "INTERNALS_VIOLATED",
                    "RULE_SATISFIED",
                    "RULE_VIOLATED",
                }
            )
        )

    def test_enum_visible_passes_only_the_visibility_guard(self) -> None:
        result = check_p023_visibility_guard(
            visibility(P023VisibilityState.VISIBLE)
        )
        self.assertEqual(
            P023VisibilityCheckStatus.VISIBILITY_GUARD_PASSED, result.status
        )
        self.assertIs(result.finer_data_required, False)
        self.assertFalse(result.fatal_to_candidate)

    def test_raw_visible_matches_enum_behavior(self) -> None:
        enum_result = check_p023_visibility_guard(
            visibility(P023VisibilityState.VISIBLE)
        )
        raw_result = check_p023_visibility_guard(visibility("VISIBLE"))
        self.assertEqual(enum_result, raw_result)

    def test_visible_never_confirms_or_violates_internals(self) -> None:
        result = check_p023_visibility_guard(visibility("VISIBLE"))
        self.assertNotEqual("INTERNALS_CONFIRMED", result.status.value)
        self.assertNotEqual("INTERNALS_VIOLATED", result.status.value)
        self.assertNotEqual("RULE_SATISFIED", result.status.value)
        self.assertNotEqual("RULE_VIOLATED", result.status.value)

    def test_enum_not_visible_leaves_internals_unresolved(self) -> None:
        result = check_p023_visibility_guard(
            visibility(P023VisibilityState.NOT_VISIBLE)
        )
        self.assertEqual(
            P023VisibilityCheckStatus.INTERNALS_UNRESOLVED, result.status
        )
        self.assertIs(result.finer_data_required, True)
        self.assertFalse(result.fatal_to_candidate)

    def test_raw_not_visible_matches_enum_behavior(self) -> None:
        enum_result = check_p023_visibility_guard(
            visibility(P023VisibilityState.NOT_VISIBLE)
        )
        raw_result = check_p023_visibility_guard(visibility("NOT_VISIBLE"))
        self.assertEqual(enum_result, raw_result)

    def test_not_visible_never_becomes_violation(self) -> None:
        result = check_p023_visibility_guard(visibility("NOT_VISIBLE"))
        self.assertNotEqual("INTERNALS_VIOLATED", result.status.value)
        self.assertNotEqual("RULE_VIOLATED", result.status.value)
        self.assertFalse(result.fatal_to_candidate)

    def test_enum_unknown_is_unresolved_diagnostic(self) -> None:
        result = check_p023_visibility_guard(
            visibility(P023VisibilityState.UNKNOWN)
        )
        self.assertEqual(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )
        self.assertIsNone(result.finer_data_required)
        self.assertFalse(result.fatal_to_candidate)

    def test_raw_unknown_matches_enum_behavior(self) -> None:
        enum_result = check_p023_visibility_guard(
            visibility(P023VisibilityState.UNKNOWN)
        )
        raw_result = check_p023_visibility_guard(visibility("UNKNOWN"))
        self.assertEqual(enum_result, raw_result)

    def test_missing_and_none_are_unresolved_diagnostics(self) -> None:
        default_result = check_p023_visibility_guard(P023VisibilityInput())
        explicit_result = check_p023_visibility_guard(visibility(None))
        self.assertEqual(default_result, explicit_result)
        self.assertEqual(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            explicit_result.status,
        )
        self.assertIsNone(explicit_result.finer_data_required)
        self.assertFalse(explicit_result.fatal_to_candidate)

    def test_malformed_values_are_not_normalized(self) -> None:
        malformed_values = (
            "",
            "   ",
            "visible",
            " VISIBLE",
            "VISIBLE ",
            " VISIBLE ",
            True,
            1,
            1.0,
            object(),
            "PARTIALLY_VISIBLE",
        )
        for malformed in malformed_values:
            with self.subTest(value=repr(malformed)):
                result = check_p023_visibility_guard(visibility(malformed))
                self.assertEqual(
                    P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertIsNone(result.finer_data_required)
                self.assertFalse(result.fatal_to_candidate)
                self.assertNotEqual(
                    P023VisibilityCheckStatus.VISIBILITY_GUARD_PASSED,
                    result.status,
                )
                self.assertNotEqual(
                    P023VisibilityCheckStatus.INTERNALS_UNRESOLVED,
                    result.status,
                )

    def test_float_is_unresolved_missing_input(self) -> None:
        result = check_p023_visibility_guard(visibility(1.0))
        self.assertEqual(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            result.status,
        )
        self.assertIsNone(result.finer_data_required)
        self.assertFalse(result.fatal_to_candidate)

    def test_unrelated_str_enum_exact_values_preserve_string_contract(self) -> None:
        cases = (
            (UnrelatedVisibilityState.VISIBLE, "VISIBLE"),
            (UnrelatedVisibilityState.NOT_VISIBLE, "NOT_VISIBLE"),
            (UnrelatedVisibilityState.UNKNOWN, "UNKNOWN"),
        )
        for unrelated, raw in cases:
            with self.subTest(value=unrelated):
                self.assertEqual(
                    check_p023_visibility_guard(visibility(raw)),
                    check_p023_visibility_guard(visibility(unrelated)),
                )

    def test_exact_value_str_subclass_preserves_string_contract(self) -> None:
        self.assertEqual(
            check_p023_visibility_guard(visibility("VISIBLE")),
            check_p023_visibility_guard(
                visibility(ExactVisibilityString("VISIBLE"))
            ),
        )
        self.assertEqual(
            check_p023_visibility_guard(visibility("VISIBLE")),
            check_p023_visibility_guard(visibility(RaisingString("VISIBLE"))),
        )

    def test_exact_two_sided_padding_is_not_normalized(self) -> None:
        result = check_p023_visibility_guard(visibility(" VISIBLE "))
        self.assertEqual(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            result.status,
        )
        self.assertIsNone(result.finer_data_required)
        self.assertFalse(result.fatal_to_candidate)

    def test_custom_equality_cannot_spoof_or_escape_the_guard(self) -> None:
        malformed_values = (
            EqualitySpoof("VISIBLE"),
            EqualitySpoof("NOT_VISIBLE"),
            RaisingEquality(),
            SpoofingString("MALFORMED"),
            RaisingString("MALFORMED"),
        )
        for malformed in malformed_values:
            with self.subTest(value=type(malformed).__name__):
                result = check_p023_visibility_guard(visibility(malformed))
                self.assertEqual(
                    P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertNotEqual(
                    P023VisibilityCheckStatus.VISIBILITY_GUARD_PASSED,
                    result.status,
                )
                self.assertNotEqual(
                    P023VisibilityCheckStatus.INTERNALS_UNRESOLVED,
                    result.status,
                )
                self.assertIsNone(result.finer_data_required)
                self.assertFalse(result.fatal_to_candidate)

    def test_local_and_shared_unresolved_statuses_are_distinct_types(self) -> None:
        local = P023VisibilityCheckStatus.INTERNALS_UNRESOLVED
        shared = InternalStatus.UNRESOLVED
        self.assertIsNot(type(local), type(shared))
        self.assertIsNot(local, shared)
        self.assertEqual(local, shared)
        self.assertEqual(local.value, shared.value)
        self.assertEqual(json.dumps(local), json.dumps(shared))

    def test_complete_result_retains_behavior_context_when_serialized(self) -> None:
        result = check_p023_visibility_guard(visibility("NOT_VISIBLE"))
        serialized = json.loads(json.dumps(asdict(result)))
        self.assertEqual("INTERNALS_UNRESOLVED", serialized["status"])
        self.assertEqual(
            "P023_INTERNAL_VISIBILITY_GUARD",
            serialized["behavior_id"],
        )

    def test_finer_data_required_has_no_default(self) -> None:
        field = P023VisibilityResult.__dataclass_fields__["finer_data_required"]
        self.assertIs(MISSING, field.default)
        self.assertIs(MISSING, field.default_factory)
        self.assertIs(
            inspect.Parameter.empty,
            inspect.signature(P023VisibilityResult).parameters[
                "finer_data_required"
            ].default,
        )

    def test_unknown_missing_and_malformed_reasons_are_distinct(self) -> None:
        unknown = check_p023_visibility_guard(visibility("UNKNOWN"))
        missing = check_p023_visibility_guard(visibility(None))
        malformed = check_p023_visibility_guard(visibility("visible"))
        reasons = {unknown.reason, missing.reason, malformed.reason}
        self.assertEqual(3, len(reasons))
        self.assertTrue(all(reasons))

    def test_every_status_family_has_complete_traceability(self) -> None:
        results = (
            check_p023_visibility_guard(visibility("VISIBLE")),
            check_p023_visibility_guard(visibility("NOT_VISIBLE")),
            check_p023_visibility_guard(visibility("UNKNOWN")),
        )
        self.assertEqual(
            set(P023VisibilityCheckStatus), {result.status for result in results}
        )
        expected_sources = {
            "docs/elliott/SOURCE_EVIDENCE_MAP.json#P023",
            "docs/elliott/DEGREE_RECURSION_BRAIN.md#5-recursive-validator",
            "docs/elliott/DEGREE_RECURSION_BRAIN.md#6-data-resolution-rule",
            "docs/elliott/MASTER_PROTOCOL.md#step-6",
            "AGENTS.md#non-negotiable-operating-constraints",
        }
        for result in results:
            with self.subTest(status=result.status):
                self.assertEqual("P023", result.principle_id)
                self.assertEqual(
                    SourceClassification.DEFINITION, result.source_class
                )
                self.assertEqual(
                    P023VisibilityExecutionRole.HARD_VALIDATION,
                    result.execution_role,
                )
                self.assertEqual(
                    "P023_INTERNAL_VISIBILITY_GUARD", result.behavior_id
                )
                self.assertEqual(result.status.value, result.outcome)
                self.assertTrue(result.reason)
                self.assertEqual(expected_sources, set(result.protected_sources))

    def test_all_possible_result_families_are_nonfatal(self) -> None:
        results = (
            check_p023_visibility_guard(visibility("VISIBLE")),
            check_p023_visibility_guard(visibility("NOT_VISIBLE")),
            check_p023_visibility_guard(visibility("UNKNOWN")),
            check_p023_visibility_guard(visibility(None)),
            check_p023_visibility_guard(visibility("PARTIALLY_VISIBLE")),
        )
        self.assertTrue(all(not result.fatal_to_candidate for result in results))

    def test_input_contract_contains_only_visibility_state(self) -> None:
        self.assertEqual(
            ("visibility_state",),
            tuple(P023VisibilityInput.__dataclass_fields__),
        )
        self.assertEqual(
            ("candidate",),
            tuple(inspect.signature(check_p023_visibility_guard).parameters),
        )

    def test_result_contract_has_no_timeframe_or_degree_selection(self) -> None:
        required = {
            "status",
            "principle_id",
            "source_class",
            "execution_role",
            "protected_sources",
            "behavior_id",
            "outcome",
            "reason",
            "fatal_to_candidate",
            "finer_data_required",
        }
        self.assertTrue(
            required.issubset(P023VisibilityResult.__dataclass_fields__)
        )
        forbidden = {
            "next_timeframe",
            "next_required_timeframe",
            "current_resolution",
            "timeframe",
            "degree",
            "aggregation",
            "aggregated",
            "resampled",
            "bars",
            "ohlcv",
            "pivot",
            "wave",
            "pattern",
            "subject_id",
            "required_internals_declared",
        }
        self.assertTrue(
            set(P023VisibilityResult.__dataclass_fields__).isdisjoint(forbidden)
        )
        self.assertTrue(
            set(P023VisibilityInput.__dataclass_fields__).isdisjoint(forbidden)
        )

    def test_prohibited_extra_inputs_are_rejected(self) -> None:
        forbidden = (
            "aggregated",
            "resampled",
            "bars",
            "ohlcv",
            "timeframe",
            "current_resolution",
            "degree",
            "pivot",
            "wave",
            "pattern",
            "subject_id",
            "required_internals_declared",
        )
        for field in forbidden:
            with self.subTest(field=field), self.assertRaises(TypeError):
                P023VisibilityInput(
                    visibility_state=P023VisibilityState.VISIBLE,
                    **{field: object()},
                )

    def test_public_surface_exposes_only_approved_p023_symbols(self) -> None:
        import elliott_methodology_kernel as kernel

        expected = {
            "P023VisibilityCheckStatus",
            "P023VisibilityExecutionRole",
            "P023VisibilityInput",
            "P023VisibilityResult",
            "P023VisibilityState",
            "check_p023_visibility_guard",
        }
        observed = {
            name
            for name in kernel.__all__
            if name.startswith("P023") or name == "check_p023_visibility_guard"
        }
        self.assertEqual(expected, observed)
        for private_constant in (
            "P023_BEHAVIOR_ID",
            "P023_PRINCIPLE_ID",
            "P023_PROTECTED_SOURCES",
        ):
            self.assertFalse(hasattr(kernel, private_constant))

    def test_behavior_has_only_approved_dependencies(self) -> None:
        module = inspect.getmodule(check_p023_visibility_guard)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        imported_modules = set()
        imported_symbols = set()
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add("." * node.level + (node.module or ""))
                imported_symbols.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called_names.add(node.func.id)

        self.assertEqual(
            {"__future__", "dataclasses", "enum", ".models"},
            imported_modules,
        )
        self.assertEqual(
            {"annotations", "dataclass", "StrEnum", "SourceClassification"},
            imported_symbols,
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "check_p004",
                    "check_degree_peer_consistency",
                    "check_parent_child_degree_adjacency",
                }
            )
        )

        forbidden_fragments = (
            "elliott_runtime",
            "tradingview",
            "provider",
            "requests",
            "urllib",
            "http",
            "socket",
            "subprocess",
            "powershell",
            "cmd",
            "selenium",
            "playwright",
            "p004",
            "degree_peer_consistency",
            "parent_child_degree_adjacency",
        )
        lowered_modules = {name.lower() for name in imported_modules}
        for fragment in forbidden_fragments:
            self.assertFalse(
                any(fragment in name for name in lowered_modules),
                fragment,
            )

        forbidden_symbols = {
            "InternalStatus",
            "Bar",
            "Timeframe",
            "DegreeStatus",
            "EvidenceRecord",
            "EvidenceState",
            "CountRank",
            "CountRepresentation",
        }
        self.assertTrue(imported_symbols.isdisjoint(forbidden_symbols))

        for fixed_mapping_token in ("Daily", "4H", "1H", "15m"):
            self.assertNotIn(fixed_mapping_token, source)

    def test_runtime_does_not_import_private_p023_module(self) -> None:
        private_module = "elliott_methodology_kernel.p023_visibility_guard"
        public_symbols = {
            "P023VisibilityCheckStatus",
            "P023VisibilityExecutionRole",
            "P023VisibilityInput",
            "P023VisibilityResult",
            "P023VisibilityState",
            "check_p023_visibility_guard",
        }
        violations = []
        for path in (support.SRC / "elliott_runtime").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            root_aliases = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(alias.name == private_module for alias in node.names):
                        violations.append(f"{path}: {private_module}")
                    root_aliases.update(
                        alias.asname or alias.name
                        for alias in node.names
                        if alias.name == "elliott_methodology_kernel"
                    )
                elif isinstance(node, ast.ImportFrom):
                    if node.module == private_module:
                        violations.append(f"{path}: {private_module}")
                    if node.module == "elliott_methodology_kernel" and any(
                        alias.name in public_symbols for alias in node.names
                    ):
                        violations.append(f"{path}: public P023 wiring")
                    if node.module == "elliott_methodology_kernel" and any(
                        alias.name == "p023_visibility_guard"
                        for alias in node.names
                    ):
                        violations.append(f"{path}: private P023 module wiring")
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in root_aliases
                    and node.attr in public_symbols
                ):
                    violations.append(f"{path}: public P023 attribute wiring")
        self.assertEqual([], violations)

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        analyze_source = inspect.getsource(MethodologyKernel.analyze)
        api_module = inspect.getmodule(MethodologyKernel)
        self.assertIsNotNone(api_module)
        api_source = inspect.getsource(api_module)
        self.assertIn("KernelStatus.NOT_IMPLEMENTED", analyze_source)
        self.assertNotIn("check_p023_visibility_guard", api_source)
        self.assertNotIn("P023_INTERNAL_VISIBILITY_GUARD", api_source)


if __name__ == "__main__":
    unittest.main()
