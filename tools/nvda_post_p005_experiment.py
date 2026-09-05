"""Replayable bounded operational experiment; no Elliott rules or certificates.

Run with PYTHONPATH=src. Capture uses only the existing Yahoo public provider.
Replay reconstructs factual observations, never serialized methodology authority.
All identities are freshly established through the public pipeline on each run.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import traceback

from elliott_methodology_kernel import (
    AnalyzedWaveSubject, MethodologyKernel, MultiTimeframeObservationBundle,
    MultiTimeframeObservationTransportRequest, OrderedChildBinding,
    RecursiveCandidateCompositionRequest,
)
from elliott_methodology_kernel.models import (
    Bar, BarProvenance, DataProvenance, DataQualityReport, MarketType,
    MissingBarInterval, NormalizedMarketObservations, SymbolIdentity, Timeframe,
)
from elliott_runtime.market_data.yahoo import (
    YahooFinanceProvider, YahooHistoricalDataRequest, YahooInterval,
)
from elliott_runtime.market_data.geometric_pivots import (
    EqualExtremePolicy, GeometricPivotDiscoveryConfig, GeometricPivotDiscoveryMethod,
    GeometricPivotDiscoveryRequest, discover_geometric_pivots,
)
from elliott_runtime.analysis.candidate_generation import (
    CandidateGenerationConfig, CandidateGenerationRequest, CandidateHypothesisShape,
    CandidatePivotWindow, generate_candidate_hypotheses,
)
from elliott_runtime.analysis.competing_candidates import (
    CompetingCandidateSetRequest, build_competing_candidate_set,
)
from elliott_runtime.analysis.family_hypotheses import (
    FamilyEvaluationKind, FamilyHypothesisBridgeRequest, build_family_evaluation_hypotheses,
)
from elliott_runtime.analysis.family_internal_subdivisions import (
    FamilyInternalSubdivisionEvaluationRequest, evaluate_family_internal_subdivisions,
)
from elliott_runtime.analysis.finer_child_observation_selection import (
    ChildObservationSelectionConfig, ChildObservationSelectionRequest,
    select_finer_child_observations,
)
from elliott_runtime.analysis.recursive_child_candidate_generation import (
    ChildCandidateGenerationConfig, ProposedChildEvaluationWindow,
    RecursiveChildCandidateGenerationRequest, generate_child_candidate_evidence,
)
from elliott_runtime.analysis.recursive_child_family_evaluation import (
    ChildFamilyEvaluationConfig, RecursiveChildFamilyEvaluationRequest,
    evaluate_recursive_child_family_hypotheses,
)
from elliott_runtime.analysis.normal_impulse_partial_evaluation import (
    NormalImpulsePartialEvaluationRequest, evaluate_normal_impulse_partial_scope,
    validate_normal_impulse_partial_evaluation_result,
)

ROOT = Path(__file__).resolve().parents[1]
STAGE = "NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1"
SHAPES = tuple(CandidateHypothesisShape)
PAIRS = (("1mo", "1wk"), ("1wk", "1d"), ("1d", "1h"))


def plain(value):
    """Factual/report JSON only, not an authority serialization mechanism."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)
                if not f.name.startswith("_")}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    return value


