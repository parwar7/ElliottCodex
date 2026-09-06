"""Deterministic reporting tests: genuine factories over a preserved snapshot.

No provider calls. The old immutable NVDA capture is replay input, not a source
of deserialized methodology authority; all live results are newly evaluated.
"""
import copy
import csv
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import support
sys.path.insert(0, str(support.RUNTIME_ROOT / "tools"))
import nvda_bounded_report as report
import audit_nvda_bounded_report as auditor
from elliott_methodology_kernel import MethodologyKernel
from test_normal_impulse_partial_evaluation import evaluate

INPUTS = support.RUNTIME_ROOT / "kernel_reviews/NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1/inputs"


class BoundedReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest, data = report.pipeline.load_inputs(INPUTS)
        collected = []
        with patch.object(report.pipeline.YahooFinanceProvider, "fetch", side_effect=AssertionError("No network in tests")):
            scope = report.pipeline.run_scope(data["1mo"], data["1wk"],
                MethodologyKernel(support.PROTECTED_ROOT), manifest["requested_at_utc"], lambda _: None,
                observe_results=lambda *objects: collected.append(report.collect_live(*objects, "1mo")))
        evidence = collected[0]
        cls.document = {"stage": report.STAGE, "data": report.data_notes(INPUTS, manifest, data, "OFFLINE_REPLAY"),
            "scopes": [scope], "hypotheses": evidence.pop("hypotheses"),
            "internal_links": [{"parent_scope": "1mo", **evidence}], "authority": dict(report.AUTHORITY)}
        cls.document["groups"] = report.group_rows(cls.document["hypotheses"])
        report.assign_display_refs(cls.document)
        cls.document["audit"] = report.audit_document(cls.document)
        cls.manifest, cls.datasets = manifest, data

    def test_actual_public_results_map_to_report_totals(self):
        audit = report.audit_document(self.document)
        self.assertEqual(len(self.document["hypotheses"]), audit["hypothesis_rows"])
        self.assertGreater(audit["hypothesis_rows"], 0)

    def test_p004_rejection_cannot_be_rescued_by_genuine_p005_sufficiency(self):
        rows = [r for r in self.document["hypotheses"] if r["p004"] and r["p004"]["fatal"]
                and r["p005"]["status"] == "SUFFICIENT_CONDITION_ESTABLISHED"]
        self.assertGreater(len(rows), 0, "Fixture must exercise actual non-rescue")
        self.assertTrue(all(r["report_status"] == "REJECTED_EXACT_HYPOTHESIS_P004" for r in rows))

    def test_rejection_is_hypothesis_local_not_other_families(self):
        rows = self.document["hypotheses"]
        rejected = next(r for r in rows if r["p004"] and r["p004"]["fatal"])
        # Same physical sequence may remain under other exact hypotheses.
        siblings = [r for r in rows if r["group_id"] == rejected["group_id"] and r["p004"] is None]
        self.assertGreater(len(siblings), 0)
        self.assertTrue(all(r["p004"] is None for r in siblings))
        self.assertTrue(all(not r["authority"]["family_validity"] for r in siblings))

    def test_sufficiency_and_cardinality_never_claim_completion_or_family_validity(self):
        self.assertTrue(all(r["authority"] == report.AUTHORITY for r in self.document["hypotheses"]))
        self.assertIn("no complete validated Elliott count", report.render_markdown(self.document))

    def test_duplicate_sequences_preserve_all_originating_links(self):
        duplicated = [g for g in self.document["groups"] if len(g["hypothesis_ids"]) > 1]
        self.assertGreater(len(duplicated), 0)
        for g in duplicated:
            self.assertEqual(g["hypothesis_ids"], [x["hypothesis_id"] for x in g["requirement_links"]])
        self.assertEqual(len(self.document["hypotheses"]),
                         sum(len(g["requirement_links"]) for g in self.document["groups"]))

    def test_grouping_does_not_merge_distinct_snapshot_identity(self):
        rows = copy.deepcopy(self.document["hypotheses"][:2])
        self.assertEqual(1, len(report.group_rows(rows)))
        rows[1]["snapshot_content_sha256"] = "different-report-snapshot"
        self.assertEqual(2, len(report.group_rows(rows)))

    def test_missing_link_and_false_authority_fail_audit(self):
        for mutation in ("link", "authority", "rejection", "total"):
            doc = copy.deepcopy(self.document)
            if mutation == "link":
                doc["groups"][0]["requirement_links"].pop()
            elif mutation == "authority":
                doc["hypotheses"][0]["authority"]["family_validity"] = True
            elif mutation == "rejection":
                row = next(r for r in doc["hypotheses"] if r["p004"] and r["p004"]["fatal"])
                row["report_status"] = "PARTIAL_REVIEW_UNRESOLVED_FAMILY"
            else:
                doc["scopes"][0]["parent_family_hypotheses"] += 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                report.audit_document(doc)

    def test_internal_partial_coverage_never_satisfies_requirement(self):
        requirements = self.document["scopes"][0]["requirements"]
        self.assertGreater(len(requirements), 0)
        self.assertTrue(all(r["requirement_satisfied"] is False for r in requirements))
        scopes = self.document["internal_links"][0]["child_family_scopes"]
        self.assertTrue(any(r["blockers"] or r["unavailable_source_families"] for r in scopes))

    def test_missing_unavailable_family_evaluations_are_not_fabricated(self):
        scopes = self.document["internal_links"][0]["child_family_scopes"]
        self.assertGreater(len(scopes), 0)
        self.assertIn("SOURCE_DERIVED_BASE_CASE_NOT_FOUND", str(self.document))
        generic = [r for r in self.document["hypotheses"] if r["p004"] is None]
        self.assertTrue(all(r["p005"] is None and r["checks"] for r in generic))

    def test_five_slot_display_not_starved_by_three_slot_enumeration_order(self):
        selected = list(report.display_groups(self.document))
        by_id = {r["hypothesis_id"]: r for r in self.document["hypotheses"]}
        for path in ("parent", "child"):
            shapes = {by_id[g["hypothesis_ids"][0]]["candidate_shape"] for g in selected
                      if by_id[g["hypothesis_ids"][0]]["path"] == path}
            self.assertIn("FIVE_SEGMENT_HYPOTHESIS", shapes)
            self.assertLessEqual(len(shapes), report.DISPLAY_GROUPS_PER_PATH)

    def test_capture_time_separate_from_latest_bar(self):
        for note in self.document["data"]["datasets"]:
            self.assertNotEqual(note["actual_capture_time_utc"], note["latest_bar_timestamp_utc"])
            self.assertEqual("2026-09-05", note["actual_capture_time_utc"][:10])
        md = report.render_markdown(self.document)
        self.assertIn("Actual capture UTC", md)
        self.assertIn("Latest bar UTC", md)

    def test_stale_fallback_must_record_reason_and_original_capture(self):
        note = report.data_notes(INPUTS, self.manifest, self.datasets, "STALE_FALLBACK", "Yahoo request failed")
        doc = copy.deepcopy(self.document)
        doc["data"] = note
        md = report.render_markdown(doc)
        self.assertIn("Older preserved data", md)
        self.assertIn("Yahoo request failed", md)
        self.assertIn("2026-09-05", md)
        with self.assertRaises(ValueError):
            report.data_notes(INPUTS, self.manifest, self.datasets, "STALE_FALLBACK")
        with self.assertRaises(ValueError):
            report.data_notes(INPUTS, self.manifest, self.datasets, "FRESH_CAPTURE", "failure")

    def test_exports_and_markdown_reconcile_counts_and_exact_endpoints(self):
        exports = report.evidence_exports(self.document)
        candidates = list(csv.DictReader(io.StringIO(exports["candidates.csv"])))
        endpoints = list(csv.DictReader(io.StringIO(exports["endpoints.csv"])))
        audit = report.audit_document(self.document)
        self.assertEqual(audit["hypothesis_rows"], len(candidates))
        self.assertEqual(audit["endpoint_rows"], len(endpoints))
        md = report.render_markdown(self.document)
        self.assertIn(f"candidates.csv: {len(candidates)} rows", md)
        for raw, exported in zip((e for r in self.document["hypotheses"] for e in r["endpoints"]), endpoints):
            self.assertEqual(raw["price"], float(exported["price"]))
            self.assertEqual(raw["timestamp_utc"], exported["timestamp_utc"])
            self.assertEqual(raw["represented_ratio"], json.loads(exported["represented_ratio"]))

    def test_rendering_is_deterministic_and_does_not_change_evidence(self):
        before = report.pipeline.encoded(self.document)
        a = report.render_markdown(self.document), report.evidence_exports(self.document)
        b = report.render_markdown(json.loads(before)), report.evidence_exports(json.loads(before))
        self.assertEqual(a, b)
        self.assertEqual(before, report.pipeline.encoded(self.document))

    def test_mapping_or_mutated_authority_not_accepted_by_live_adapter(self):
        with self.assertRaises(ValueError):
            report.normal_rows({}, "parent", "1d")
        live = evaluate()
        h = live.evaluations[0].hypothesis
        old = h.five_slot_view.binding.parent_subject
        object.__setattr__(h.five_slot_view.binding, "parent_subject", None)
        try:
            with self.assertRaises(ValueError):
                report.normal_rows(live, "parent", "1d")
        finally:
            object.__setattr__(h.five_slot_view.binding, "parent_subject", old)

    def test_workspace_write_once_and_no_overwrite(self):
        with TemporaryDirectory(dir=support.RUNTIME_ROOT) as folder:
            p = Path(folder) / "report.md"
            report.write_bytes_new(p, b"test")
            with self.assertRaises(FileExistsError):
                report.write_bytes_new(p, b"replacement")
        with self.assertRaises(ValueError):
            report.write_bytes_new(support.PROTECTED_ROOT / "must-not-write.txt", b"test")

    def test_independent_saved_observation_and_artifact_audit(self):
        with TemporaryDirectory(dir=support.RUNTIME_ROOT) as folder:
            folder = Path(folder)
            report.pipeline.write_new(folder / "market_report.json", {
                **self.document, "kind": "BOUNDED_NON_CERTIFYING_REPORT"})
            report.write_bytes_new(folder / "market_report.md", report.render_markdown(self.document).encode())
            for name, content in report.evidence_exports(self.document).items():
                report.write_bytes_new(folder / name, content.encode())
            checked = auditor.audit(folder)
            self.assertEqual(self.document["audit"]["endpoint_rows"], checked["all_saved_endpoint_prices_verified"])

    def test_audit_rejects_report_price_not_present_in_saved_bars(self):
        with TemporaryDirectory(dir=support.RUNTIME_ROOT) as folder:
            bad = copy.deepcopy(self.document)
            bad["kind"] = "BOUNDED_NON_CERTIFYING_REPORT"
            bad["hypotheses"][0]["endpoints"][0]["price"] += 1
            report.pipeline.write_new(Path(folder) / "market_report.json", bad)
            with self.assertRaisesRegex(ValueError, "Endpoint price"):
                auditor.audit(folder)


if __name__ == "__main__":
    unittest.main()
