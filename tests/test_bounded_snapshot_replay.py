"""Synthetic deterministic replay/report tests. No live market retrieval."""
import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import support
sys.path.insert(0, str(support.RUNTIME_ROOT / "tools"))
import bounded_snapshot_replay as replay
from elliott_methodology_kernel import MethodologyKernel
from test_candidate_generation import market_observations
from test_finer_child_observation_selection import finer_observations


class SnapshotMembershipTests(unittest.TestCase):
    def setUp(self):
        self.source = market_observations(24)

    def test_cutoff_is_inclusive_and_later_bars_are_excluded(self):
        cutoff = self.source.bars[12].timestamp_utc
        data, derivation = replay.subset_observations(self.source, cutoff)
        self.assertEqual(13, len(data.bars))
        self.assertEqual(cutoff, data.bars[-1].timestamp_utc)
        self.assertEqual(11, derivation["excluded_later_bar_count"])
        self.assertEqual([b.provenance.source_record_index for b in self.source.bars[:13]],
                         derivation["source_record_indices"])
        before, _ = replay.subset_observations(self.source, cutoff - timedelta(microseconds=1))
        self.assertEqual(12, len(before.bars))

    def test_original_capture_provenance_and_prices_preserved_separate_from_subset_hash(self):
        original = replay.prior.encoded(self.source)
        data, record = replay.subset_observations(self.source, self.source.bars[12].timestamp_utc)
        self.assertEqual(self.source.provenance, data.provenance)
        self.assertEqual(self.source.bars[:13], data.bars)
        self.assertEqual(original, replay.prior.encoded(self.source))
        self.assertNotEqual(data.provenance.source_sha256, record["derived_observation_transport_sha256"])
        self.assertFalse(data.provenance.resampled)
        self.assertIn("NOT a Yahoo", record["hash_boundary"])

    def test_each_subset_has_fresh_objects_but_identical_content(self):
        cutoff = self.source.bars[-1].timestamp_utc
        a, ar = replay.subset_observations(self.source, cutoff)
        b, br = replay.subset_observations(self.source, cutoff)
        self.assertIsNot(a, b)
        self.assertIsNot(a.provenance, b.provenance)
        self.assertTrue(all(x is not y for x, y in zip(a.bars, b.bars)))
        self.assertEqual(ar, br)
        self.assertEqual(replay.prior.encoded(a), replay.prior.encoded(b))

    def test_naive_and_non_utc_cutoffs_fail_closed(self):
        for value in (datetime(2024, 1, 2), "2024-01-02T00:00:00+01:00", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replay.subset_observations(self.source, value)

    def test_empty_membership_fails_instead_of_fabricating_input(self):
        with self.assertRaisesRegex(ValueError, "no observations"):
            replay.subset_observations(self.source, "2000-01-01T00:00:00+00:00")

    def test_unordered_or_duplicate_input_not_silently_normalized(self):
        for bars in (self.source.bars[::-1], self.source.bars[:1] + self.source.bars):
            with self.assertRaisesRegex(ValueError, "Strictly increasing"):
                replay.subset_observations(replace(self.source, bars=bars), self.source.bars[-1].timestamp_utc)

    def test_mapping_and_subclass_rejected(self):
        class Lookalike(type(self.source)):
            pass
        for source in (replay.prior.plain(self.source), Lookalike(self.source.symbol, self.source.timeframe,
                self.source.bars, self.source.provenance, self.source.quality)):
            with self.assertRaisesRegex(ValueError, "Exact normalized"):
                replay.subset_observations(source, self.source.bars[-1].timestamp_utc)

    def test_cutoff_plan_is_calendar_selection_not_outcome_selection(self):
        plan = replay.make_plan({"requested_at_utc": "2026-09-05T09:09:19+00:00"})
        self.assertEqual(["2026-07-31T23:59:59+00:00", "2026-08-31T23:59:59+00:00",
                          "2026-09-05T09:09:19+00:00"], plan["cutoffs_utc"])
        self.assertEqual(9, plan["budget"]["scope_evaluations"])
        self.assertEqual(1, plan["budget"]["child_levels"])
        self.assertEqual(replay.prior.configuration(), plan["pipeline_bounds"])
        self.assertIn("NOT a lookahead-free", plan["caveat"])
        self.assertFalse(plan["network_retrieval"])

    def test_quality_diagnostics_are_bounded_without_invented_calendar(self):
        data, _ = replay.subset_observations(self.source, self.source.bars[12].timestamp_utc)
        stamps = {b.timestamp_utc.isoformat() for b in data.bars}
        self.assertTrue(all(g.after_timestamp_utc in stamps and g.before_timestamp_utc in stamps for g in data.quality.missing_intervals))
        self.assertTrue(data.quality.volume_available and data.quality.volume_complete)


class FreshPipelineReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = market_observations(24)
        cls.finer = finer_observations(cls.parent, seconds=3600)
        cls.source_hashes = [replay.prior.sha(replay.prior.encoded(d)) for d in (cls.parent, cls.finer)]
        cls.live = []
        original_summary = replay.prior.summarize_partial
        def record_live(result):
            cls.live.append(result)
            return original_summary(result)
        datasets = {"1d": cls.parent, "3600s": cls.finer}
        with patch.object(replay.prior, "PAIRS", (("1d", "3600s"),)), \
             patch.object(replay.prior, "summarize_partial", side_effect=record_live), \
             patch.object(replay.prior.YahooFinanceProvider, "fetch", side_effect=AssertionError("No live test data")):
            kernel = MethodologyKernel(support.PROTECTED_ROOT)
            cutoff = cls.parent.bars[-1].timestamp_utc
            cls.first = replay.run_cutoff(datasets, cutoff, kernel, lambda _: None)
            cls.first_bytes = replay.prior.encoded(cls.first)
            cls.second = replay.run_cutoff(datasets, cutoff, kernel, lambda _: None)

    def test_replay_is_deterministic_and_earlier_results_and_sources_unchanged(self):
        self.assertEqual(self.first_bytes, replay.prior.encoded(self.first))
        self.assertEqual(self.first_bytes, replay.prior.encoded(self.second))
        self.assertEqual(self.source_hashes, [replay.prior.sha(replay.prior.encoded(d)) for d in (self.parent, self.finer)])

    def test_fresh_parent_and_child_authority_is_issued_for_each_replay(self):
        self.assertEqual(4, len(self.live))
        for old, new in zip(self.live[:2], self.live[2:]):
            self.assertGreater(len(old.evaluations), 0)
            self.assertIsNot(old, new)
            for a, b in zip(old.evaluations, new.evaluations):
                self.assertIsNot(a.p005_input.observation_binding, b.p005_input.observation_binding)
                self.assertIsNot(a.hypothesis.five_slot_view.binding, b.hypothesis.five_slot_view.binding)
                self.assertIsNot(a.p005_input.observation_binding.observation_snapshot,
                                 b.p005_input.observation_binding.observation_snapshot)
                self.assertIsNot(a.p004_result, b.p004_result)
                self.assertIsNot(a.p005_result, b.p005_result)

    def test_existing_validators_reject_cross_snapshot_evidence_substitution_both_paths(self):
        for old, new in zip(self.live[:2], self.live[2:]):
            a, b = old.evaluations[0], new.evaluations[0]
            original = a.p005_input.observation_binding
            try:
                object.__setattr__(a.p005_input, "observation_binding", b.p005_input.observation_binding)
                with self.assertRaises(ValueError):
                    a.p005_input.validated()
                with self.assertRaises(ValueError):
                    replay.prior.validate_normal_impulse_partial_evaluation_result(old)
            finally:
                object.__setattr__(a.p005_input, "observation_binding", original)
            replay.prior.validate_normal_impulse_partial_evaluation_result(old)

    def test_all_outcomes_reconcile_without_p004_rescue_or_family_proof(self):
        fatal = 0
        for scope in self.first["scopes"]:
            self.assertEqual(len(scope["requirements"]), sum(scope["coverage_counts"].values()))
            self.assertEqual(0, scope["requirements_satisfied"])
            for path in ("parent", "child"):
                summary = scope[path]
                replay.prior.audit_summary(summary)
                fatal += summary["p004_certificates"]
                for trace in summary["traces"]:
                    if trace["p004_fatal"]:
                        self.assertTrue(trace["p004_certificate_origin_identity"])
                        self.assertEqual("P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS", trace["partial_state"])
                    self.assertFalse(trace["family_validity_authority"])
        self.assertGreater(fatal, 0)

    def test_same_sequences_are_comparable_without_confirmation(self):
        old, new = self.first["scopes"][0], self.second["scopes"][0]
        for path in ("parent", "child"):
            result = replay.compare_scopes(old, new, path)
            self.assertEqual([], result["added_sequences"])
            self.assertEqual([], result["disappeared_sequences"])
            self.assertEqual(0, result["comparable_eligibility_changes"])
            self.assertEqual(0, result["confirmation_count"])
            self.assertGreater(len(result["matches"]), 0)

    def test_reporting_replacement_is_not_eligibility_transition(self):
        old = self.first["scopes"][0]
        new = copy.deepcopy(old)  # Report-only perturbation, not fake authority.
        new["parent"]["traces"][0]["endpoints"][-1]["timestamp_utc"] = "2030-01-01T00:00:00+00:00"
        result = replay.compare_scopes(old, new, "parent")
        self.assertEqual(1, len(result["added_sequences"]))
        self.assertEqual(1, len(result["disappeared_sequences"]))
        self.assertEqual([], result["matches"])
        self.assertTrue(result["replacement_or_membership_change"])
        self.assertEqual(0, result["comparable_eligibility_changes"])

    def test_reporting_same_sequence_eligibility_change_is_separate(self):
        old = self.first["scopes"][0]
        new = copy.deepcopy(old)
        edge = new["parent"]["traces"][0]["endpoints"][-1]
        edge["eligible"] = not edge["eligible"]
        result = replay.compare_scopes(old, new, "parent")
        self.assertEqual(1, result["comparable_eligibility_changes"])
        self.assertFalse(result["replacement_or_membership_change"])
        self.assertEqual(0, result["confirmation_count"])

    def test_duplicate_requirements_are_not_independent_confirmations(self):
        scope = copy.deepcopy(self.first["scopes"][0])
        trace = copy.deepcopy(scope["child"]["traces"][0])
        req = copy.deepcopy(next(r for r in scope["requirements"] if r["requirement_id"] == trace["child_requirement_id"]))
        req["requirement_id"] += ":report-duplicate"
        req["child_index"] += 100  # Different report context, identical endpoints.
        trace["child_requirement_id"] = req["requirement_id"]
        before = replay.compare_scopes(scope, scope, "child")
        scope["requirements"].append(req)
        scope["child"]["traces"].append(trace)
        after = replay.compare_scopes(scope, scope, "child")
        self.assertEqual(before["same_sequence_count"], after["same_sequence_count"])
        self.assertEqual(before["after_duplicate_sequence_evaluations"] + 1, after["after_duplicate_sequence_evaluations"])
        self.assertEqual(0, after["confirmation_count"])

    def test_ambiguous_factual_contexts_are_not_forced_into_matches(self):
        scope = copy.deepcopy(self.first["scopes"][0])
        scope["parent"]["traces"].append(copy.deepcopy(scope["parent"]["traces"][0]))
        result = replay.compare_scopes(scope, scope, "parent")
        self.assertEqual([], result["matches"])
        self.assertEqual(1, len(result["ambiguous_factual_contexts_not_matched"]))

    def test_window_coverage_changes_are_reported_separately(self):
        old = self.first["scopes"][0]
        new = copy.deepcopy(old)
        new["requirements"][0]["bars"] += 1
        changes = replay.compare_coverage(old, new)
        self.assertEqual(1, len(changes["changes"]))
        self.assertEqual(0, changes["added_window_contexts"])

    def test_report_tampering_fails_existing_total_audit(self):
        broken = copy.deepcopy(self.first["scopes"][0]["parent"])
        broken["p004_invalid_despite_p005_sufficiency"] += 1
        with self.assertRaises(ValueError):
            replay.prior.audit_summary(broken)


if __name__ == "__main__":
    unittest.main()
