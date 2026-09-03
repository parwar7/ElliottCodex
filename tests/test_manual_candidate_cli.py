import ast
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

import support
from elliott_methodology_kernel import (
    BoundedManualChartAnalysisRequest,
    CandidateScope,
    ImpulseDirection,
    ManualCardinalityBehavior,
    ManualDegreePeerFact,
    ManualDirectChildCardinalityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualP004Wave2OriginFact,
    ManualP023VisibilityFact,
    ManualParentChildDegreeFact,
    P003OneLargerDegreeRelation,
    P023VisibilityState,
)
from elliott_methodology_kernel.models import DegreeStatus, InternalStatus
from elliott_runtime.manual_candidate_cli import (
    ARTIFACT_CLASSIFICATION,
    INPUT_SCHEMA_VERSION,
    MAX_INPUT_BYTES,
    ManualCandidateCliError,
    SNAPSHOT_SCHEMA_VERSION,
    load_manual_candidate_file,
    main,
    parse_manual_candidate_document,
)


EXAMPLES = support.RUNTIME_ROOT / "examples" / "manual_candidate"
MODULE = support.SRC / "elliott_runtime" / "manual_candidate_cli.py"


def base_document(*, facts=None):
    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "request_id": "cli-request",
        "requested_at_utc": "2026-09-03T12:00:00Z",
        "subject": {
            "subject_id": "cli-subject",
            "observation_provenance_ref": "manual-chart:cli-subject",
        },
        "candidate_id": "cli-candidate",
        "facts": [] if facts is None else facts,
        "provenance_refs": ["cli:human-entered"],
    }


