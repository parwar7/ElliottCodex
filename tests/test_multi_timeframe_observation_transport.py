import ast
import copy
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel_package
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.candidate_analysis_envelope as envelope_module
import elliott_methodology_kernel.multi_timeframe_observation_transport as transport_module
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    CandidateScope,
    ImpulseDirection,
    ManualP004Wave2OriginFact,
    ManualP023VisibilityFact,
    MethodologyKernel,
    MultiTimeframeObservationBundle,
    MultiTimeframeObservationTransportError,
    MultiTimeframeObservationTransportRequest,
    MultiTimeframeObservationTransportResult,
    ObservationAssociationRole,
    ObservationResolutionRelation,
    ObservationTransportDiagnosticState,
    OrderedChildBinding,
    P023VisibilityState,
    RecursiveCandidateCompositionRequest,
    SubjectObservationAttachment,
    TIMEFRAME_IS_NOT_DEGREE,
    compare_observation_resolutions,
    has_coarser_observation_data,
    has_finer_observation_data,
)
from elliott_methodology_kernel.models import (
    Bar,
    BarProvenance,
    DataProvenance,
    DataQualityReport,
    MarketType,
    MissingBarInterval,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def bounded_candidate(analyzed_subject: AnalyzedWaveSubject, visibility=None):
    if visibility is None:
        facts = (
            ManualP004Wave2OriginFact(
                CandidateScope.NORMAL_IMPULSE,
                ImpulseDirection.UP,
                100,
                101,
            ),
        )
    else:
        facts = (ManualP023VisibilityFact(analyzed_subject, visibility),)
    return MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(
        BoundedManualChartAnalysisRequest(
            request_id=f"bounded:{analyzed_subject.subject_id}",
            requested_at_utc="2026-09-03T12:00:00Z",
            subject=analyzed_subject,
            candidate_id=f"candidate:{analyzed_subject.subject_id}",
            manual_behavior_facts=facts,
            provenance_refs=(f"candidate:{analyzed_subject.subject_id}",),
        )
    )


def recursive_candidate(parent_subject=None, child_subjects=()):
    parent_subject = parent_subject or subject("tree-parent")
    parent = bounded_candidate(parent_subject)
    children = tuple(bounded_candidate(item) for item in child_subjects)
    binding = OrderedChildBinding(
        "tree-binding",
        parent_subject,
        tuple(item.subject for item in children),
    )
    request = RecursiveCandidateCompositionRequest(
        "tree-composition",
        parent,
        children,
        binding,
        ("tree:explicit",),
    )
    return MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(request)


def observations(
    timeframe: Timeframe,
    *,
    symbol_identity=None,
    resampled=False,
    start_day=1,
    volume=True,
    source="memory",
):
    symbol_identity = symbol_identity or SymbolIdentity(
        "TEST",
        MarketType.OTHER,
        "TEST-EXCHANGE",
        "PROVIDER:TEST",
    )
    bars = (
        Bar(
            datetime(2026, 1, start_day, tzinfo=timezone.utc),
            100.0,
            102.0,
            99.0,
            101.0,
            500.0 if volume else None,
            BarProvenance(1, f"2026-01-{start_day:02d}T00:00:00Z"),
        ),
    )
    provenance = DataProvenance(
        source_type="test",
        source_identifier=source,
        source_sha256=(str(timeframe.resolution_seconds) * 64)[:64],
        source_resolution=timeframe,
        ingested_at_utc="2026-09-03T12:00:00Z",
        resampled=resampled,
        parent_source_hashes=("a" * 64,) if resampled else (),
    )
    quality = DataQualityReport(
        duplicate_timestamps_utc=(),
        missing_intervals=(
            MissingBarInterval("2026-01-01T00:00:00Z", "2026-01-03T00:00:00Z", 1),
        ),
        volume_available=volume,
        volume_complete=volume,
    )
    return NormalizedMarketObservations(
        symbol_identity,
        timeframe,
        bars,
        provenance,
        quality,
    )


def transport_request(tree, bundle, attachments=(), request_id="transport"):
    return MultiTimeframeObservationTransportRequest(
        request_id,
        tree,
        bundle,
        tuple(attachments),
        (f"transport:{request_id}",),
    )


def attach(tree, bundle, attachments=(), request_id="transport"):
    return MethodologyKernel(support.PROTECTED_ROOT).attach_multi_timeframe_observations(
        transport_request(tree, bundle, attachments, request_id)
    )


class MultiTimeframeObservationTransportTests(unittest.TestCase):
    def test_classification_and_timeframe_is_not_degree_constraint(self) -> None:
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", transport_module.ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_OBSERVATION_ASSOCIATION", transport_module.ASSOCIATION_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", transport_module.WORKFLOW_POLICY_CLASSIFICATION)
        self.assertIs(True, TIMEFRAME_IS_NOT_DEGREE)

    def test_exact_bundle_accepts_multiple_timeframes_and_is_immutable(self) -> None:
        symbol_identity = SymbolIdentity("TEST", MarketType.OTHER, "X", "PX:TEST")
        monthly = observations(Timeframe("1M", 2592000), symbol_identity=symbol_identity)
        weekly = observations(Timeframe("1W", 604800), symbol_identity=symbol_identity)
        bundle = MultiTimeframeObservationBundle(
            symbol_identity,
            (monthly, weekly),
            ("bundle:manual",),
        )
        self.assertIs(symbol_identity, bundle.symbol)
        self.assertIs(monthly, bundle.observation_sets[0])
        self.assertIs(weekly, bundle.observation_sets[1])
        self.assertIs(bundle, copy.copy(bundle))
        self.assertIs(bundle, copy.deepcopy(bundle))
        with self.assertRaises(FrozenInstanceError):
            bundle.observation_sets = ()
        with self.assertRaises(TypeError):
            pickle.dumps(bundle)

    def test_mapping_duck_and_observation_subclass_are_rejected(self) -> None:
        class Duck:
            timeframe = Timeframe("1D", 86400)

        class ObservationSubclass(NormalizedMarketObservations):
            pass

        valid = observations(Timeframe("1D", 86400))
        subclass = ObservationSubclass(
            valid.symbol,
            valid.timeframe,
            valid.bars,
            valid.provenance,
            valid.quality,
        )
        for value in ({"timeframe": "1D"}, Duck(), subclass):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(MultiTimeframeObservationTransportError):
                    MultiTimeframeObservationBundle(valid.symbol, (value,))

    def test_same_symbol_uses_exact_existing_field_values(self) -> None:
        bundle_symbol = SymbolIdentity("TEST", MarketType.STOCK, "NYSE", "NYSE:TEST")
        equal_symbol = SymbolIdentity("TEST", MarketType.STOCK, "NYSE", "NYSE:TEST")
        daily = observations(Timeframe("1D", 86400), symbol_identity=equal_symbol)
        bundle = MultiTimeframeObservationBundle(bundle_symbol, (daily,))
        self.assertIs(bundle_symbol, bundle.symbol)
        self.assertIs(equal_symbol, bundle.observation_sets[0].symbol)
        self.assertIsNot(bundle_symbol, equal_symbol)

    def test_symbol_exchange_market_and_provider_mismatches_are_rejected(self) -> None:
        expected = SymbolIdentity("TEST", MarketType.STOCK, "NYSE", "NYSE:TEST")
        mismatches = (
            SymbolIdentity("OTHER", MarketType.STOCK, "NYSE", "NYSE:TEST"),
            SymbolIdentity("TEST", MarketType.OTHER, "NYSE", "NYSE:TEST"),
            SymbolIdentity("TEST", MarketType.STOCK, "NASDAQ", "NYSE:TEST"),
            SymbolIdentity("TEST", MarketType.STOCK, "NYSE", "OTHER:TEST"),
        )
        for index, mismatch in enumerate(mismatches):
            with self.subTest(index=index):
                with self.assertRaises(MultiTimeframeObservationTransportError):
                    MultiTimeframeObservationBundle(
                        expected,
                        (observations(Timeframe(f"T{index}", index + 1), symbol_identity=mismatch),),
                    )

    def test_duplicate_resolution_seconds_is_rejected_without_merge(self) -> None:
        symbol_identity = SymbolIdentity("TEST", MarketType.OTHER)
        first = observations(Timeframe("Daily", 86400), symbol_identity=symbol_identity, source="first")
        second = observations(Timeframe("24H", 86400), symbol_identity=symbol_identity, source="second")
        with self.assertRaises(MultiTimeframeObservationTransportError):
            MultiTimeframeObservationBundle(symbol_identity, (first, second))

    def test_caller_order_is_preserved_and_resolution_inventory_is_deterministic(self) -> None:
        symbol_identity = SymbolIdentity("TEST", MarketType.OTHER)
        monthly = observations(Timeframe("1M", 2592000), symbol_identity=symbol_identity)
        daily = observations(Timeframe("1D", 86400), symbol_identity=symbol_identity)
        weekly = observations(Timeframe("1W", 604800), symbol_identity=symbol_identity)
        bundle = MultiTimeframeObservationBundle(symbol_identity, (monthly, daily, weekly))
        result = attach(recursive_candidate(), bundle)
        self.assertEqual((monthly, daily, weekly), bundle.observation_sets)
        self.assertEqual((daily, weekly, monthly), result.resolution_inventory)
        for expected, actual in zip((daily, weekly, monthly), result.resolution_inventory, strict=True):
            self.assertIs(expected, actual)

    def test_resolution_comparison_is_chart_sampling_only(self) -> None:
        daily = Timeframe("1D", 86400)
        weekly = Timeframe("1W", 604800)
        alias = Timeframe("24H", 86400)
        self.assertIs(ObservationResolutionRelation.FINER_THAN, compare_observation_resolutions(daily, weekly))
        self.assertIs(ObservationResolutionRelation.COARSER_THAN, compare_observation_resolutions(weekly, daily))
        self.assertIs(ObservationResolutionRelation.SAME_RESOLUTION, compare_observation_resolutions(daily, alias))
        self.assertTrue({"degree", "parent_degree", "child_degree"}.isdisjoint(ObservationResolutionRelation.__members__))

    def test_exact_request_and_result_retain_all_live_identities(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1D", 86400))
        bundle = MultiTimeframeObservationBundle(obs.symbol, (obs,))
        attachment = SubjectObservationAttachment(
            tree.parent_node.subject,
            obs,
            ObservationAssociationRole.REFERENCE_VIEW,
            ("attachment:manual",),
        )
        request = transport_request(tree, bundle, (attachment,), "identity")
        result = MethodologyKernel(support.PROTECTED_ROOT).attach_multi_timeframe_observations(request)
        self.assertIs(tree, result.recursive_candidate_result)
        self.assertIs(bundle, result.observation_bundle)
        self.assertIs(request.subject_attachments, result.subject_attachments)
        self.assertIs(attachment, result.subject_attachments[0])
        self.assertIs(obs, result.subject_attachments[0].observations)
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))

    def test_request_result_mapping_duck_subclass_and_pickle_boundaries(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1D", 86400))
        bundle = MultiTimeframeObservationBundle(obs.symbol, (obs,))
        request = transport_request(tree, bundle)
        with self.assertRaises(TypeError):
            type("RequestSubclass", (MultiTimeframeObservationTransportRequest,), {})
        with self.assertRaises(TypeError):
            type("ResultSubclass", (MultiTimeframeObservationTransportResult,), {})
        for value in ({"request_id": request.request_id}, object()):
            with self.assertRaises(MultiTimeframeObservationTransportError):
                MethodologyKernel(support.PROTECTED_ROOT).attach_multi_timeframe_observations(value)
        with self.assertRaises(TypeError):
            pickle.dumps(request)
        with self.assertRaises(TypeError):
            pickle.dumps(attach(tree, bundle))

    def test_attachment_requires_exact_subject_observation_and_role(self) -> None:
        analyzed_subject = subject("attachment")
        obs = observations(Timeframe("1D", 86400))
        valid = SubjectObservationAttachment(
            analyzed_subject,
            obs,
            ObservationAssociationRole.ADDITIONAL_VIEW,
        )
        self.assertIs(analyzed_subject, valid.subject)
        self.assertIs(obs, valid.observations)
        for bad_subject, bad_observation, bad_role in (
            ({"subject_id": "attachment"}, obs, ObservationAssociationRole.ADDITIONAL_VIEW),
            (analyzed_subject, {"bars": []}, ObservationAssociationRole.ADDITIONAL_VIEW),
            (analyzed_subject, obs, "ADDITIONAL_VIEW"),
        ):
            with self.assertRaises(MultiTimeframeObservationTransportError):
                SubjectObservationAttachment(bad_subject, bad_observation, bad_role)

    def test_foreign_subject_and_foreign_observation_are_rejected(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1D", 86400))
        foreign_obs = observations(Timeframe("1W", 604800), symbol_identity=obs.symbol)
        bundle = MultiTimeframeObservationBundle(obs.symbol, (obs,))
        attachments = (
            SubjectObservationAttachment(subject("foreign"), obs, ObservationAssociationRole.REFERENCE_VIEW),
            SubjectObservationAttachment(tree.parent_node.subject, foreign_obs, ObservationAssociationRole.REFERENCE_VIEW),
        )
        for attachment in attachments:
            with self.subTest(subject=attachment.subject.subject_id):
                with self.assertRaises(MultiTimeframeObservationTransportError):
                    transport_request(tree, bundle, (attachment,))

    def test_duplicate_subject_observation_pair_is_rejected(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1D", 86400))
        bundle = MultiTimeframeObservationBundle(obs.symbol, (obs,))
        first = SubjectObservationAttachment(tree.parent_node.subject, obs, ObservationAssociationRole.REFERENCE_VIEW)
        second = SubjectObservationAttachment(tree.parent_node.subject, obs, ObservationAssociationRole.ADDITIONAL_VIEW)
        with self.assertRaises(MultiTimeframeObservationTransportError):
            transport_request(tree, bundle, (first, second))

    def test_same_subject_accepts_multiple_distinct_resolutions(self) -> None:
        tree = recursive_candidate()
        symbol_identity = SymbolIdentity("TEST", MarketType.OTHER)
        daily = observations(Timeframe("1D", 86400), symbol_identity=symbol_identity)
        weekly = observations(Timeframe("1W", 604800), symbol_identity=symbol_identity)
        bundle = MultiTimeframeObservationBundle(symbol_identity, (daily, weekly))
        attachments = (
            SubjectObservationAttachment(tree.parent_node.subject, daily, ObservationAssociationRole.REFERENCE_VIEW),
            SubjectObservationAttachment(tree.parent_node.subject, weekly, ObservationAssociationRole.ADDITIONAL_VIEW),
        )
        result = attach(tree, bundle, attachments)
        states = {item.state for item in result.transport_diagnostics}
        self.assertIn(ObservationTransportDiagnosticState.MULTIPLE_RESOLUTIONS_ATTACHED, states)
        self.assertIn(ObservationTransportDiagnosticState.FINER_RESOLUTION_AVAILABLE, states)
        self.assertIn(ObservationTransportDiagnosticState.COARSER_RESOLUTION_AVAILABLE, states)

    def test_recursive_subject_inventory_contains_only_exact_explicit_tree(self) -> None:
        parent = subject("inventory-parent")
        first = subject("inventory-first")
        second = subject("inventory-second")
        tree = recursive_candidate(parent, (first, second))
        obs = observations(Timeframe("1D", 86400))
        result = attach(tree, MultiTimeframeObservationBundle(obs.symbol, (obs,)))
        self.assertEqual((parent, first, second), result.subject_inventory)
        for expected, actual in zip((parent, first, second), result.subject_inventory, strict=True):
            self.assertIs(expected, actual)
        self.assertEqual(3, len(result.subject_inventory))

    def test_missing_subject_attachment_is_diagnostic_only(self) -> None:
        tree = recursive_candidate(child_subjects=(subject("unattached-child"),))
        obs = observations(Timeframe("1D", 86400))
        result = attach(tree, MultiTimeframeObservationBundle(obs.symbol, (obs,)))
        self.assertTrue(all(item.state is ObservationTransportDiagnosticState.SUBJECT_NO_OBSERVATIONS for item in result.transport_diagnostics))
        self.assertTrue(all(item.reason == "NO_OBSERVATION_ASSOCIATION_SUPPLIED" for item in result.transport_diagnostics))
        self.assertFalse(hasattr(result, "methodology_summary"))
        self.assertFalse(hasattr(result, "validity"))

    def test_finer_and_coarser_helpers_report_only_explicit_attachment_facts(self) -> None:
        tree = recursive_candidate()
        symbol_identity = SymbolIdentity("TEST", MarketType.OTHER)
        four_hour = observations(Timeframe("4H", 14400), symbol_identity=symbol_identity)
        daily = observations(Timeframe("1D", 86400), symbol_identity=symbol_identity)
        weekly = observations(Timeframe("1W", 604800), symbol_identity=symbol_identity)
        bundle = MultiTimeframeObservationBundle(symbol_identity, (daily, weekly, four_hour))
        attached = (
            SubjectObservationAttachment(tree.parent_node.subject, daily, ObservationAssociationRole.REFERENCE_VIEW),
            SubjectObservationAttachment(tree.parent_node.subject, weekly, ObservationAssociationRole.ADDITIONAL_VIEW),
            SubjectObservationAttachment(tree.parent_node.subject, four_hour, ObservationAssociationRole.FINER_RESOLUTION_VIEW),
        )
        result = attach(tree, bundle, attached)
        self.assertTrue(has_finer_observation_data(result, tree.parent_node.subject, daily.timeframe))
        self.assertTrue(has_coarser_observation_data(result, tree.parent_node.subject, daily.timeframe))
        self.assertFalse(has_finer_observation_data(result, tree.parent_node.subject, four_hour.timeframe))
        self.assertFalse(has_coarser_observation_data(result, tree.parent_node.subject, weekly.timeframe))

    def test_finer_data_does_not_change_not_visible_or_invoke_p023(self) -> None:
        analyzed_subject = subject("p023-not-visible")
        parent = bounded_candidate(analyzed_subject, P023VisibilityState.NOT_VISIBLE)
        tree = MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(
            RecursiveCandidateCompositionRequest(
                "p023-tree",
                parent,
                (),
                OrderedChildBinding("p023-binding", analyzed_subject, ()),
            )
        )
        original_result = parent.traceability[0].result_object
        original_state = original_result.result.status
        daily = observations(Timeframe("1D", 86400))
        four_hour = observations(Timeframe("4H", 14400), symbol_identity=daily.symbol)
        bundle = MultiTimeframeObservationBundle(daily.symbol, (daily, four_hour))
        attachment = SubjectObservationAttachment(analyzed_subject, four_hour, ObservationAssociationRole.FINER_RESOLUTION_VIEW)
        result = attach(tree, bundle, (attachment,), "p023-transport")
        self.assertTrue(has_finer_observation_data(result, analyzed_subject, daily.timeframe))
        self.assertIs(original_result, result.recursive_candidate_result.parent_candidate_result.traceability[0].result_object)
        self.assertIs(original_state, original_result.result.status)
        self.assertIs(P023VisibilityState.NOT_VISIBLE, original_result.visibility_state)

    def test_unknown_p023_also_remains_unchanged(self) -> None:
        analyzed_subject = subject("p023-unknown")
        parent = bounded_candidate(analyzed_subject, P023VisibilityState.UNKNOWN)
        tree = MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(
            RecursiveCandidateCompositionRequest(
                "unknown-tree",
                parent,
                (),
                OrderedChildBinding("unknown-binding", analyzed_subject, ()),
            )
        )
        obs = observations(Timeframe("1H", 3600))
        result = attach(
            tree,
            MultiTimeframeObservationBundle(obs.symbol, (obs,)),
            (SubjectObservationAttachment(analyzed_subject, obs, ObservationAssociationRole.FINER_RESOLUTION_VIEW),),
        )
        retained = result.recursive_candidate_result.parent_candidate_result.traceability[0].result_object
        self.assertIs(P023VisibilityState.UNKNOWN, retained.visibility_state)

    def test_data_quality_volume_and_provenance_are_exact_transport_only(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1D", 86400), volume=False)
        bundle = MultiTimeframeObservationBundle(obs.symbol, (obs,))
        result = attach(
            tree,
            bundle,
            (SubjectObservationAttachment(tree.parent_node.subject, obs, ObservationAssociationRole.REFERENCE_VIEW),),
        )
        retained = result.resolution_inventory[0]
        self.assertIs(obs, retained)
        self.assertIs(obs.quality, retained.quality)
        self.assertIs(obs.provenance, retained.provenance)
        self.assertFalse(retained.quality.volume_available)
        self.assertEqual(1, retained.quality.missing_intervals[0].missing_bar_count)

    def test_resampled_flag_is_retained_without_resampling(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1W", 604800), resampled=True)
        result = attach(tree, MultiTimeframeObservationBundle(obs.symbol, (obs,)))
        self.assertIs(obs, result.resolution_inventory[0])
        self.assertIs(True, result.resolution_inventory[0].provenance.resampled)
        self.assertEqual(("a" * 64,), result.resolution_inventory[0].provenance.parent_source_hashes)

    def test_different_date_coverage_is_accepted_without_relationship_inference(self) -> None:
        tree = recursive_candidate()
        symbol_identity = SymbolIdentity("TEST", MarketType.OTHER)
        early = observations(Timeframe("1D", 86400), symbol_identity=symbol_identity, start_day=1)
        late = observations(Timeframe("1W", 604800), symbol_identity=symbol_identity, start_day=20)
        result = attach(tree, MultiTimeframeObservationBundle(symbol_identity, (early, late)))
        self.assertEqual(1, result.observation_bundle.observation_sets[0].bars[0].timestamp_utc.day)
        self.assertEqual(20, result.observation_bundle.observation_sets[1].bars[0].timestamp_utc.day)
        self.assertTrue({"parent_timeframe", "child_timeframe", "date_nesting"}.isdisjoint(MultiTimeframeObservationTransportResult.__dataclass_fields__))

    def test_low_level_bundle_attachment_request_and_result_mutation_fail_closed(self) -> None:
        tree = recursive_candidate()
        obs = observations(Timeframe("1D", 86400))
        bundle = MultiTimeframeObservationBundle(obs.symbol, (obs,))
        attachment = SubjectObservationAttachment(tree.parent_node.subject, obs, ObservationAssociationRole.REFERENCE_VIEW)
        request = transport_request(tree, bundle, (attachment,), "mutation")
        result = MethodologyKernel(support.PROTECTED_ROOT).attach_multi_timeframe_observations(request)
        object.__setattr__(result, "resolution_inventory", ())
        with self.assertRaises(MultiTimeframeObservationTransportError):
            copy.copy(result)
        object.__setattr__(request, "request_id", "changed")
        with self.assertRaises(MultiTimeframeObservationTransportError):
            copy.copy(request)
        object.__setattr__(attachment, "association_role", ObservationAssociationRole.ADDITIONAL_VIEW)
        with self.assertRaises(MultiTimeframeObservationTransportError):
            copy.copy(attachment)
        object.__setattr__(obs.timeframe, "label", "changed")
        with self.assertRaises(MultiTimeframeObservationTransportError):
            copy.copy(bundle)

    def test_result_surface_has_no_methodology_degree_rank_or_trading_fields(self) -> None:
        self.assertEqual(
            {
                "request_id",
                "recursive_candidate_result",
                "observation_bundle",
                "subject_attachments",
                "subject_inventory",
                "resolution_inventory",
                "transport_diagnostics",
                "provenance_refs",
                "_request",
                "_identity_snapshot",
            },
            {item.name for item in fields(MultiTimeframeObservationTransportResult)},
        )
        forbidden = {
            "degree", "validity", "confirmation", "family", "rank", "confidence",
            "trade", "entry", "stop", "target", "alert",
        }
        self.assertTrue(forbidden.isdisjoint(MultiTimeframeObservationTransportResult.__dataclass_fields__))

    def test_no_dynamic_import_callable_provider_resampling_or_interpretation(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "multi_timeframe_observation_transport.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text)
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        }
        self.assertTrue(imported.isdisjoint({"socket", "urllib", "requests", "http", "subprocess", "selenium", "playwright", "tradingview"}))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"eval", "exec", "__import__"}.isdisjoint(calls))
        for forbidden in (
            "check_p023", "check_p004", "certify_", "resample(", "pivot detection",
            "wave detection", "pattern inference", "cross-timeframe confirmation",
            "PREFERRED", "ALTERNATIVE", "TRADE", "STAND_ASIDE",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_no_subject_recursive_child_or_family_authority_is_created(self) -> None:
        parent = subject("authority-parent")
        child = subject("authority-child")
        tree = recursive_candidate(parent, (child,))
        obs = observations(Timeframe("1D", 86400))
        before_node = tree.parent_node
        before_family = (tuple(family_private._PRODUCERS), len(family_private._ISSUED))
        result = attach(tree, MultiTimeframeObservationBundle(obs.symbol, (obs,)))
        self.assertIs(before_node, result.recursive_candidate_result.parent_node)
        self.assertEqual((parent, child), result.subject_inventory)
        self.assertEqual(before_family, (tuple(family_private._PRODUCERS), len(family_private._ISSUED)))

    def test_methodology_and_producer_inventories_remain_exact(self) -> None:
        self.assertEqual(10, len(envelope_module._BEHAVIOR_COMPATIBILITY))
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))
        api_text = (support.SRC / "elliott_methodology_kernel" / "api.py").read_text(encoding="utf-8")
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", api_text)


if __name__ == "__main__":
    unittest.main()
