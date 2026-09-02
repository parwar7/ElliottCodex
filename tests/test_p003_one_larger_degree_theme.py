import ast
from dataclasses import FrozenInstanceError, fields
import inspect
import unittest

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as private_contract
from elliott_methodology_kernel import (
    MethodologyKernel,
    P003ExecutionRole,
    P003OneLargerDegreeRelation,
    P003OneLargerDegreeThemeInput,
    P003OneLargerDegreeThemeResult,
    P003SearchTheme,
    P003ThemeMappingStatus,
    StructuralInvalidityCertificationError,
    StructuralValidatorResult,
    certify_structural_invalidity,
    map_p003_one_larger_degree_theme,
)
from elliott_methodology_kernel.models import KernelStatus, SourceClassification
from elliott_methodology_kernel.p003_one_larger_degree_theme import (
    P003_BEHAVIOR,
    P003_PRINCIPLE_ID,
    P003_PROTECTED_SOURCES,
)


class P003OneLargerDegreeThemeTests(unittest.TestCase):
    def test_enum_with_maps_to_motive_search_theme(self) -> None:
        result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.WITH)
        )
        self.assertIs(P003ThemeMappingStatus.SEARCH_THEME_MAPPED, result.status)
        self.assertIs(P003SearchTheme.MOTIVE, result.theme)

    def test_raw_exact_with_maps_identically(self) -> None:
        enum_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.WITH)
        )
        raw_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput("WITH")
        )
        self.assertEqual(enum_result, raw_result)

    def test_enum_against_maps_to_corrective_search_theme(self) -> None:
        result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.AGAINST)
        )
        self.assertIs(P003ThemeMappingStatus.SEARCH_THEME_MAPPED, result.status)
        self.assertIs(P003SearchTheme.CORRECTIVE, result.theme)

    def test_raw_exact_against_maps_identically(self) -> None:
        enum_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.AGAINST)
        )
        raw_result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput("AGAINST")
        )
        self.assertEqual(enum_result, raw_result)

    def test_explicit_unresolved_relation_preserves_unresolved_theme(self) -> None:
        for relation in (P003OneLargerDegreeRelation.UNRESOLVED, "UNRESOLVED"):
            with self.subTest(relation=relation):
                result = map_p003_one_larger_degree_theme(
                    P003OneLargerDegreeThemeInput(relation)
                )
                self.assertIs(
                    P003ThemeMappingStatus.SEARCH_THEME_UNRESOLVED,
                    result.status,
                )
                self.assertIs(P003SearchTheme.UNRESOLVED, result.theme)

    def test_missing_unknown_empty_lowercase_padded_and_wrong_types_fail_closed(self) -> None:
        values = (
            None,
            "",
            "UNKNOWN",
            "with",
            "against",
            "unresolved",
            " WITH",
            "WITH ",
            "\tAGAINST",
            True,
            False,
            1,
            1.0,
            object(),
        )
        for value in values:
            with self.subTest(value=repr(value)):
                result = map_p003_one_larger_degree_theme(
                    P003OneLargerDegreeThemeInput(value)
                )
                self.assertIs(
                    P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertIs(P003SearchTheme.UNRESOLVED, result.theme)
                self.assertIs(result.fatal_to_candidate, False)

    def test_wrong_input_container_fails_closed_without_inference(self) -> None:
        for candidate in (None, object(), {"relation_to_one_larger_degree": "WITH"}):
            with self.subTest(candidate_type=type(candidate).__name__):
                result = map_p003_one_larger_degree_theme(candidate)
                self.assertIs(
                    P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertIs(P003SearchTheme.UNRESOLVED, result.theme)

    def test_no_normalization_or_custom_equality_spoofing(self) -> None:
        class AlwaysEqual(str):
            def __eq__(self, other):
                return True

        class RaisingEqual(str):
            def __eq__(self, other):
                raise AssertionError("overloaded equality must not run")

        for relation in (AlwaysEqual("UNKNOWN"), RaisingEqual("UNKNOWN")):
            with self.subTest(relation_type=type(relation).__name__):
                result = map_p003_one_larger_degree_theme(
                    P003OneLargerDegreeThemeInput(relation)
                )
                self.assertIs(
                    P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
                    result.status,
                )
                self.assertIs(P003SearchTheme.UNRESOLVED, result.theme)

    def test_motive_and_corrective_are_search_themes_not_pattern_validation(self) -> None:
        cases = (
            ("WITH", P003SearchTheme.MOTIVE, "no motive pattern"),
            ("AGAINST", P003SearchTheme.CORRECTIVE, "no corrective pattern"),
        )
        for relation, expected_theme, reason_fragment in cases:
            result = map_p003_one_larger_degree_theme(
                P003OneLargerDegreeThemeInput(relation)
            )
            with self.subTest(relation=relation):
                self.assertIs(expected_theme, result.theme)
                self.assertIn(reason_fragment, result.reason)
                for forbidden_attribute in (
                    "structural_validity",
                    "pattern_valid",
                    "validated_pattern",
                    "candidate_valid",
                    "direction",
                    "degree",
                ):
                    self.assertFalse(hasattr(result, forbidden_attribute))

    def test_every_status_family_has_complete_traceability_and_is_nonfatal(self) -> None:
        results = (
            map_p003_one_larger_degree_theme(P003OneLargerDegreeThemeInput("WITH")),
            map_p003_one_larger_degree_theme(
                P003OneLargerDegreeThemeInput("UNRESOLVED")
            ),
            map_p003_one_larger_degree_theme(P003OneLargerDegreeThemeInput(None)),
        )
        self.assertEqual(
            {
                P003ThemeMappingStatus.SEARCH_THEME_MAPPED,
                P003ThemeMappingStatus.SEARCH_THEME_UNRESOLVED,
                P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
            },
            {result.status for result in results},
        )
        for result in results:
            with self.subTest(status=result.status):
                self.assertEqual(P003_PRINCIPLE_ID, result.principle_id)
                self.assertIs(SourceClassification.DEFINITION, result.source_class)
                self.assertIs(
                    P003ExecutionRole.STRUCTURAL_CONTEXT,
                    result.execution_role,
                )
                self.assertIs(P003_PROTECTED_SOURCES, result.protected_sources)
                self.assertTrue(result.protected_sources)
                self.assertEqual(P003_BEHAVIOR, result.behavior_id)
                self.assertEqual(result.status.value, result.outcome)
                self.assertTrue(result.reason)
                self.assertIs(result.fatal_to_candidate, False)

    def test_result_is_frozen_slotted_and_has_exact_narrow_surface(self) -> None:
        result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput("WITH")
        )
        self.assertEqual(
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
                "theme",
            ),
            tuple(field.name for field in fields(result)),
        )
        self.assertFalse(hasattr(result, "__dict__"))
        for attribute, replacement in (
            ("status", P003ThemeMappingStatus.SEARCH_THEME_UNRESOLVED),
            ("principle_id", "P999"),
            ("source_class", SourceClassification.RULE),
            ("execution_role", "HARD_VALIDATION"),
            ("protected_sources", ("rewritten",)),
            ("behavior_id", "REWRITTEN"),
            ("outcome", "REWRITTEN"),
            ("reason", "rewritten"),
            ("fatal_to_candidate", True),
            ("theme", P003SearchTheme.CORRECTIVE),
        ):
            with self.subTest(attribute=attribute):
                with self.assertRaises(
                    (FrozenInstanceError, AttributeError, TypeError)
                ):
                    setattr(result, attribute, replacement)

    def test_input_contract_contains_only_caller_supplied_relation(self) -> None:
        self.assertEqual(
            ("relation_to_one_larger_degree",),
            tuple(field.name for field in fields(P003OneLargerDegreeThemeInput)),
        )
        self.assertEqual(
            ("candidate",),
            tuple(inspect.signature(map_p003_one_larger_degree_theme).parameters),
        )
        forbidden = {
            "price",
            "ohlcv",
            "bars",
            "timeframe",
            "duration",
            "degree",
            "pivot",
            "evidence",
            "rank",
        }
        field_names = {
            field.name.lower() for field in fields(P003OneLargerDegreeThemeInput)
        }
        self.assertTrue(forbidden.isdisjoint(field_names))

    def test_result_is_not_structural_producer_and_cannot_certify(self) -> None:
        result = map_p003_one_larger_degree_theme(
            P003OneLargerDegreeThemeInput("WITH")
        )
        self.assertNotIsInstance(result, StructuralValidatorResult)
        self.assertNotIn(type(result), private_contract._PRODUCERS)
        self.assertNotIn(result.behavior_id, private_contract._BEHAVIOR_IDS)
        with self.assertRaises(StructuralInvalidityCertificationError):
            certify_structural_invalidity(result)

    def test_public_exports_are_complete(self) -> None:
        expected = {
            "P003ExecutionRole",
            "P003OneLargerDegreeRelation",
            "P003OneLargerDegreeThemeInput",
            "P003OneLargerDegreeThemeResult",
            "P003SearchTheme",
            "P003ThemeMappingStatus",
            "map_p003_one_larger_degree_theme",
        }
        self.assertTrue(expected.issubset(set(kernel.__all__)))
        for name in expected:
            self.assertTrue(hasattr(kernel, name))

    def test_module_has_only_behavior_local_dependencies_and_no_prohibited_calls(self) -> None:
        path = (
            support.SRC
            / "elliott_methodology_kernel"
            / "p003_one_larger_degree_theme.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported_modules = set()
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add("." * node.level + (node.module or ""))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertEqual(
            {"__future__", "dataclasses", "enum", ".models"},
            imported_modules,
        )
        prohibited_calls = {
            "check_p004",
            "check_degree_peer_consistency",
            "check_parent_child_degree_adjacency",
            "check_p023_visibility_guard",
            "certify_structural_invalidity",
            "apply_structural_invalidity_evidence_no_rescue",
            "open",
            "connect",
            "run",
            "Popen",
        }
        self.assertTrue(prohibited_calls.isdisjoint(called_names))
        for prohibited_import in (
            "elliott_runtime",
            "TradingView",
            "provider",
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "playwright",
            "selenium",
            "p004",
            "degree_peer_consistency",
            "parent_child_degree_adjacency",
            "p023_visibility_guard",
            "structural_invalidity_evidence_no_rescue",
            "_structural_invalidity_certification",
        ):
            with self.subTest(prohibited_import=prohibited_import):
                self.assertNotIn(prohibited_import, imported_modules)

    def test_no_runtime_or_orchestration_wiring_exists(self) -> None:
        runtime_root = support.SRC / "elliott_runtime"
        references = []
        for path in runtime_root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if "p003_one_larger_degree_theme" in source or P003_BEHAVIOR in source:
                references.append(str(path))
        self.assertEqual([], references)

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        source = inspect.getsource(MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source)
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, kernel.KernelStatus.NOT_IMPLEMENTED)

    def test_executable_methodology_inventory_is_exactly_nine(self) -> None:
        observed = set()
        kernel_root = support.SRC / "elliott_methodology_kernel"
        special_names = {"NO_RESCUE_BEHAVIOR", "P003_BEHAVIOR"}
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

    def test_runtime_vocabulary_and_protected_meaning_are_explicit(self) -> None:
        module = inspect.getmodule(map_p003_one_larger_degree_theme)
        self.assertIsNotNone(module)
        self.assertIn("behavior-local Runtime vocabulary", module.__doc__)
        self.assertEqual(
            {"WITH", "AGAINST", "UNRESOLVED"},
            {member.value for member in P003OneLargerDegreeRelation},
        )
        self.assertEqual(
            {"MOTIVE", "CORRECTIVE", "UNRESOLVED"},
            {member.value for member in P003SearchTheme},
        )
        self.assertEqual(
            {"STRUCTURAL_CONTEXT"},
            {member.value for member in P003ExecutionRole},
        )


if __name__ == "__main__":
    unittest.main()