class ManualCandidateCliTests(unittest.TestCase):
    def test_example_loads_as_exact_typed_non_authoritative_request(self) -> None:
        request = load_manual_candidate_file(EXAMPLES / "p004_reviewed.json")
        self.assertIs(BoundedManualChartAnalysisRequest, type(request))
        self.assertEqual("example-manual-subject", request.subject.subject_id)
        self.assertIs(tuple, type(request.manual_behavior_facts))
        fact = request.manual_behavior_facts[0]
        self.assertIs(ManualP004Wave2OriginFact, type(fact))
        self.assertIs(CandidateScope.NORMAL_IMPULSE, fact.candidate_scope)
        self.assertIs(ImpulseDirection.UP, fact.direction)

    def test_every_supported_fact_form_constructs_only_existing_exact_fact_types(self) -> None:
        document = base_document(
            facts=[
                {
                    "type": "P004_WAVE2_ORIGIN",
                    "candidate_scope": "NORMAL_IMPULSE",
                    "direction": "DOWN",
                    "wave1_origin_price": 10,
                    "wave2_end_price": 9.5,
                },
                {
                    "type": "DEGREE_PEER_CONSISTENCY",
                    "parent_node_id": "parent",
                    "direct_child_degrees": [
                        {
                            "label": "a",
                            "degree": "Primary",
                            "degree_status": "RESOLVED",
                            "internal_status": "INTERNALS_CONFIRMED",
                            "parent_label": "parent",
                        },
                        {
                            "label": "b",
                            "degree": None,
                            "degree_status": "DEGREE_UNRESOLVED",
                            "internal_status": "INTERNALS_UNRESOLVED",
                            "parent_label": "parent",
                        },
                    ],
                },
                {
                    "type": "PARENT_CHILD_DEGREE_ADJACENCY",
                    "parent_degree": "Primary",
                    "parent_degree_status": "RESOLVED",
                    "child_degree": "Intermediate",
                    "child_degree_status": "RESOLVED",
                },
                {"type": "P023_VISIBILITY", "visibility_state": "VISIBLE"},
                {
                    "type": "P003_ONE_LARGER_DEGREE_RELATION",
                    "relation": "WITH",
                },
                {"type": "DIRECT_CHILD_CARDINALITY", "behavior": "FLAT"},
            ]
        )
        document["ordered_children"] = [
            {
                "subject_id": f"child-{index}",
                "observation_provenance_ref": f"manual-chart:child-{index}",
            }
            for index in range(3)
        ]
        document["constructed_binding_id"] = "cli-binding"
        request = parse_manual_candidate_document(document)
        expected = (
            ManualP004Wave2OriginFact,
            ManualDegreePeerFact,
            ManualParentChildDegreeFact,
            ManualP023VisibilityFact,
            ManualP003OneLargerDegreeRelationFact,
            ManualDirectChildCardinalityFact,
        )
        self.assertEqual(expected, tuple(type(item) for item in request.manual_behavior_facts))
        p004, peer, parent_child, visibility, relation, cardinality = request.manual_behavior_facts
        self.assertIs(ImpulseDirection.DOWN, p004.direction)
        self.assertIs(DegreeStatus.RESOLVED, peer.direct_child_degrees[0].degree_status)
        self.assertIs(InternalStatus.UNRESOLVED, peer.direct_child_degrees[1].internal_status)
        self.assertIs(DegreeStatus.RESOLVED, parent_child.child_degree_status)
        self.assertIs(request.subject, visibility.subject)
        self.assertIs(P023VisibilityState.VISIBLE, visibility.visibility_state)
        self.assertIs(P003OneLargerDegreeRelation.WITH, relation.relation)
        self.assertIs(ManualCardinalityBehavior.FLAT, cardinality.behavior)
        self.assertEqual(3, len(request.ordered_child_subjects))

    def test_json_values_remain_untrusted_and_authority_fields_are_rejected(self) -> None:
        forbidden = (
            "trusted_invalidity_certificates",
            "observations",
            "operational_resolution",
            "child_binding",
            "final_summary",
            "validator",
            "constructor",
        )
        for field in forbidden:
            with self.subTest(field=field):
                document = base_document()
                document[field] = []
                with self.assertRaisesRegex(ManualCandidateCliError, "unknown fields"):
                    parse_manual_candidate_document(document)

    def test_root_and_nested_unknown_or_missing_fields_fail_closed(self) -> None:
        invalid = []
        missing = base_document()
        del missing["candidate_id"]
        invalid.append(missing)
        extra = base_document()
        extra["extra"] = True
        invalid.append(extra)
        fact_extra = base_document(
            facts=[
                {
                    "type": "P023_VISIBILITY",
                    "visibility_state": "VISIBLE",
                    "direction": "UP",
                }
            ]
        )
        invalid.append(fact_extra)
        subject_extra = base_document()
        subject_extra["subject"]["degree"] = "Primary"
        invalid.append(subject_extra)
        for document in invalid:
            with self.subTest(document=document):
                with self.assertRaises(ManualCandidateCliError):
                    parse_manual_candidate_document(document)

    def test_mapping_subclass_and_mutated_result_fail_closed(self) -> None:
        class MappingSubclass(dict):
            pass

        with self.assertRaises(ManualCandidateCliError):
            parse_manual_candidate_document(MappingSubclass(base_document()))
        request = load_manual_candidate_file(EXAMPLES / "p004_reviewed.json")
        from elliott_methodology_kernel import MethodologyKernel
        from elliott_runtime.manual_candidate_cli import render_non_authoritative_snapshot

        result = MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(
            request
        )
        object.__setattr__(result, "candidate_id", "mutated")
        with self.assertRaises(ManualCandidateCliError):
            render_non_authoritative_snapshot(result)

    def test_wrong_schema_unknown_fact_and_unknown_enum_fail_closed(self) -> None:
        documents = []
        wrong_version = base_document()
        wrong_version["schema_version"] = "FUTURE"
        documents.append(wrong_version)
        documents.append(base_document(facts=[{"type": "INVENTED"}]))
        documents.append(
            base_document(
                facts=[{"type": "P023_VISIBILITY", "visibility_state": "MAYBE"}]
            )
        )
        for document in documents:
            with self.subTest(document=document):
                with self.assertRaises(ManualCandidateCliError):
                    parse_manual_candidate_document(document)

    def test_numeric_strings_booleans_and_nonfinite_values_are_rejected(self) -> None:
        for value in ("100.0", True, float("inf"), float("nan")):
            with self.subTest(value=value):
                document = base_document(
                    facts=[
                        {
                            "type": "P004_WAVE2_ORIGIN",
                            "candidate_scope": "NORMAL_IMPULSE",
                            "direction": "UP",
                            "wave1_origin_price": value,
                            "wave2_end_price": 101,
                        }
                    ]
                )
                with self.assertRaises(ManualCandidateCliError):
                    parse_manual_candidate_document(document)

    def test_exact_json_booleans_and_binding_pairing_are_enforced(self) -> None:
        wrong_bool = base_document()
        wrong_bool["no_rescue_requested"] = 1
        with self.assertRaises(ManualCandidateCliError):
            parse_manual_candidate_document(wrong_bool)
        missing_children = base_document()
        missing_children["constructed_binding_id"] = "binding"
        with self.assertRaises(ManualCandidateCliError):
            parse_manual_candidate_document(missing_children)
        missing_binding = base_document()
        missing_binding["ordered_children"] = []
        with self.assertRaises(ManualCandidateCliError):
            parse_manual_candidate_document(missing_binding)

    def test_duplicate_json_keys_and_nonfinite_json_tokens_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ManualCandidateCliError, "Duplicate"):
                load_manual_candidate_file(duplicate)
            nonfinite = Path(directory) / "nonfinite.json"
            nonfinite.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ManualCandidateCliError, "Non-finite"):
                load_manual_candidate_file(nonfinite)

    def test_invalid_utf8_missing_file_and_size_limit_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            root = Path(directory)
            invalid = root / "invalid.json"
            invalid.write_bytes(b"\xff")
            with self.assertRaisesRegex(ManualCandidateCliError, "UTF-8"):
                load_manual_candidate_file(invalid)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (MAX_INPUT_BYTES + 1))
            with self.assertRaisesRegex(ManualCandidateCliError, "byte limit"):
                load_manual_candidate_file(oversized)
            with self.assertRaisesRegex(ManualCandidateCliError, "Cannot read"):
                load_manual_candidate_file(root / "missing.json")

    def test_cli_runs_end_to_end_and_writes_only_non_authoritative_stdout(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main([str(EXAMPLES / "p004_reviewed.json")])
        self.assertEqual(0, status)
        self.assertEqual("", stderr.getvalue())
        snapshot = json.loads(stdout.getvalue())
        self.assertEqual(SNAPSHOT_SCHEMA_VERSION, snapshot["schema_version"])
        self.assertEqual(ARTIFACT_CLASSIFICATION, snapshot["artifact_classification"])
        self.assertEqual("NON_AUTHORITATIVE_HUMAN_READABLE_SNAPSHOT", snapshot["authority"])
        self.assertEqual("CURRENT_SUPPLIED_SCOPE_REVIEWED", snapshot["final_summary"])
        self.assertFalse(snapshot["reviewed_is_valid"])
        self.assertEqual(10, len(snapshot["methodology_coverage"]))
        self.assertEqual("P004Result", snapshot["traceability"][0]["result_type"])

    def test_cli_cardinality_example_is_unresolved_and_infers_nothing_else(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main([str(EXAMPLES / "cardinality_unresolved.json")])
        snapshot = json.loads(stdout.getvalue())
        self.assertEqual(0, status)
        self.assertEqual("UNRESOLVED", snapshot["final_summary"])
        supplied = [
            item["behavior_id"]
            for item in snapshot["methodology_coverage"]
            if item["state"] == "SUPPLIED_AND_EXECUTED"
        ]
        self.assertEqual(["P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY"], supplied)

    def test_zero_facts_and_requested_missing_certificate_remain_unresolved(self) -> None:
        document = base_document()
        document["no_rescue_requested"] = True
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(0, main([str(path)]))
        snapshot = json.loads(stdout.getvalue())
        self.assertEqual("UNRESOLVED", snapshot["final_summary"])
        self.assertIn("NO_METHODOLOGY_EVALUATIONS_SUPPLIED", snapshot["unresolved_reasons"])
        self.assertIn(
            "MISSING_TRUSTED_STRUCTURAL_INVALIDITY_CERTIFICATE",
            snapshot["unresolved_reasons"],
        )
        no_rescue = next(
            item
            for item in snapshot["methodology_coverage"]
            if item["behavior_id"] == "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE"
        )
        self.assertEqual("BLOCKED_MISSING_TRUSTED_DEPENDENCY", no_rescue["state"])

    def test_error_path_is_machine_readable_and_emits_no_success_output(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main([str(EXAMPLES / "missing.json")])
        self.assertEqual(2, status)
        self.assertEqual("", stdout.getvalue())
        error = json.loads(stderr.getvalue())
        self.assertEqual("INVALID_MANUAL_CANDIDATE_INPUT", error["error"])

    def test_snapshot_cannot_be_reloaded_as_input_or_methodology_authority(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(0, main([str(EXAMPLES / "p004_reviewed.json")]))
        with self.assertRaises(ManualCandidateCliError):
            parse_manual_candidate_document(json.loads(stdout.getvalue()))

    def test_cli_has_no_methodology_dispatch_certificate_or_external_capability(self) -> None:
        source = MODULE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(
            {"socket", "urllib", "requests", "http", "subprocess", "webbrowser"}.isdisjoint(imports)
        )
        forbidden = (
            "_EXECUTION_DISPATCH",
            "_MANUAL_FACT_BUILDERS",
            "certify_structural_invalidity",
            "certify_validated_internal_family",
            "check_p004",
            "TradingView",
            "PREFERRED",
            "ALTERNATIVE",
            "REMOTE",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        for token in ("RSI", "MACD", "Fibonacci"):
            self.assertNotRegex(source, rf"\b{token}\b")
        self.assertIn("analyze_bounded_manual_chart(request)", source)

    def test_cli_has_no_output_file_or_filesystem_write_surface(self) -> None:
        source = MODULE.read_text(encoding="utf-8")
        for token in ("write_text(", "write_bytes(", "open(", "unlink(", "rename(", "replace("):
            self.assertNotIn(token, source)
        self.assertNotIn("--output", source)
        self.assertIn("sys.stdout", source)

    def test_packaging_entrypoint_and_examples_are_present(self) -> None:
        project = (support.RUNTIME_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(
            'elliott-manual-candidate = "elliott_runtime.manual_candidate_cli:main"',
            project,
        )
        self.assertTrue((EXAMPLES / "README.md").is_file())
        self.assertTrue((EXAMPLES / "p004_reviewed.json").is_file())
        self.assertTrue((EXAMPLES / "cardinality_unresolved.json").is_file())


if __name__ == "__main__":
    unittest.main()