def encoded(value):
    # Python's finite float repr round-trips the same represented binary value.
    return (json.dumps(plain(value), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, value):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise ValueError("Experiment output must stay inside Runtime_WORKSPACE")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = encoded(value)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": path.name, "sha256": sha(raw), "byte_length": len(raw)}


def restore_observations(record):
    """Reconstruct only the existing factual transport types, preserving values."""
    symbol = dict(record["symbol"])
    symbol["market_type"] = MarketType(symbol["market_type"])
    timeframe = Timeframe(**record["timeframe"])
    provenance = dict(record["provenance"])
    provenance["source_resolution"] = Timeframe(**provenance["source_resolution"])
    provenance["parent_source_hashes"] = tuple(provenance["parent_source_hashes"])
    quality = dict(record["quality"])
    quality["duplicate_timestamps_utc"] = tuple(quality["duplicate_timestamps_utc"])
    quality["missing_intervals"] = tuple(MissingBarInterval(**v) for v in quality["missing_intervals"])
    bars = tuple(Bar(datetime.fromisoformat(v["timestamp_utc"]), v["open"], v["high"],
                     v["low"], v["close"], v["volume"], BarProvenance(**v["provenance"]))
                 for v in record["bars"])
    result = NormalizedMarketObservations(SymbolIdentity(**symbol), timeframe, bars,
                                          DataProvenance(**provenance), DataQualityReport(**quality))
    if encoded(result) != encoded(record):
        raise ValueError("Observation replay changed the recorded transport values")
    return result


def load_inputs(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / "input_manifest.json").read_bytes())
    if manifest["kind"] != "FRESH_YAHOO_NORMALIZED_SNAPSHOTS":
        raise ValueError("Unexpected input snapshot kind")
    datasets = {}
    for entry in manifest["files"]:
        path = (folder / entry["path"]).resolve()
        if not path.is_relative_to(folder):
            raise ValueError("Snapshot path escapes input folder")
        raw = path.read_bytes()
        if sha(raw) != entry["sha256"] or len(raw) != entry["byte_length"]:
            raise ValueError("Snapshot hash/length mismatch")
        payload = json.loads(raw)
        obs = restore_observations(payload["observations"])
        if obs.symbol.symbol != "NVDA" or obs.timeframe.label in datasets:
            raise ValueError("Wrong instrument or duplicate snapshot")
        if obs.provenance.resampled or obs.provenance.source_type != "yahoo_finance_chart_api":
            raise ValueError("Snapshots must be unresampled Yahoo observations")
        if payload["metadata"]["response_sha256"] != obs.provenance.source_sha256:
            raise ValueError("Snapshot and provider provenance differ")
        datasets[obs.timeframe.label] = obs
    if set(datasets) != {"1mo", "1wk", "1d", "1h"}:
        raise ValueError("Four exact observation resolutions required")
    return manifest, datasets


def capture(folder):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    entries = []
    provider = YahooFinanceProvider()
    for interval in (YahooInterval.MONTHLY, YahooInterval.WEEKLY,
                     YahooInterval.DAILY, YahooInterval.HOURLY):
        # Explicit retention request; no inferred timeframe/degree relation.
        start = now - timedelta(days=729) if interval is YahooInterval.HOURLY else datetime(1970, 1, 1, tzinfo=timezone.utc)
        request = YahooHistoricalDataRequest("NVDA", MarketType.STOCK, interval, start, now)
        print(f"Yahoo retrieval: {interval.value}", flush=True)
        result = provider.fetch(request)
        entry = write_new(folder / f"NVDA_{interval.value}.json", {
            "request": request, "retrieved_at_utc": datetime.now(timezone.utc),
            "metadata": result.provider_metadata, "warnings": result.warnings,
            "observations": result.normalized_observations,
        })
        entries.append(entry)
    write_new(folder / "input_manifest.json", {
        "kind": "FRESH_YAHOO_NORMALIZED_SNAPSHOTS", "requested_at_utc": now,
        "files": entries, "raw_response_retained": False,
        "replay_boundary": "Lossless normalized transport; provider raw hash retained but raw body not exposed by public provider API.",
        "historical_comparison": "Fresh retrieval differs from historical inputs; do not attribute result differences solely to code.",
    })


def configuration():
    return {
        "classification": "CALLER_SUPPLIED_OPERATIONAL_BOUND",
        "geometry": plain(GeometricPivotDiscoveryConfig(
            GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 2, 2, EqualExtremePolicy.LAST, True)),
        "parent": plain(CandidateGenerationConfig(6, 6, 0, 10, SHAPES, CandidatePivotWindow.LATEST)),
        "child": plain(ChildCandidateGenerationConfig(100, 100, 6, 6, 0, 10, 500, SHAPES, 100, 10000)),
        "selection": plain(ChildObservationSelectionConfig(10000, 5000)),
        "child_family": plain(ChildFamilyEvaluationConfig(tuple(FamilyEvaluationKind), 100, 100, 500, 3, 1500, 1500)),
        "parent_normal_impulse_cap": 100, "child_normal_impulse_cap": 1000,
        "parent_family_kinds": plain(tuple(FamilyEvaluationKind)),
        "automatic_child_levels": 1, "timeframe_pairs": PAIRS,
        "child_pivot_window": "EARLIEST (existing child generator)",
        "scope_note": "Latest six parent pivots; earliest six per child window. No skipped pivots, degree assignment, resampling or ranking.",
    }


def counter(values):
    return dict(sorted(Counter(str(v) for v in values).items()))


