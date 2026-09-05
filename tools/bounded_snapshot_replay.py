"""Diagnostic captured-value replay, NOT a point-in-time historical backtest.

Only factual transports are reconstructed. The unchanged prior runner issues
fresh geometry, bindings and methodology results. Comparison keys are reporting
keys, never certificates, identities, candidate continuity or confirmation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import traceback

import nvda_post_p005_experiment as prior
from elliott_methodology_kernel import MethodologyKernel
from elliott_methodology_kernel.models import NormalizedMarketObservations

STAGE = "BOUNDED-SNAPSHOT-ELIGIBILITY-REPLAY-V1"
BASE = "380bb7224847226f80f46eddc52066fc66ab4b15"
CAVEAT = (
    "Diagnostic replay of later-captured values, NOT a lookahead-free historical "
    "backtest. Timestamp membership does not mean final OHLC values were known "
    "at bar opening. No exchange calendar, bar-close or completion authority."
)


def utc(value):
    result = datetime.fromisoformat(value) if type(value) is str else value
    if type(result) is not datetime or result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("Explicit UTC timestamp required")
    return result


def make_plan(manifest):
    capture = utc(manifest["requested_at_utc"])
    month = capture.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last = month - timedelta(seconds=1)
    previous = last.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    return {
        "stage": STAGE, "approved_base": BASE, "caveat": CAVEAT,
        "capture_requested_at_utc": capture.isoformat(),
        "cutoffs_utc": [v.isoformat() for v in (previous, last, capture)],
        "cutoff_selection": "Last two UTC calendar month-ends before capture, then capture; independent of outcomes.",
        "membership": "Include recorded bars with timestamp_utc <= cutoff; exact inclusive UTC comparison.",
        "budget": {"cutoffs": 3, "pairs_per_cutoff": 3, "scope_evaluations": 9, "child_levels": 1},
        "pipeline_bounds": prior.configuration(),
        "network_retrieval": False,
        "snapshot_policy": "Reconstruct from original capture independently at every cutoff; never extend or mutate earlier snapshots.",
    }


def subset_observations(source, cutoff):
    """Fresh factual objects and separate derivation, with original capture provenance."""
    if type(source) is not NormalizedMarketObservations:
        raise ValueError("Exact normalized observations required")
    cutoff = utc(cutoff)
    stamps = [b.timestamp_utc for b in source.bars]
    if any(a >= b for a, b in zip(stamps, stamps[1:])):
        raise ValueError("Strictly increasing, unique input timestamps required; no silent sorting/deduplication")
    record = prior.plain(source)
    selected = [b for b in record["bars"] if utc(b["timestamp_utc"]) <= cutoff]
    if not selected:
        raise ValueError("Cutoff retains no observations")
    original_hash = prior.sha(prior.encoded(record))
    record["bars"] = selected
    # Retain nominal gap diagnostics only when both endpoints are retained.
    # Do not infer exchange sessions or claim these are missing trading bars.
    members = {b["timestamp_utc"] for b in selected}
    quality = record["quality"]
    quality["missing_intervals"] = [g for g in quality["missing_intervals"]
        if g["after_timestamp_utc"] in members and g["before_timestamp_utc"] in members]
    quality["duplicate_timestamps_utc"] = [s for s in quality["duplicate_timestamps_utc"] if s in members]
    quality["volume_available"] = any(b["volume"] is not None for b in selected)
    quality["volume_complete"] = all(b["volume"] is not None for b in selected)
    result = prior.restore_observations(record)
    if result is source or any(a is b for a, b in zip(source.bars, result.bars)):
        raise ValueError("Fresh snapshot/bar identity required")
    if prior.sha(prior.encoded(source)) != original_hash:
        raise ValueError("Source snapshot mutated")
    return result, {
        "timeframe": source.timeframe.label, "cutoff_utc": cutoff.isoformat(),
        "original_observation_transport_sha256": original_hash,
        "derived_observation_transport_sha256": prior.sha(prior.encoded(result)),
        "original_capture_provenance": prior.plain(source.provenance),
        "hash_boundary": "Derived transport hash is NOT a Yahoo raw-response hash.",
        "membership": "Original normalized array prefix [0, retained_bar_count); timestamp <= cutoff.",
        "retained_bar_count": len(selected), "excluded_later_bar_count": len(source.bars) - len(selected),
        "first_timestamp_utc": selected[0]["timestamp_utc"], "last_timestamp_utc": selected[-1]["timestamp_utc"],
        "source_record_indices": [b["provenance"]["source_record_index"] for b in selected],
        "quality_derivation": "Filter captured nominal gaps to retained endpoints; recompute volume presence/completeness. No resampling or session inference.",
        "fresh_factual_identity_checked": True,
    }


def sequence_key(trace, timeframe):
    return (timeframe, trace["direction"], tuple(
        (e["role"], e["edge"], e["timestamp_utc"], e["price_field"],
         e["represented_ratio"]["numerator"], e["represented_ratio"]["denominator"])
        for e in trace["endpoints"]))


def requirement_key(req, scope):
    return (scope["parent_resolution"], scope["child_resolution"], req["parent_family"],
            req["child_index"], req["shape_required"], req["window_start"], req["window_end"])


def indexed_traces(scope, path):
    """Limited factual scope keys; ambiguous duplicate contexts are not matched."""
    requirements = {r["requirement_id"]: r for r in scope["requirements"]}
    if len(requirements) != len(scope["requirements"]):
        raise ValueError("Duplicate requirement IDs in one report")
    rows = []
    for index, trace in enumerate(scope[path]["traces"]):
        timeframe = scope["parent_resolution"] if path == "parent" else scope["child_resolution"]
        seq = sequence_key(trace, timeframe)
        context = ("parent", scope["parent_resolution"])
        if path == "child":
            context = requirement_key(requirements[trace["child_requirement_id"]], scope)
        rows.append({"sequence": seq, "key": (context, seq), "trace_index": index, "trace": trace})
    return rows


def observed_state(trace):
    return {"endpoint_eligibility": [e["eligible"] for e in trace["endpoints"]],
            "pivot_states": [e["pivot_state"] for e in trace["endpoints"]],
            "p004_status": trace["p004_status"], "p005_status": trace["p005_status"],
            "p005_reason": trace["p005_reason"], "p004_fatal": trace["p004_fatal"]}


def compare_scopes(before, after, path):
    if (before["parent_resolution"], before["child_resolution"]) != (after["parent_resolution"], after["child_resolution"]):
        raise ValueError("Only like observation resolutions may be compared")
    left, right = indexed_traces(before, path), indexed_traces(after, path)
    groups = []
    for rows in (left, right):
        group = defaultdict(list)
        for row in rows:
            group[row["key"]].append(row)
        groups.append(group)
    a, b = groups
    matches = []
    ambiguous = []
    for key in sorted(a.keys() & b.keys()):
        if len(a[key]) != 1 or len(b[key]) != 1:
            ambiguous.append(prior.plain(key))
            continue
        old, new = a[key][0], b[key][0]
        old_state, new_state = observed_state(old["trace"]), observed_state(new["trace"])
        matches.append({"factual_key": prior.plain(key), "before_trace_index": old["trace_index"],
                        "after_trace_index": new["trace_index"], "before": old_state, "after": new_state,
                        "eligibility_changed": old_state["endpoint_eligibility"] != new_state["endpoint_eligibility"],
                        "outcome_changed": old_state != new_state})
    seq_a, seq_b = {r["sequence"] for r in left}, {r["sequence"] for r in right}
    return {
        "path": path, "matches": matches, "ambiguous_factual_contexts_not_matched": ambiguous,
        "same_sequence_count": len(seq_a & seq_b),
        "added_sequences": prior.plain(sorted(seq_b - seq_a)),
        "disappeared_sequences": prior.plain(sorted(seq_a - seq_b)),
        "added_contextual_rows": [r["trace_index"] for r in right if r["key"] not in a],
        "disappeared_contextual_rows": [r["trace_index"] for r in left if r["key"] not in b],
        "before_duplicate_sequence_evaluations": len(left) - len(seq_a),
        "after_duplicate_sequence_evaluations": len(right) - len(seq_b),
        "comparable_eligibility_changes": sum(m["eligibility_changed"] for m in matches),
        "replacement_or_membership_change": bool(seq_a - seq_b or seq_b - seq_a),
        "confirmation_count": 0,
        "comparison_boundary": "Factual endpoint/window/slot/family context only, not full ancestry continuity, identity or authority. Additions/disappearances are not paired replacements or confirmations; duplicate contexts are excluded from matching.",
    }


def compare_coverage(before, after):
    groups = []
    for scope in (before, after):
        group = defaultdict(list)
        for req in scope["requirements"]:
            group[requirement_key(req, scope)].append(req)
        groups.append(group)
    a, b = groups
    changes = []
    for key in sorted(a.keys() & b.keys()):
        if len(a[key]) == len(b[key]) == 1:
            fields = ("coverage", "bars", "pivots", "generation_status")
            old, new = ({f: group[key][0][f] for f in fields} for group in (a, b))
            if old != new:
                changes.append({"factual_window_context": prior.plain(key), "before": old, "after": new})
    return {"changes": changes, "added_window_contexts": len(b.keys() - a.keys()),
            "disappeared_window_contexts": len(a.keys() - b.keys()),
            "ambiguous_common_contexts_excluded": sum(len(a[k]) != 1 or len(b[k]) != 1 for k in a.keys() & b.keys())}


def run_cutoff(datasets, cutoff, kernel, progress=print):
    snapshots, derivations = {}, {}
    for label, data in datasets.items():
        snapshots[label], derivations[label] = subset_observations(data, cutoff)
    scopes = []
    for parent, finer in prior.PAIRS:
        scopes.append(prior.run_scope(snapshots[parent], snapshots[finer], kernel, utc(cutoff).isoformat(), progress))
    for label, snapshot in snapshots.items():
        if prior.sha(prior.encoded(snapshot)) != derivations[label]["derived_observation_transport_sha256"]:
            raise ValueError("Replay mutated a factual snapshot")
    return {"cutoff_utc": utc(cutoff).isoformat(), "derivations": derivations, "scopes": scopes}


def comparisons(runs):
    output = []
    for old, new in zip(runs, runs[1:]):
        for before, after in zip(old["scopes"], new["scopes"], strict=True):
            output.append({"before_cutoff": old["cutoff_utc"], "after_cutoff": new["cutoff_utc"],
                "parent_resolution": before["parent_resolution"], "child_resolution": before["child_resolution"],
                "paths": [compare_scopes(before, after, path) for path in ("parent", "child")],
                "coverage": compare_coverage(before, after)})
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if any(not p.resolve().is_relative_to(prior.ROOT) for p in (args.inputs, args.plan, args.output)):
        parser.error("All paths must remain inside Runtime_WORKSPACE")
    if args.output.exists():
        parser.error("Never overwrite an existing replay")
    manifest, datasets = prior.load_inputs(args.inputs)
    plan = json.loads(args.plan.read_bytes())
    if prior.encoded(plan) != prior.encoded(make_plan(manifest)):
        parser.error("Plan differs from the deterministic predeclared capture-derived budget")
    original_hashes = {k: prior.sha(prior.encoded(v)) for k, v in datasets.items()}
    report = {"stage": STAGE, "status": "INCOMPLETE", "caveat": CAVEAT, "configuration": plan,
              "plan_sha256": prior.sha(args.plan.read_bytes()), "runs": [],
              "input_manifest_sha256": prior.sha((args.inputs / "input_manifest.json").read_bytes())}
    stage = "start"
    def progress(value):
        nonlocal stage
        stage = value
        print(value, flush=True)
    try:
        kernel = MethodologyKernel(Path(r"C:\ElliottCodex\Brain_LOCKED"))
        for cutoff in plan["cutoffs_utc"]:
            progress("cutoff:" + cutoff)
            prior_hashes = [prior.sha(prior.encoded(r)) for r in report["runs"]]
            report["runs"].append(run_cutoff(datasets, cutoff, kernel, progress))
            if prior_hashes != [prior.sha(prior.encoded(r)) for r in report["runs"][:-1]]:
                raise ValueError("Earlier report mutated")
        report["comparisons"] = comparisons(report["runs"])
        if original_hashes != {k: prior.sha(prior.encoded(v)) for k, v in datasets.items()}:
            raise ValueError("Original captured observations mutated")
        report["status"] = "COMPLETED_BOUNDED_CAPTURED_VALUE_REPLAY"
    except Exception as error:
        report["failure"] = {"stage": stage, "type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc(), "partial_run_is_not_exhaustive": True}
        print(report["failure"]["traceback"], flush=True)
    prior.write_new(args.output, report)
    print(report["status"], flush=True)
    return 0 if report["status"] == "COMPLETED_BOUNDED_CAPTURED_VALUE_REPLAY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
