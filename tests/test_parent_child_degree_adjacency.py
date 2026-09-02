import ast
import inspect
import unittest

import support
from elliott_methodology_kernel import (
    ParentChildDegreeCheckStatus,
    ParentChildDegreeExecutionRole,
    ParentChildDegreeInput,
    check_parent_child_degree_adjacency,
)
from elliott_methodology_kernel.models import DegreeStatus, SourceClassification


def pair(
    parent: str | None,
    child: str | None,
    *,
    parent_status: DegreeStatus = DegreeStatus.RESOLVED,
    child_status: DegreeStatus = DegreeStatus.RESOLVED,
) -> ParentChildDegreeInput:
    return ParentChildDegreeInput(
        parent_degree=parent,
        parent_degree_status=parent_status,
        child_degree=child,
        child_degree_status=child_status,
    )


class ParentChildDegreeAdjacencyTests(unittest.TestCase):
    def test_every_adjacent_hierarchy_pair_satisfies(self) -> None:
        adjacent_pairs = (
            ("Grand Supercycle", "Supercycle"),
            ("Supercycle", "Cycle"),
            ("Cycle", "Primary"),
            ("Primary", "Intermediate"),
            ("Intermediate", "Minor"),
            ("Minor", "Minute"),
            ("Minute", "Minuette"),
            ("Minuette", "Subminuette"),
        )
        for parent, child in adjacent_pairs:
            with self.subTest(parent=parent, child=child):
                result = check_parent_child_degree_adjacency(pair(parent, child))
                self.assertEqual(
                    ParentChildDegreeCheckStatus.RULE_SATISFIED, result.status
                )
                self.assertFalse(result.fatal_to_candidate)

    def test_same_degree_violates_and_is_fatal(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", "Cycle"))
        self.assertEqual(ParentChildDegreeCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_skip_down_one_level_violates_and_is_fatal(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Intermediate")
        )
        self.assertEqual(ParentChildDegreeCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_skip_down_multiple_levels_violates_and_is_fatal(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", "Minute"))
        self.assertEqual(ParentChildDegreeCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_reverse_one_level_violates_and_is_fatal(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Primary", "Cycle"))
        self.assertEqual(ParentChildDegreeCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_reverse_multiple_levels_violates_and_is_fatal(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Intermediate", "Supercycle")
        )
        self.assertEqual(ParentChildDegreeCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_parent_unresolved_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", parent_status=DegreeStatus.UNRESOLVED)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )
        self.assertFalse(result.fatal_to_candidate)

    def test_child_unresolved_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", child_status=DegreeStatus.UNRESOLVED)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_both_unresolved_are_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair(
                None,
                None,
                parent_status=DegreeStatus.UNRESOLVED,
                child_status=DegreeStatus.UNRESOLVED,
            )
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_resolved_parent_missing_label_is_missing_input(self) -> None:
        for parent in (None, ""):
            with self.subTest(parent=parent):
                result = check_parent_child_degree_adjacency(
                    pair(parent, "Primary")
                )
                self.assertEqual(
                    ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )

    def test_resolved_child_missing_label_is_missing_input(self) -> None:
        for child in (None, ""):
            with self.subTest(child=child):
                result = check_parent_child_degree_adjacency(pair("Cycle", child))
                self.assertEqual(
                    ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )

    def test_unknown_parent_is_unresolved_and_nonfatal(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Unknown", "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )
        self.assertFalse(result.fatal_to_candidate)

    def test_unknown_child_is_unresolved_and_nonfatal(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", "Unknown"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_case_changed_label_is_not_normalized(self) -> None:
        result = check_parent_child_degree_adjacency(pair("cycle", "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_abbreviation_is_not_normalized(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", "Prim"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_whitespace_only_parent_is_unknown_degree(self) -> None:
        result = check_parent_child_degree_adjacency(pair("   ", "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_whitespace_only_child_is_unknown_degree(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", "   "))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_leading_whitespace_on_valid_parent_is_unknown_degree(self) -> None:
        result = check_parent_child_degree_adjacency(pair(" Cycle", "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_trailing_whitespace_on_valid_child_is_unknown_degree(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", "Primary "))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_uppercase_canonical_looking_label_is_unknown_degree(self) -> None:
        result = check_parent_child_degree_adjacency(pair("CYCLE", "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_integer_parent_label_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(pair(123, "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_integer_child_label_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", 123))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_boolean_parent_label_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(pair(True, "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_boolean_child_label_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", False))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_arbitrary_object_parent_label_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(pair(object(), "Primary"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_arbitrary_object_child_label_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Cycle", object()))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    # The following precedence tests lock Runtime diagnostic policy only.
    # The protected Elliott sources do not establish diagnostic precedence.
    def test_runtime_diagnostic_policy_parent_unresolved_precedes_unknown_child(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Unknown", parent_status=DegreeStatus.UNRESOLVED)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )
        self.assertEqual(
            "Both parent and child degree statuses must be explicitly resolved.",
            result.reason,
        )

    def test_runtime_diagnostic_policy_child_unresolved_precedes_unknown_parent(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Unknown", "Primary", child_status=DegreeStatus.UNRESOLVED)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_runtime_diagnostic_policy_child_unresolved_precedes_subminuette_boundary(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair(
                "Subminuette",
                "Primary",
                child_status=DegreeStatus.UNRESOLVED,
            )
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_runtime_diagnostic_policy_unknown_child_precedes_subminuette_boundary(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Subminuette", "Unknown")
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )
        self.assertEqual(
            "A supplied resolved degree label is not in the protected hierarchy.",
            result.reason,
        )

    def test_runtime_diagnostic_policy_subminuette_with_canonical_child_reaches_boundary(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Subminuette", "Grand Supercycle")
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_NO_DEFINED_SUBORDINATE,
            result.status,
        )

    def test_runtime_diagnostic_policy_unresolved_child_precedes_missing_parent_label(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("", "Primary", child_status=DegreeStatus.UNRESOLVED)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_runtime_diagnostic_policy_two_distinct_unknown_labels_reach_unknown_gate(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Unknown Parent", "Unknown Child")
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_runtime_diagnostic_policy_parent_unknown_and_child_unknown_reach_unknown_gate(self) -> None:
        result = check_parent_child_degree_adjacency(pair("Unknown", "Unknown"))
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE, result.status
        )

    def test_runtime_diagnostic_policy_both_unresolved_use_status_reason(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair(
                None,
                None,
                parent_status=DegreeStatus.UNRESOLVED,
                child_status=DegreeStatus.UNRESOLVED,
            )
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )
        self.assertEqual(
            "Both parent and child degree statuses must be explicitly resolved.",
            result.reason,
        )

    def test_raw_resolved_status_matches_degree_status_resolved(self) -> None:
        enum_result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary")
        )
        raw_result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", parent_status="RESOLVED", child_status="RESOLVED")
        )
        self.assertEqual(enum_result, raw_result)

    def test_raw_unresolved_status_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", parent_status="DEGREE_UNRESOLVED")
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_unknown_raw_status_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", parent_status="UNKNOWN")
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_none_status_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", parent_status=None)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_boolean_status_is_missing_input(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Cycle", "Primary", parent_status=True)
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_subminuette_parent_has_no_defined_subordinate(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Subminuette", "Grand Supercycle")
        )
        self.assertEqual(
            ParentChildDegreeCheckStatus.UNRESOLVED_NO_DEFINED_SUBORDINATE,
            result.status,
        )
        self.assertFalse(result.fatal_to_candidate)

    def test_satisfaction_is_not_candidate_wide_validity(self) -> None:
        result = check_parent_child_degree_adjacency(
            pair("Minuette", "Subminuette")
        )
        self.assertEqual(ParentChildDegreeCheckStatus.RULE_SATISFIED, result.status)
        self.assertIn("no broader candidate validity", result.reason.lower())

    def test_only_rule_violation_is_fatal(self) -> None:
        cases = (
            check_parent_child_degree_adjacency(pair("Cycle", "Primary")),
            check_parent_child_degree_adjacency(pair("Cycle", "Cycle")),
            check_parent_child_degree_adjacency(
                pair("Cycle", None, child_status=DegreeStatus.UNRESOLVED)
            ),
            check_parent_child_degree_adjacency(pair("Cycle", "Unknown")),
            check_parent_child_degree_adjacency(
                pair("Subminuette", "Grand Supercycle")
            ),
        )
        for result in cases:
            self.assertEqual(
                result.status == ParentChildDegreeCheckStatus.RULE_VIOLATED,
                result.fatal_to_candidate,
            )

    def test_complete_traceability_for_every_status_family(self) -> None:
        results = (
            check_parent_child_degree_adjacency(pair("Cycle", "Primary")),
            check_parent_child_degree_adjacency(pair("Cycle", "Cycle")),
            check_parent_child_degree_adjacency(
                pair("Cycle", None, child_status=DegreeStatus.UNRESOLVED)
            ),
            check_parent_child_degree_adjacency(pair("Cycle", "Unknown")),
            check_parent_child_degree_adjacency(
                pair("Subminuette", "Grand Supercycle")
            ),
        )
        self.assertEqual(
            set(ParentChildDegreeCheckStatus), {result.status for result in results}
        )
        for result in results:
            self.assertIsNone(result.source_principle_id)
            self.assertEqual(SourceClassification.DEFINITION, result.source_class)
            self.assertEqual(
                ParentChildDegreeExecutionRole.HARD_VALIDATION,
                result.execution_role,
            )
            self.assertEqual("PARENT_CHILD_DEGREE_ADJACENCY", result.behavior_id)
            self.assertTrue(result.protected_sources)
            self.assertEqual(result.status.value, result.outcome)
            self.assertTrue(result.reason)

    def test_input_has_no_market_or_tree_fields(self) -> None:
        fields = set(ParentChildDegreeInput.__dataclass_fields__)
        self.assertEqual(
            {
                "parent_degree",
                "parent_degree_status",
                "child_degree",
                "child_degree_status",
            },
            fields,
        )
        for forbidden in (
            "timeframe",
            "duration",
            "price",
            "bars",
            "ohlcv",
            "siblings",
            "parent_node",
        ):
            self.assertNotIn(forbidden, fields)

    def test_behavior_is_independent_and_has_no_forbidden_dependencies(self) -> None:
        module = inspect.getmodule(check_parent_child_degree_adjacency)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        imported_modules = set()
        imported_symbols = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                relative_prefix = "." * node.level
                imported_module = relative_prefix + (node.module or "")
                imported_modules.add(imported_module)
                imported_symbols.add(
                    (imported_module, tuple(alias.name for alias in node.names))
                )

        self.assertEqual(
            set(),
            imported_modules
            - {
                "__future__",
                "dataclasses",
                "enum",
                "._structural_invalidity_certification",
                ".models",
            },
        )
        self.assertEqual(
            {
                ("__future__", ("annotations",)),
                ("dataclasses", ("dataclass",)),
                ("enum", ("StrEnum",)),
                (
                    "._structural_invalidity_certification",
                    (
                        "StructuralValidatorResult",
                        "_register_structural_validator",
                    ),
                ),
                (".models", ("DegreeStatus", "SourceClassification")),
            },
            imported_symbols,
        )

        forbidden_exact_imports = {
            ".p004",
            ".degree_peer_consistency",
            "elliott_methodology_kernel.p004",
            "elliott_methodology_kernel.degree_peer_consistency",
        }
        self.assertTrue(imported_modules.isdisjoint(forbidden_exact_imports))

        forbidden_import_fragments = (
            "elliott_runtime",
            "market_data",
            "tradingview",
            "provider",
            "evidence",
            "ranking",
            "monitoring",
            "alert",
        )
        for imported_module in imported_modules:
            lowered = imported_module.lower()
            for forbidden in forbidden_import_fragments:
                self.assertNotIn(forbidden, lowered)

        for forbidden in (
            "degree_peer_consistency",
            "elliott_methodology_kernel.p004",
            "elliott_runtime",
            "TradingView",
            "market_data",
            "provider",
            "EvidenceState",
            "evidence.",
            "CountRank",
            "ranking",
            "monitoring",
            "alert",
            "Fibonacci",
        ):
            self.assertNotIn(forbidden, source)

        private_module = "elliott_methodology_kernel.parent_child_degree_adjacency"
        runtime_violations = []
        for path in (support.SRC / "elliott_runtime").rglob("*.py"):
            runtime_tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(runtime_tree):
                if isinstance(node, ast.Import):
                    if any(alias.name == private_module for alias in node.names):
                        runtime_violations.append(f"{path}: {private_module}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module == private_module:
                        runtime_violations.append(f"{path}: {private_module}")
                    if node.module == "elliott_methodology_kernel" and any(
                        alias.name == "parent_child_degree_adjacency"
                        for alias in node.names
                    ):
                        runtime_violations.append(
                            f"{path}: elliott_methodology_kernel import parent_child_degree_adjacency"
                        )
        self.assertEqual([], runtime_violations)


if __name__ == "__main__":
    unittest.main()
