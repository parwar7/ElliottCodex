"""Deterministic orchestration/reporting tests; never retrieve live Yahoo data."""
import copy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import support
from elliott_methodology_kernel import MethodologyKernel
from test_candidate_generation import market_observations
from test_normal_impulse_partial_evaluation import evaluate
from test_finer_child_observation_selection import finer_observations

spec = importlib.util.spec_from_file_location(
    "nvda_experiment", support.RUNTIME_ROOT / "tools/nvda_post_p005_experiment.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class ExperimentReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate()
        cls.summary = experiment.summarize_partial(cls.result)

    def test_snapshot_roundtrip_preserves_every_transport_field(self):
        observations = market_observations(24)
        payload = json.loads(experiment.encoded(observations))
        replayed = experiment.restore_observations(payload)
        self.assertIsNot(replayed, observations)
        self.assertEqual(observations, replayed)
        self.assertEqual(experiment.encoded(observations), experiment.encoded(replayed))
        for before, after in zip(observations.bars, replayed.bars):
            self.assertEqual(before.high.as_integer_ratio(), after.high.as_integer_ratio())

    def test_configuration_keeps_prior_normal_impulse_bounds_explicit(self):
        config = experiment.configuration()
        self.assertEqual((6, 6, 0, 10), tuple(config['parent'][name] for name in
            ('max_pivots_considered', 'max_candidate_span_pivots', 'max_skipped_pivots', 'max_candidates_generated')))
        self.assertEqual(500, config['child']['max_total_child_candidates'])
        self.assertEqual(1, config['automatic_child_levels'])
        self.assertEqual((('1mo', '1wk'), ('1wk', '1d'), ('1d', '1h')), experiment.PAIRS)

    def test_reports_live_outcomes_and_identity_without_family_authority(self):
        summary = self.summary
        self.assertEqual(len(self.result.evaluations), summary['hypotheses'])
        experiment.audit_summary(summary)
        for item, trace in zip(self.result.evaluations, summary['traces']):
            self.assertEqual(item.p005_result.reason, trace['p005_reason'])
            self.assertEqual(item.p004_result.status.value, trace['p004_status'])
            self.assertEqual(6, len(trace['endpoints']))
            self.assertFalse(trace['family_validity_authority'])
            self.assertTrue(trace['exact_runtime_identity_checks_passed'])
            self.assertEqual(['1', '1', '3', '3', '5', '5'], [e['role'] for e in trace['endpoints']])

    def test_reporting_is_deterministic_for_the_same_live_result(self):
        self.assertEqual(experiment.encoded(self.summary), experiment.encoded(experiment.summarize_partial(self.result)))

    def test_summary_count_tampering_is_rejected(self):
        for key in ('hypotheses', 'p004_certificates', 'p004_invalid_despite_p005_sufficiency'):
            broken = copy.deepcopy(self.summary)
            broken[key] += 1
            with self.assertRaises(ValueError):
                experiment.audit_summary(broken)

    def test_unresolved_reason_tampering_is_rejected(self):
        broken = copy.deepcopy(self.summary)
        broken['p005_unresolved_reasons']['INVENTED'] = 1
        with self.assertRaises(ValueError):
            experiment.audit_summary(broken)

    def test_fabricated_family_validity_is_rejected(self):
        broken = copy.deepcopy(self.summary)
        broken['traces'][0]['family_validity_authority'] = True
        with self.assertRaises(ValueError):
            experiment.audit_summary(broken)

    def test_output_is_write_once_and_workspace_bounded(self):
        with TemporaryDirectory(dir=support.RUNTIME_ROOT) as directory:
            target = Path(directory) / 'record.json'
            entry = experiment.write_new(target, {'value': 0.1})
            self.assertEqual(entry['sha256'], experiment.sha(target.read_bytes()))
            with self.assertRaises(FileExistsError):
                experiment.write_new(target, {})
        with self.assertRaises(ValueError):
            experiment.write_new(support.RUNTIME_ROOT.parent / 'must-not-exist.json', {})

    def test_tampered_snapshot_rejected_before_reconstruction(self):
        with TemporaryDirectory(dir=support.RUNTIME_ROOT) as directory:
            folder = Path(directory)
            entry = experiment.write_new(folder / 'snapshot.json', {})
            entry['sha256'] = '0' * 64
            experiment.write_new(folder / 'input_manifest.json', {
                'kind': 'FRESH_YAHOO_NORMALIZED_SNAPSHOTS', 'files': [entry]})
            with self.assertRaisesRegex(ValueError, 'hash/length'):
                experiment.load_inputs(folder)

    def test_failed_provider_is_not_reported_as_success_or_synthetic_nvda(self):
        with TemporaryDirectory(dir=support.RUNTIME_ROOT) as directory:
            folder = Path(directory)
            with patch.object(experiment.YahooFinanceProvider, 'fetch', side_effect=ValueError('recorded test provider failure')):
                code = experiment.main(['--capture', '--inputs', str(folder / 'inputs'),
                                        '--output', str(folder / 'failure.json')])
            report = json.loads((folder / 'failure.json').read_bytes())
            self.assertEqual(1, code)
            self.assertEqual('INCOMPLETE', report['status'])
            self.assertEqual([], report['scopes'])
            self.assertIn('recorded test provider failure', report['failure']['message'])
            self.assertFalse((folder / 'inputs/input_manifest.json').exists())

    def test_pipeline_uses_real_public_factories_with_synthetic_test_data(self):
        parent = market_observations(24)
        finer = finer_observations(parent, seconds=21600)
        with patch.object(experiment.YahooFinanceProvider, 'fetch', side_effect=AssertionError('No test network')):
            result = experiment.run_scope(parent, finer, MethodologyKernel(support.PROTECTED_ROOT),
                                          '2026-09-06T00:00:00Z', lambda stage: None)
        self.assertEqual(0, result['requirements_satisfied'])
        self.assertFalse(result['search_exhaustive'])
        self.assertEqual(len(result['requirements']), sum(result['coverage_counts'].values()))
        experiment.audit_summary(result['parent'])
        experiment.audit_summary(result['child'])


if __name__ == '__main__':
    unittest.main()
