"""Read-only independent saved-result audit; no methodology implementation."""
from collections import Counter
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import nvda_post_p005_experiment as prior
from elliott_runtime.market_data.geometric_pivots import (
    EqualExtremePolicy, GeometricPivotDiscoveryConfig, GeometricPivotDiscoveryMethod,
    GeometricPivotDiscoveryRequest, discover_geometric_pivots,
)


def run_audit(folder):
    original = ROOT / "kernel_reviews/NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1"
    manifest, datasets = prior.load_inputs(original / "inputs")
    report = json.loads((folder / "replay_results.json").read_bytes())
    plan = json.loads((folder / "configuration.json").read_bytes())
    assert report["status"] == "COMPLETED_BOUNDED_CAPTURED_VALUE_REPLAY"
    assert report["configuration"] == plan
    assert report["plan_sha256"] == prior.sha((folder / "configuration.json").read_bytes())
    assert len(report["runs"]) == 3 and sum(len(r["scopes"]) for r in report["runs"]) == 9
    assert [r["cutoff_utc"] for r in report["runs"]] == plan["cutoffs_utc"]
    summary, representatives, quality, replacement_cases, partial_windows = [], [], [], [], []
    endpoint_checks = 0
    for run in report["runs"]:
        cutoff = datetime.fromisoformat(run["cutoff_utc"])
        subsets = {}
        for label, data in datasets.items():
            # Independent timestamp filter, not the new runner's subset function.
            record = prior.plain(data)
            record["bars"] = [b for b in record["bars"] if datetime.fromisoformat(b["timestamp_utc"]) <= cutoff]
            stamps = {b["timestamp_utc"] for b in record["bars"]}
            record["quality"]["missing_intervals"] = [g for g in record["quality"]["missing_intervals"]
                if g["before_timestamp_utc"] in stamps and g["after_timestamp_utc"] in stamps]
            record["quality"]["duplicate_timestamps_utc"] = [s for s in record["quality"]["duplicate_timestamps_utc"] if s in stamps]
            record["quality"]["volume_available"] = any(b["volume"] is not None for b in record["bars"])
            record["quality"]["volume_complete"] = all(b["volume"] is not None for b in record["bars"])
            derived = run["derivations"][label]
            assert derived["derived_observation_transport_sha256"] == prior.sha(prior.encoded(record))
            assert derived["original_observation_transport_sha256"] == prior.sha(prior.encoded(data))
            assert derived["original_capture_provenance"] == prior.plain(data.provenance)
            assert derived["retained_bar_count"] == len(record["bars"])
            assert derived["excluded_later_bar_count"] == len(data.bars) - len(record["bars"])
            assert derived["source_record_indices"] == [b["provenance"]["source_record_index"] for b in record["bars"]]
            subsets[label] = prior.restore_observations(record)
            quality.append({"cutoff": run["cutoff_utc"], "timeframe": label,
                "bars": len(record["bars"]), "excluded_later_bars": derived["excluded_later_bar_count"],
                "first": record["bars"][0]["timestamp_utc"], "last": record["bars"][-1]["timestamp_utc"],
                "capture_requested_at": manifest["requested_at_utc"],
                "nominal_gap_intervals": len(record["quality"]["missing_intervals"]),
                "missing_volume": sum(b["volume"] is None for b in record["bars"]),
                "duplicate_timestamps": len(record["bars"]) - len(stamps)})
        for scope in run["scopes"]:
            reqs = {r["requirement_id"]: r for r in scope["requirements"]}
            assert len(reqs) == len(scope["requirements"]) == sum(scope["coverage_counts"].values())
            assert Counter(r["coverage"] for r in reqs.values()) == scope["coverage_counts"]
            assert Counter(r["generation_status"] for r in reqs.values()) == scope["child_generation_counts"]
            assert not any(r["requirement_satisfied"] for r in reqs.values())
            finer = subsets[scope["child_resolution"]]
            for req in reqs.values():
                retained = [b for b in finer.bars if datetime.fromisoformat(req["window_start"]) <= b.timestamp_utc <= datetime.fromisoformat(req["window_end"])]
                assert len(retained) == req["bars"]
                expected_coverage = "NO_WINDOW_COVERAGE" if not retained else (
                    "FULL_WINDOW_COVERAGE" if finer.bars[0].timestamp_utc <= datetime.fromisoformat(req["window_start"])
                    and finer.bars[-1].timestamp_utc >= datetime.fromisoformat(req["window_end"]) else "PARTIAL_WINDOW_COVERAGE")
                assert req["coverage"] == expected_coverage
                if expected_coverage != "FULL_WINDOW_COVERAGE":
                    partial_windows.append({"cutoff": run["cutoff_utc"], "requirement": req,
                        "first_available_finer_bar": finer.bars[0].timestamp_utc.isoformat(),
                        "last_available_finer_bar": finer.bars[-1].timestamp_utc.isoformat()})
            for path in ("parent", "child"):
                traces = scope[path]["traces"]
                prior.audit_summary(scope[path])
                data = subsets[scope["parent_resolution"] if path == "parent" else scope["child_resolution"]]
                cache = {}
                sequence_counts = Counter()
                for index, trace in enumerate(traces):
                    assert trace["snapshot_content_sha256"] == prior.sha(prior.encoded(data))
                    assert trace["source_response_sha256"] == data.provenance.source_sha256
                    assert not trace["family_validity_authority"]
                    interval = None
                    if path == "child":
                        req = reqs[trace["child_requirement_id"]]
                        interval = (req["window_start"], req["window_end"])
                    if interval not in cache:
                        bars = None if interval is None else tuple(b for b in data.bars
                            if datetime.fromisoformat(interval[0]) <= b.timestamp_utc <= datetime.fromisoformat(interval[1]))
                        geom = discover_geometric_pivots(GeometricPivotDiscoveryRequest(
                            "read-only-replay-audit", data,
                            GeometricPivotDiscoveryConfig(GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 2, 2, EqualExtremePolicy.LAST, True),
                            ("audit:factual-replay",), bars))
                        cache[interval] = geom
                    geom = cache[interval]
                    bar_lookup = {b.timestamp_utc.isoformat(): b for b in data.bars}
                    values = []
                    for edge in trace["endpoints"]:
                        bar = bar_lookup[edge["timestamp_utc"]]
                        value = Fraction(getattr(bar, edge["price_field"]))
                        assert value == Fraction(edge["represented_ratio"]["numerator"], edge["represented_ratio"]["denominator"])
                        assert edge["bar_provenance"] == prior.plain(bar.provenance)
                        matches = [p for p in geom.pivots if p.timestamp_utc == bar.timestamp_utc and
                            p.pivot_kind.value == ("HIGH" if edge["price_field"] == "high" else "LOW") and p.observed_price == edge["price"]]
                        assert len(matches) == 1
                        pivot = matches[0]
                        assert pivot.state.value == edge["pivot_state"]
                        assert edge["eligible"] == (pivot.state.value == "CONFIRMED_BY_GEOMETRY")
                        assert edge["window_bar_count"] == len(geom.scoped_bars if geom.scoped_bars is not None else data.bars)
                        values.append(value)
                        endpoint_checks += 1
                    direction = 1 if trace["direction"] == "UP" else -1
                    violation = direction * (values[2] - values[0]) < 0
                    assert trace["p004_fatal"] == violation == trace["p004_certificate_origin_identity"]
                    assert (trace["p004_status"] == "RULE_VIOLATED") == violation
                    if not all(e["eligible"] for e in trace["endpoints"]):
                        assert trace["p005_status"] == "UNRESOLVED" and trace["p005_reason"] == "DEVELOPING_REQUIRED_ENDPOINT"
                    elif any(direction * (values[i+1] - values[i]) <= 0 for i in (0, 2, 4)):
                        assert trace["p005_status"] == "UNRESOLVED" and trace["p005_reason"] == "ZERO_OR_OPPOSING_ROLE_MOVEMENT"
                    else:
                        changes = [100 * abs(values[i+1] - values[i]) / values[i] for i in (0, 2, 4)]
                        assert prior.plain(changes) == trace["percentage_movements"]
                        assert (trace["p005_status"] == "SUFFICIENT_CONDITION_ESTABLISHED") == (changes[1] > changes[0] or changes[1] > changes[2])
                    key = tuple((e["timestamp_utc"], e["price_field"], e["price"]) for e in trace["endpoints"])
                    sequence_counts[key] += 1
                summary.append({"cutoff": run["cutoff_utc"], "parent_resolution": scope["parent_resolution"], "path": path,
                    "hypotheses": len(traces), "unique_endpoint_sequences": len(sequence_counts),
                    "duplicate_sequence_evaluations": len(traces) - len(sequence_counts),
                    "p004": scope[path]["p004"], "p005": scope[path]["p005"],
                    "p005_reasons": scope[path]["p005_unresolved_reasons"],
                    "p004_invalid_despite_p005_sufficiency": scope[path]["p004_invalid_despite_p005_sufficiency"]})
    for comparison in report["comparisons"]:
        before = next(r for r in report["runs"] if r["cutoff_utc"] == comparison["before_cutoff"])
        after = next(r for r in report["runs"] if r["cutoff_utc"] == comparison["after_cutoff"])
        old = next(s for s in before["scopes"] if s["parent_resolution"] == comparison["parent_resolution"])
        new = next(s for s in after["scopes"] if s["parent_resolution"] == comparison["parent_resolution"])
        for path in comparison["paths"]:
            def factual_sequence(t):
                return tuple((e["timestamp_utc"], e["price_field"], e["price"], e["role"], e["edge"])
                             for e in t["endpoints"])
            old_sequences = {factual_sequence(t) for t in old[path["path"]]["traces"]}
            new_sequences = {factual_sequence(t) for t in new[path["path"]]["traces"]}
            assert len(new_sequences - old_sequences) == len(path["added_sequences"])
            assert len(old_sequences - new_sequences) == len(path["disappeared_sequences"])
            assert len(new_sequences & old_sequences) == path["same_sequence_count"]
            assert len(new[path["path"]]["traces"]) - len(new_sequences) == path["after_duplicate_sequence_evaluations"]
            if path["replacement_or_membership_change"] and len(replacement_cases) < 4:
                gone = next((t for t in old[path["path"]]["traces"] if factual_sequence(t) not in new_sequences), None)
                added = next((t for t in new[path["path"]]["traces"] if factual_sequence(t) not in old_sequences), None)
                replacement_cases.append({"before_cutoff": comparison["before_cutoff"], "after_cutoff": comparison["after_cutoff"],
                    "parent_resolution": comparison["parent_resolution"], "path": path["path"],
                    "disappeared_example": gone, "added_example": added,
                    "not_a_pairing_or_confirmation": True})
            for match in path["matches"]:
                a = old[path["path"]]["traces"][match["before_trace_index"]]
                b = new[path["path"]]["traces"][match["after_trace_index"]]
                facts = lambda t: [(e["role"], e["edge"], e["timestamp_utc"], e["price_field"], e["represented_ratio"]) for e in t["endpoints"]]
                assert facts(a) == facts(b)
                changed = [e["eligible"] for e in a["endpoints"]] != [e["eligible"] for e in b["endpoints"]]
                assert changed == match["eligibility_changed"]
                if changed or not representatives:
                    representatives.append({"before_cutoff": comparison["before_cutoff"], "after_cutoff": comparison["after_cutoff"],
                        "parent_resolution": comparison["parent_resolution"], "path": path["path"], "match": match,
                        "before_trace": a, "after_trace": b})
            assert path["comparable_eligibility_changes"] == sum(m["eligibility_changed"] for m in path["matches"])
            assert path["confirmation_count"] == 0
    historical = json.loads((original / "experiment_results.json").read_bytes())
    assert report["runs"][-1]["scopes"] == historical["scopes"]
    return {"assessment": "SHARE_WITH_CAVEATS_DIAGNOSTIC_ONLY", "all_checks_passed": True,
        "endpoint_checks": endpoint_checks, "scope_path_summary": summary, "quality": quality,
        "representative_comparisons": representatives,
        "representative_membership_changes": replacement_cases,
        "partial_window_cases": partial_windows,
        "final_cutoff_reproduces_prior_scope_reports_exactly": True,
        "all_endpoint_geometry_states_checked_against_public_geometry": True,
        "no_confirmation_or_family_authority": True,
        "limitations": ["Later capture values, not point-in-time history", "Nominal gaps are not verified missing trading bars",
                        "Comparison keys are limited factual contexts, not complete ancestry or live authority"]}


if __name__ == "__main__":
    print(json.dumps(run_audit(Path(__file__).resolve().parent)))