def trace_evaluation(item):
    hypothesis = item.hypothesis
    snapshot = hypothesis.generated_candidate.source_observations
    evidence = item.p005_input.observation_binding
    roles = hypothesis.role_bindings[::2]
    checks = [evidence.observation_snapshot is snapshot,
              evidence.five_slot_view is hypothesis.five_slot_view,
              item.bounded_request.child_binding is hypothesis.five_slot_view.binding,
              item.bounded_request.subject is hypothesis.generated_candidate.subject,
              item.p005_result.input_snapshot is item.p005_input]
    endpoints = []
    for index, (bar, basis) in enumerate(zip(evidence.endpoint_bars, evidence.price_fields, strict=True)):
        role = roles[index // 2]
        pivot = role.start_boundary if index % 2 == 0 else role.end_boundary
        window = evidence.geometry_windows[index]
        checks.extend((any(bar is b for b in snapshot.bars),
                       window.provenance_ref is pivot,
                       bar.timestamp_utc == pivot.timestamp_utc,
                       getattr(bar, basis.value) == pivot.observed_price))
        endpoints.append({"role": role.component_role, "edge": "start" if index % 2 == 0 else "end",
                          "child_subject": role.child_subject.subject_id, "pivot_id": pivot.pivot_id,
                          "timestamp_utc": bar.timestamp_utc, "price_field": basis,
                          "price": getattr(bar, basis.value), "represented_ratio": plain(Fraction(getattr(bar, basis.value))),
                          "bar_provenance": bar.provenance, "pivot_state": pivot.state,
                          "eligible": evidence.endpoint_eligibility[index],
                          "window_bar_count": len(window.scoped_bars) if window.scoped_bars is not None else len(snapshot.bars)})
    if not all(checks):
        raise ValueError("Report trace differs from live exact observation/binding identities")
    child = hypothesis.generated_child_evidence
    return plain({
        "hypothesis_id": hypothesis.hypothesis_id,
        "candidate_id": hypothesis.generated_candidate.candidate_id,
        "subject_id": hypothesis.generated_candidate.subject.subject_id,
        "binding_id": hypothesis.five_slot_view.binding.binding_id,
        "source_kind": hypothesis.source_kind, "direction": item.p005_input.direction,
        "snapshot_content_sha256": sha(encoded(snapshot)), "source_response_sha256": snapshot.provenance.source_sha256,
        "exact_runtime_identity_checks_passed": True,
        "identity_note": "Content hashes identify replay data; live is-checks prove in-process identity. No serialized authority.",
        "child_requirement_id": None if child is None else child.internal_requirement.requirement_id,
        "parent_family_hypothesis_id": None if child is None else child.internal_requirement.family_hypothesis.hypothesis_id,
        "endpoints": endpoints, "p004_status": item.p004_result.status, "p004_reason": item.p004_result.reason,
        "p004_fatal": item.p004_result.fatal_to_candidate,
        "p004_certificate_origin_identity": item.structural_invalidity_certificate is not None and item.structural_invalidity_certificate.origin is item.p004_result,
        "p005_status": item.p005_result.status, "p005_reason": item.p005_result.reason,
        "percentage_movements": item.p005_result.percentage_movements,
        "partial_state": item.state, "unresolved_dependencies": item.unresolved_dependencies,
        "p005_protected_refs": item.p005_result.protected_sources,
        "family_validity_authority": item.family_validity_authority,
    })


def summarize_partial(result):
    validate_normal_impulse_partial_evaluation_result(result)
    traces = [trace_evaluation(item) for item in result.evaluations]
    summary = {
        "hypotheses": len(traces), "p004": counter(t["p004_status"] for t in traces),
        "p005": counter(t["p005_status"] for t in traces),
        "p005_unresolved_reasons": counter(t["p005_reason"] for t in traces if t["p005_status"] == "UNRESOLVED"),
        "p004_invalid_despite_p005_sufficiency": sum(t["p004_fatal"] and t["p005_status"] == "SUFFICIENT_CONDITION_ESTABLISHED" for t in traces),
        "p004_certificates": len(result.p004_certificates),
        "family_validity": 0, "diagnostics": list(result.diagnostics), "traces": traces,
    }
    audit_summary(summary)
    return summary


def audit_summary(summary):
    traces = summary["traces"]
    if len(traces) != summary["hypotheses"]:
        raise ValueError("Hypothesis/trace count mismatch")
    for behavior in ("p004", "p005"):
        if counter(t[f"{behavior}_status"] for t in traces) != summary[behavior]:
            raise ValueError("Outcome total mismatch")
    if summary["p004_certificates"] != sum(t["p004_fatal"] for t in traces):
        raise ValueError("Certificate/fatal total mismatch")
    expected_reasons = counter(t["p005_reason"] for t in traces if t["p005_status"] == "UNRESOLVED")
    if summary["p005_unresolved_reasons"] != expected_reasons:
        raise ValueError("Unresolved-reason total mismatch")
    overlap = sum(t["p004_fatal"] and t["p005_status"] == "SUFFICIENT_CONDITION_ESTABLISHED" for t in traces)
    if summary["p004_invalid_despite_p005_sufficiency"] != overlap:
        raise ValueError("Non-rescue overlap total mismatch")
    if any(t["family_validity_authority"] or not t["exact_runtime_identity_checks_passed"] for t in traces):
        raise ValueError("Unsupported authority or missing identity audit")
    if any(t["p004_fatal"] != t["p004_certificate_origin_identity"] for t in traces):
        raise ValueError("P004 origin not retained")


def run_scope(parent, finer, kernel, at, progress=print):
    prefix = f"nvda-post-p005:{parent.timeframe.label}"
    refs = (STAGE, parent.provenance.source_sha256, finer.provenance.source_sha256)
    cfg = configuration()
    geometry = GeometricPivotDiscoveryConfig(GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 2, 2, EqualExtremePolicy.LAST, True)
    progress(prefix + ":parent-generation")
    pivots = discover_geometric_pivots(GeometricPivotDiscoveryRequest(prefix + ":pivots", parent, geometry, refs))
    generated = generate_candidate_hypotheses(CandidateGenerationRequest(
        prefix + ":generation", at, AnalyzedWaveSubject(prefix, parent.provenance.source_sha256), parent, pivots,
        CandidateGenerationConfig(6, 6, 0, 10, SHAPES, CandidatePivotWindow.LATEST), (), refs))
    competing = build_competing_candidate_set(CompetingCandidateSetRequest(prefix + ":set", prefix, generated, refs))
    families = build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(
        prefix + ":families", at, competing, tuple(FamilyEvaluationKind), refs), kernel)
    progress(prefix + ":parent-p004-p005")
    parent_partial = evaluate_normal_impulse_partial_scope(NormalImpulsePartialEvaluationRequest(
        prefix + ":parent-partial", at, families, 100, 100, 100, refs), kernel)
    parent_summary = summarize_partial(parent_partial)
    internals = evaluate_family_internal_subdivisions(FamilyInternalSubdivisionEvaluationRequest(
        prefix + ":internals", families, (), refs))
    progress(prefix + ":finer-selection")
    bundle = MultiTimeframeObservationBundle(parent.symbol, (parent, finer), refs)
    contexts = {}
    selections = []
    for requirement in internals.internal_requirements:
        hypothesis = requirement.family_hypothesis
        if hypothesis.hypothesis_id not in contexts:
            # Operational leaf container for factual transport only. Reuses the genuine
            # existing cardinality result; supplies no synthetic methodology facts.
            tree = kernel.compose_recursive_candidate(RecursiveCandidateCompositionRequest(
                hypothesis.hypothesis_id + ":transport-leaf", hypothesis.bounded_result, (),
                OrderedChildBinding(hypothesis.hypothesis_id + ":transport-leaf-binding", hypothesis.parent_subject, ()), refs))
            contexts[hypothesis.hypothesis_id] = kernel.attach_multi_timeframe_observations(
                MultiTimeframeObservationTransportRequest(hypothesis.hypothesis_id + ":transport", tree, bundle, (), refs))
        candidate = requirement.parent_candidate
        start, end = candidate.ordered_selected_pivots[requirement.child_index:requirement.child_index + 2]
        interval = tuple(p for p in candidate.source_geometric_pivots.pivots if start.timestamp_utc <= p.timestamp_utc <= end.timestamp_utc)
        window = ProposedChildEvaluationWindow(requirement, candidate.source_geometric_pivots, start, end, interval, refs)
        selections.append(select_finer_child_observations(ChildObservationSelectionRequest(
            requirement.requirement_id + ":finer", requirement, window, contexts[hypothesis.hypothesis_id], finer,
            geometry, ChildObservationSelectionConfig(**cfg["selection"]), refs)))
    progress(prefix + ":child-generation")
    child_config = ChildCandidateGenerationConfig(100, 100, 6, 6, 0, 10, 500, SHAPES, 100, 10000)
    children = generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
        prefix + ":children", at, internals, child_config, refs, tuple(selections)))
    progress(prefix + ":child-family-review")
    child_families = evaluate_recursive_child_family_hypotheses(RecursiveChildFamilyEvaluationRequest(
        prefix + ":child-families", at, children,
        ChildFamilyEvaluationConfig(tuple(FamilyEvaluationKind), 100, 100, 500, 3, 1500, 1500), refs), kernel)
    progress(prefix + ":child-p004-p005")
    child_partial = evaluate_normal_impulse_partial_scope(NormalImpulsePartialEvaluationRequest(
        prefix + ":child-partial", at, children, 1000, 1000, 1000, refs), kernel)
    child_summary = summarize_partial(child_partial)
    requirements = []
    for req, selection, outcome in zip(internals.internal_requirements, selections, children.requirement_outcomes, strict=True):
        matching = [t for t in child_summary["traces"] if t["child_requirement_id"] == req.requirement_id]
        requirements.append(plain({
            "requirement_id": req.requirement_id, "parent_family": req.family_hypothesis.family_kind,
            "shape_required": req.required_internal_shape, "source_refs": req.protected_refs,
            "child_index": req.child_index, "coverage": selection.selected_window.coverage_state,
            "window_start": selection.selected_window.parent_window_start_utc, "window_end": selection.selected_window.parent_window_end_utc,
            "bars": len(selection.selected_window.ordered_bars),
            "pivots": 0 if selection.finer_geometric_pivots is None else len(selection.finer_geometric_pivots.pivots),
            "generation_status": outcome.status, "generation_diagnostic": outcome.diagnostic,
            "partial_normal_impulse_hypotheses": len(matching), "requirement_satisfied": False,
        }))
    return plain({
        "parent_resolution": parent.timeframe.label, "child_resolution": finer.timeframe.label,
        "parent_bars": len(parent.bars), "finer_bars": len(finer.bars), "geometric_pivots": len(pivots.pivots),
        "neutral_parent_candidates": len(generated.candidates), "parent_generation_diagnostics": generated.diagnostics,
        "parent_family_hypotheses": len(families.family_hypotheses),
        "parent_family_breakdown": counter(h.family_kind for h in families.family_hypotheses),
        "neutral_child_candidates": sum(len(e.competing_candidate_set.ordered_candidates) for e in children.generated_child_evidence),
        "child_family_hypotheses": len(child_families.family_hypotheses),
        "child_family_breakdown": counter(h.family_kind for h in child_families.family_hypotheses),
        "child_generation_diagnostics": children.diagnostics, "parent": parent_summary, "child": child_summary,
        "requirements": requirements, "requirements_satisfied": 0,
        "requirements_with_partial_normal_impulse_execution": sum(bool(r["partial_normal_impulse_hypotheses"]) for r in requirements),
        "coverage_counts": counter(r["coverage"] for r in requirements),
        "child_generation_counts": counter(r["generation_status"] for r in requirements),
        "caps_exhausted": False, "search_exhaustive": False,
        "scope_caveat": "No cap exception occurred; configured pivot selection still excludes search space. Bounded absence is not family impossibility.",
    })


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="Fresh Yahoo retrieval before execution")
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    for path in (args.inputs, args.output):
        if not path.resolve().is_relative_to(ROOT):
            parser.error("Paths must stay inside Runtime_WORKSPACE")
    if args.output.exists():
        parser.error("Output must not exist; never overwrite a prior run")
    report = {"stage": STAGE, "status": "INCOMPLETE", "configuration": configuration(), "scopes": []}
    current_stage = "input-capture" if args.capture else "input-replay"
    def progress(stage):
        nonlocal current_stage
        current_stage = stage
        print(stage, flush=True)
    try:
        if args.capture:
            capture(args.inputs)
        manifest, datasets = load_inputs(args.inputs)
        report["input_manifest_sha256"] = sha((args.inputs / "input_manifest.json").read_bytes())
        report["input_kind"] = "FRESH_CAPTURE" if args.capture else "REPLAY"
        report["snapshot_identity"] = {k: sha(encoded(v)) for k, v in datasets.items()}
        kernel = MethodologyKernel(Path(r"C:\ElliottCodex\Brain_LOCKED"))
        for parent, finer in PAIRS:
            report["scopes"].append(run_scope(datasets[parent], datasets[finer], kernel, manifest["requested_at_utc"], progress))
        report["status"] = "COMPLETED_BOUNDED_OPERATIONAL_EXPERIMENT"
    except Exception as error:
        # No retry with relaxed gates, synthetic replacement, or repaired contracts.
        report["failure"] = {"stage": current_stage, "type": type(error).__name__,
                             "message": str(error), "traceback": traceback.format_exc(),
                             "completed_scopes_are_not_a_complete_run": True}
        print(report["failure"]["traceback"], flush=True)
    write_new(args.output, report)
    print(report["status"], flush=True)
    return 0 if report["status"] == "COMPLETED_BOUNDED_OPERATIONAL_EXPERIMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
