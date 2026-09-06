"""Bounded NVDA evidence report, not a completed-count or authority serializer."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from fractions import Fraction
import io
import json
from pathlib import Path
import traceback

import nvda_post_p005_experiment as pipeline
from elliott_methodology_kernel import MethodologyKernel
from elliott_runtime.analysis.family_hypotheses import validate_family_hypothesis_bridge_result
from elliott_runtime.analysis.family_internal_subdivisions import validate_family_internal_subdivision_evaluation_result
from elliott_runtime.analysis.recursive_child_family_evaluation import validate_recursive_child_family_evaluation_result
from elliott_runtime.analysis.normal_impulse_partial_evaluation import validate_normal_impulse_partial_evaluation_result
from elliott_runtime.market_data.yahoo import YahooFinanceProviderError

STAGE = "NVDA-BOUNDED-ANALYSIS-REPORT-V1"
DISPLAY_GROUPS_PER_PATH = 2  # Presentation only; never search/ranking policy.
OPENING = "Candidate analysis only: no complete validated Elliott count or directional forecast is established."
AUTHORITY = {"family_validity": False, "completion": False, "ranking": False,
             "forecast": False, "degree": False}
BLOCKERS = (
    "P006 remains frozen/unresolved/conflicted: orthodox endpoints, scope, equality and timing are not resolved.",
    "P005 establishes percentage sufficiency only, not full P005 or impulse validity.",
    "SOURCE_DERIVED_BASE_CASE_NOT_FOUND: reviewed children do not supply positive family proof.",
    "Flat/Triangle geometry freezes remain intact; cardinality is not subtype or full-family validation.",
)


def write_bytes_new(path, raw):
    path = Path(path).resolve()
    if not path.is_relative_to(pipeline.ROOT) or path == pipeline.ROOT:
        raise ValueError("Report writes must stay inside Runtime_WORKSPACE")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def endpoint_records(candidate, labels, children):
    """Audit each transported pivot against its exact source observation."""
    snapshot = candidate.source_observations
    pivots = candidate.ordered_selected_pivots
    if candidate.source_geometric_pivots.input_observations is not snapshot:
        raise ValueError("Candidate lost exact observation relationship")
    if len(labels) != len(pivots) - 1 or len(children) != len(labels):
        raise ValueError("Role/cardinality mismatch")
    by_time = {bar.timestamp_utc: bar for bar in snapshot.bars}
    endpoints = []
    for index, (label, child) in enumerate(zip(labels, children, strict=True)):
        for edge, pivot in zip(("start", "end"), pivots[index:index + 2], strict=True):
            if not any(pivot is p for p in candidate.source_geometric_pivots.pivots):
                raise ValueError("Foreign selected pivot")
            # Existing geometric contract explicitly selects HIGH or LOW.
            basis = pivot.pivot_kind.value.lower()
            if basis not in ("high", "low") or pivot.elliott_endpoint_authority:
                raise ValueError("Unsupported endpoint price/authority")
            bar = by_time[pivot.timestamp_utc]
            price = getattr(bar, basis)
            if price != pivot.observed_price:
                raise ValueError("Reported pivot differs from actual bar field")
            endpoints.append(pipeline.plain({
                "role": label, "edge": edge, "child_subject": child.subject_id,
                "pivot_id": pivot.pivot_id, "timestamp_utc": bar.timestamp_utc,
                "price_field": basis, "price": price, "represented_ratio": Fraction(price),
                "pivot_state": pivot.state, "bar_provenance": bar.provenance,
            }))
    return endpoints


def base_row(hypothesis, path, parent_scope, labels, children, requirement=None):
    candidate = hypothesis.generated_candidate
    return {
        "hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate.candidate_id,
        "path": path, "parent_scope": parent_scope,
        "timeframe": candidate.source_observations.timeframe.label,
        "snapshot_content_sha256": pipeline.sha(pipeline.encoded(candidate.source_observations)),
        "source_response_sha256": candidate.source_observations.provenance.source_sha256,
        "candidate_shape": candidate.candidate_shape.value, "authority": dict(AUTHORITY),
        "direction": "NOT_ASSIGNED",
        "role_authority": "HYPOTHESIS_SLOT_METADATA_NOT_CONFIRMED_WAVE_LABELS",
        "endpoints": endpoint_records(candidate, labels, children),
        "requirement_id": None if requirement is None else requirement.requirement_id,
        "parent_family_hypothesis_id": None if requirement is None else requirement.family_hypothesis.hypothesis_id,
    }


def family_rows(bridge, path, parent_scope, requirement=None):
    validate_family_hypothesis_bridge_result(bridge)
    rows = []
    for h in bridge.family_hypotheses:
        row = base_row(h, path, parent_scope,
            tuple(f"child_{i + 1}" for i in range(len(h.ordered_child_subjects))),
            h.ordered_child_subjects, requirement)
        result = h.bounded_result
        row.update({
            "family": h.family_kind.value, "binding_id": h.child_binding.binding_id,
            "state": result.final_summary.value, "coverage": pipeline.plain(result.methodology_coverage),
            "unresolved_reasons": list(result.unresolved_reasons),
            "checks": [{"behavior_id": t.behavior_id, "result": pipeline.plain(t.result_object)}
                       for t in result.traceability],
            "p004": None, "p005": None,
        })
        rows.append(row)
    return rows


def normal_rows(result, path, parent_scope):
    validate_normal_impulse_partial_evaluation_result(result)
    rows = []
    for item in result.evaluations:
        h = item.hypothesis
        child = h.generated_child_evidence
        row = base_row(h, path, parent_scope,
            tuple(r.component_role for r in h.role_bindings),
            tuple(r.child_subject for r in h.role_bindings),
            None if child is None else child.internal_requirement)
        trace = pipeline.trace_evaluation(item)
        if item.bounded_request.child_binding is not h.five_slot_view.binding:
            raise ValueError("Normal Impulse binding changed")
        row.update({
            "family": "NORMAL_IMPULSE_PARTIAL", "direction": trace["direction"],
            "binding_id": h.five_slot_view.binding.binding_id, "state": item.state.value,
            "coverage": "P004_AND_P005_PARTIAL_ONLY",
            "unresolved_reasons": trace["unresolved_dependencies"], "checks": [],
            "p004": {"status": trace["p004_status"], "reason": trace["p004_reason"],
                     "fatal": trace["p004_fatal"], "origin_identity_checked": trace["p004_certificate_origin_identity"]},
            "p005": {"status": trace["p005_status"], "reason": trace["p005_reason"],
                     "percentage_movements": trace["percentage_movements"]},
            "p005_observation_trace": trace,
            "report_status": "REJECTED_EXACT_HYPOTHESIS_P004" if trace["p004_fatal"] else "PARTIAL_REVIEW_UNRESOLVED_FAMILY",
        })
        rows.append(row)
    return rows


def collect_live(families, internals, child_families, parent_partial, child_partial, parent_scope):
    validate_family_internal_subdivision_evaluation_result(internals)
    validate_recursive_child_family_evaluation_result(child_families)
    rows = family_rows(families, "parent", parent_scope) + normal_rows(parent_partial, "parent", parent_scope)
    for item in child_families.child_evaluations:
        if item.family_hypothesis_result is not None:
            rows += family_rows(item.family_hypothesis_result, "child", parent_scope,
                                item.generated_child_evidence.internal_requirement)
    rows += normal_rows(child_partial, "child", parent_scope)
    requirements = [{
        "requirement_id": r.requirement_id, "parent_family_hypothesis_id": r.family_hypothesis.hypothesis_id,
        "parent_candidate_id": r.parent_candidate.candidate_id,
        "child_subject": r.child_subject.subject_id, "child_index": r.child_index,
        "required_internal_shape": r.required_internal_shape.value,
        "execution_status": r.execution_status.value, "source_class": r.source_class,
        "source_principle_id": r.source_principle_id, "protected_refs": list(r.protected_refs),
        "requirement_satisfied": False,
    } for r in internals.internal_requirements]
    scopes = [{
        "requirement_id": r.internal_requirement.requirement_id, "coverage_state": r.coverage_state.value,
        "compatible_executable_family_kinds": pipeline.plain(r.compatible_executable_family_kinds),
        "unavailable_source_families": list(r.unavailable_source_families), "blockers": list(r.blockers),
    } for r in child_families.requirement_scopes]
    return {"hypotheses": rows, "requirements": requirements, "child_family_scopes": scopes,
            "child_family_blockers": list(child_families.blockers)}


def group_rows(rows):
    """Group presentation only; every original row and parent link is retained."""
    groups = {}
    for index, row in enumerate(rows):
        key = (row["parent_scope"], row["path"], row["timeframe"], row["snapshot_content_sha256"],
               tuple((e["timestamp_utc"], e["price_field"], e["represented_ratio"]["numerator"],
                      e["represented_ratio"]["denominator"]) for e in row["endpoints"]))
        token = pipeline.sha(pipeline.encoded(key))
        groups.setdefault(token, {"group_id": token, "hypothesis_ids": [],
                                 "requirement_links": [], "first_row_index": index})
        groups[token]["hypothesis_ids"].append(row["hypothesis_id"])
        groups[token]["requirement_links"].append({"hypothesis_id": row["hypothesis_id"],
            "requirement_id": row["requirement_id"], "parent_family_hypothesis_id": row["parent_family_hypothesis_id"]})
        row["group_id"] = token
    return list(groups.values())


def display_groups(report):
    """First group of each neutral shape per path; no outcome-based selection."""
    by_id = {r["hypothesis_id"]: r for r in report["hypotheses"]}
    seen = set()
    for group in report["groups"]:
        row = by_id[group["hypothesis_ids"][0]]
        key = (row["parent_scope"], row["path"], row["candidate_shape"])
        if key not in seen:
            seen.add(key)
            yield group


def assign_display_refs(report):
    """Compact lookup aliases only; full stable pipeline IDs remain in JSON/CSV."""
    candidates = {}
    for index, row in enumerate(report["hypotheses"], 1):
        row["display_ref"] = f"H{index:04}"
        key = (row["parent_scope"], row["path"], row["candidate_id"])
        candidates.setdefault(key, f"C{len(candidates) + 1:04}")
        row["candidate_display_ref"] = candidates[key]


def data_notes(folder, manifest, datasets, mode, failure=None):
    if mode not in ("FRESH_CAPTURE", "OFFLINE_REPLAY", "STALE_FALLBACK"):
        raise ValueError("Explicit data mode required")
    if (mode == "STALE_FALLBACK") != bool(failure):
        raise ValueError("Stale fallback requires its actual capture failure")
    notes = []
    for entry in manifest["files"]:
        payload = json.loads((folder / entry["path"]).read_bytes())
        obs = datasets[payload["observations"]["timeframe"]["label"]]
        notes.append({
            "timeframe": obs.timeframe.label, "bars": len(obs.bars),
            "first_bar_timestamp_utc": obs.bars[0].timestamp_utc.isoformat(),
            "latest_bar_timestamp_utc": obs.bars[-1].timestamp_utc.isoformat(),
            "actual_capture_time_utc": payload["retrieved_at_utc"], "input_file": entry,
            "metadata": payload["metadata"], "warnings": payload["warnings"],
            "quality": pipeline.plain(obs.quality), "provenance": pipeline.plain(obs.provenance),
            "snapshot_content_sha256": pipeline.sha(pipeline.encoded(obs)),
        })
    return {"mode": mode, "fallback_reason": failure, "datasets": notes,
            "capture_requested_at_utc": manifest["requested_at_utc"],
            "input_manifest_sha256": pipeline.sha((folder / "input_manifest.json").read_bytes()),
            "input_folder": folder.resolve().relative_to(pipeline.ROOT).as_posix(),
            "raw_body_retained": False,
            "caveat": "Bar timestamps are not bar-close/completion evidence. No historical point-in-time claim; raw response hashes cannot be recomputed from normalized snapshots."}


def audit_document(report):
    """Reconcile records; reject inconsistent reporting, never issue authority."""
    rows = report["hypotheses"]
    ids = [r["hypothesis_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate hypothesis identity in report")
    grouped = [h for g in report["groups"] for h in g["hypothesis_ids"]]
    if Counter(grouped) != Counter(ids):
        raise ValueError("Grouping dropped or duplicated hypothesis links")
    by_id = {r["hypothesis_id"]: r for r in rows}
    for g in report["groups"]:
        if len(g["requirement_links"]) != len(g["hypothesis_ids"]):
            raise ValueError("Missing requirement links")
        for link in g["requirement_links"]:
            row = by_id[link["hypothesis_id"]]
            if row["group_id"] != g["group_id"] or any(row[k] != link[k] for k in ("requirement_id", "parent_family_hypothesis_id")):
                raise ValueError("Changed grouping ancestry")
    for row in rows:
        if row["authority"] != AUTHORITY:
            raise ValueError("Report cannot carry family/completion authority")
        if row["p004"] is not None:
            p4 = row["p004"]
            rejected = p4["status"] == "RULE_VIOLATED"
            if rejected != p4["fatal"] or rejected != p4["origin_identity_checked"]:
                raise ValueError("P004 fatality/origin mismatch")
            if rejected != (row["report_status"] == "REJECTED_EXACT_HYPOTHESIS_P004"):
                raise ValueError("P004 rejection concealed")
    for scope in report["scopes"]:
        own = [r for r in rows if r["parent_scope"] == scope["parent_resolution"]]
        for path in ("parent", "child"):
            selected = [r for r in own if r["path"] == path]
            normals = [r for r in selected if r["p004"] is not None]
            generic = [r for r in selected if r["p004"] is None]
            if len(generic) != scope[path + "_family_hypotheses"] or len(normals) != scope[path]["hypotheses"]:
                raise ValueError("Public result/report totals differ")
            for behavior in ("p004", "p005"):
                if pipeline.counter(r[behavior]["status"] for r in normals) != scope[path][behavior]:
                    raise ValueError("Status totals differ from public results")
        if any(r["requirement_satisfied"] for r in scope["requirements"]):
            raise ValueError("Partial coverage is not requirement satisfaction")
    return {"hypothesis_rows": len(rows), "groups": len(report["groups"]),
            "endpoint_rows": sum(len(r["endpoints"]) for r in rows),
            "requirement_links": len(grouped), "result": "PASS"}


def csv_text(rows, columns):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(row.get(k), sort_keys=True, ensure_ascii=False)
                         if isinstance(row.get(k), (list, dict)) else row.get(k) for k in columns})
    return out.getvalue()


def evidence_exports(report):
    candidates, endpoints = [], []
    for row in report["hypotheses"]:
        candidates.append({**row, "p004_status": None if row["p004"] is None else row["p004"]["status"],
            "p005_status": None if row["p005"] is None else row["p005"]["status"],
            "p005_reason": None if row["p005"] is None else row["p005"]["reason"]})
        for endpoint in row["endpoints"]:
            endpoints.append({**{k: row[k] for k in ("hypothesis_id", "candidate_id", "group_id", "path",
                "parent_scope", "timeframe", "family", "requirement_id", "parent_family_hypothesis_id",
                "snapshot_content_sha256")}, **endpoint})
    return {
        "candidates.csv": csv_text(candidates, ("display_ref", "candidate_display_ref", "hypothesis_id", "candidate_id", "group_id", "parent_scope",
            "path", "timeframe", "family", "direction", "state", "report_status", "requirement_id",
            "parent_family_hypothesis_id", "p004_status", "p005_status", "p005_reason",
            "snapshot_content_sha256", "unresolved_reasons")),
        "endpoints.csv": csv_text(endpoints, ("hypothesis_id", "candidate_id", "group_id", "parent_scope",
            "path", "timeframe", "family", "requirement_id", "parent_family_hypothesis_id",
            "snapshot_content_sha256", "role", "edge", "child_subject", "pivot_id", "timestamp_utc",
            "price_field", "price", "represented_ratio", "pivot_state", "bar_provenance")),
    }


def md(value):
    return str(value).replace("|", r"\|").replace("\n", " ")


def outcome_counts(values):
    names = {"RULE_SATISFIED": "satisfied", "RULE_VIOLATED": "violated",
        "UNRESOLVED": "unresolved", "SUFFICIENT_CONDITION_ESTABLISHED": "sufficiency established",
        "CURRENT_SUPPLIED_SCOPE_REVIEWED": "cardinality scope reviewed",
        "STRUCTURALLY_INVALID": "rejected in supplied scope"}
    return "; ".join(f"{names.get(k, k)}: {v}" for k, v in values.items()) or "none"


def render_markdown(report):
    audit = audit_document(report)
    rows = report["hypotheses"]
    normals = [r for r in rows if r["p004"] is not None]
    rejected = sum(r["p004"]["fatal"] for r in normals)
    sufficient = [r for r in normals if r["p005"]["status"] == "SUFFICIENT_CONDITION_ESTABLISHED"]
    lines = ["# NVDA bounded candidate analysis", "", OPENING, "", "## Summary", "",
        f"This executed search retained {audit['hypothesis_rows']} family/partial hypotheses across "
        f"{audit['groups']} endpoint-sequence groups. Repeated sequences are not independent market episodes. "
        "Rejection applies only to the named hypothesis; other interpretations are not thereby validated.", "",
        f"Of {len(normals)} Normal Impulse partial hypotheses, {rejected} are rejected by P004. "
        f"P005 percentage sufficiency is established in {len(sufficient)}; "
        f"{sum(r['p004']['fatal'] for r in sufficient)} of these still have a fatal P004 result. "
        "None establishes a complete family. The remaining family-bridge results concern supplied cardinality only.", "",
        "P004 tests the supplied Wave 2/origin relationship. P005 reports only percentage sufficiency. "
        "Neither establishes a completed impulse, exact degree, or validated family. No preferred/alternative ranking is made.", "",
        "## Data dates and scope", "", f"Data mode: **{report['data']['mode']}**. "
        + ("Older preserved data used because fresh retrieval failed: " + md(report["data"]["fallback_reason"])
           if report["data"]["fallback_reason"] else "Capture times below are actual retrieval times, not the time this report was replayed."), "",
        "| View | Bars | First bar UTC | Latest bar UTC | Actual capture UTC |",
        "| --- | ---: | --- | --- | --- |"]
    for d in report["data"]["datasets"]:
        lines.append(f"| {d['timeframe']} | {d['bars']} | {d['first_bar_timestamp_utc']} | {d['latest_bar_timestamp_utc']} | {d['actual_capture_time_utc']} |")
    currencies = sorted({str(d["metadata"].get("currency", "unavailable")) for d in report["data"]["datasets"]})
    lines += ["", f"Instrument: NVIDIA (NVDA). Provider currency: {', '.join(currencies)}. "
        "Prices retain Yahoo quote OHLC values, not adjusted-close substitutions. Timestamps locate provider bars, "
        "not necessarily the instant of an intrabar extreme or a completed Elliott endpoint.", "",
        "Monthly→Weekly, Weekly→Daily and Daily→1H are explicitly selected observation pairs, not Elliott degrees. "
        "Exactly one child layer is searched. Latest six parent pivots and earliest six child pivots, "
        "zero skips, maximum ten candidates per window and 500 child candidates per scope. "
        "Complete limits and diagnostics are retained in JSON and configuration.json. "
        "The beginning of available data is not assigned a wave origin.", "",
        "## Evaluated evidence", "",
        "The family bridge tests direct-child cardinality only. Its supplied-scope result is not family validity. "
        "Normal Impulse partial evaluation is additional to the four-family bridge.", "",
        "| Parent scope / path | Family | Hypotheses | P004 outcomes or cardinality scope | P005 sufficiency / unresolved |",
        "| --- | --- | ---: | --- | --- |"]
    for scope in report["scopes"]:
        for path in ("parent", "child"):
            subset = [r for r in rows if r["parent_scope"] == scope["parent_resolution"] and r["path"] == path]
            for family in dict.fromkeys(r["family"] for r in subset):
                part = [r for r in subset if r["family"] == family]
                p4 = pipeline.counter(r["p004"]["status"] for r in part) if part[0]["p004"] else pipeline.counter(r["state"] for r in part)
                p5 = pipeline.counter(r["p005"]["status"] for r in part) if part[0]["p005"] else "Not applicable"
                lines.append(f"| {scope['parent_resolution']} / {path} | {family} | {len(part)} | {md(outcome_counts(p4))} | {md(outcome_counts(p5) if isinstance(p5, dict) else p5)} |")
            if not subset:
                lines.append(f"| {scope['parent_resolution']} / {path} | No hypotheses generated | 0 | Unavailable within this search | Not evaluated |")
    lines += ["", "## Proposed structures: bounded display", "",
        f"At most {DISPLAY_GROUPS_PER_PATH} sequence groups per parent scope/path are shown, in deterministic generation order, "
        "not quality order: the first group of each neutral shape. Every hypothesis, including omitted display rows and rejected cases, remains in JSON/CSV. "
        "Compact H/C aliases resolve to exact hypothesis/candidate IDs in candidates.csv. "
        "Numeric roles belong only to the Normal Impulse hypothesis; other families retain neutral child slots.", ""]
    by_id = {r["hypothesis_id"]: r for r in rows}
    for g in display_groups(report):
        representative = by_id[g["hypothesis_ids"][0]]
        members = [by_id[i] for i in g["hypothesis_ids"]]
        sample = next((r for r in members if r["p004"]), representative)
        lines += [f"### {sample['parent_scope']} / {sample['path']} — sequence {g['group_id'][:12]}", "",
            f"Observed in {sample['timeframe']}; snapshot prefix {sample['snapshot_content_sha256'][:12]} (full hash in JSON/CSV). "
            "These are proposed endpoints, not certified orthodox ends.", "",
            "| Candidate ID | Hypothesis ID | Family | Explicit direction | Evidence |",
            "| --- | --- | --- | --- | --- |"]
        for row in members:
            result = row["state"]
            if row["p004"]:
                result = f"{row['report_status']}; P004 {row['p004']['status']}; P005 {row['p005']['status']}: {row['p005']['reason']}"
            lines.append(f"| {row['candidate_display_ref']} | {row['display_ref']} | {row['family']} | {row['direction']} | {md(result)} |")
        lines += ["", "| Proposed slot | Start UTC / field / price | End UTC / field / price |",
                  "| --- | --- | --- |"]
        for a, b in zip(sample["endpoints"][::2], sample["endpoints"][1::2], strict=True):
            lines.append(f"| {a['role']} | {a['timestamp_utc']} / {a['price_field']} / {a['price']!r} ({a['pivot_state']}) | {b['timestamp_utc']} / {b['price_field']} / {b['price']!r} ({b['pivot_state']}) |")
        if sample["p004"]:
            origin, extreme = sample["endpoints"][0], sample["endpoints"][3]
            lines += ["", f"For {sample['display_ref']} only, the P004 operands are the proposed Wave 1 origin "
                f"{origin['price']!r} and supplied Wave 2 retracement endpoint {extreme['price']!r}. "
                f"Returned reason: {md(sample['p004']['reason'])}. These are rule operands, not trading levels."]
        links = [x for x in g["requirement_links"] if x["requirement_id"]]
        if links:
            lines += ["", "Exact finer-evidence links (repetition retained):", "",
                      "| Child hypothesis | Parent family hypothesis | Required child |",
                      "| --- | --- | --- |"]
            for link in links:
                parent_ref = by_id[link["parent_family_hypothesis_id"]]["display_ref"]
                req = next(r for block in report["internal_links"] for r in block["requirements"]
                           if r["requirement_id"] == link["requirement_id"])
                lines.append(f"| {by_id[link['hypothesis_id']]['display_ref']} | {parent_ref} | child_{req['child_index'] + 1}: {req['required_internal_shape']} (exact ID in export) |")
        lines += [""]
    lines += ["## Rejections, unresolved internals and exclusions", ""]
    for scope in report["scopes"]:
        lines += [f"### {scope['parent_resolution']} with {scope['child_resolution']} child observations", "",
            f"Internal requirements: {len(scope['requirements'])}; satisfied: 0. "
            f"Requirements with partial Normal Impulse execution: {scope['requirements_with_partial_normal_impulse_execution']}. "
            f"Window coverage: {md(scope['coverage_counts'])}.", ""]
        for path in ("parent", "child"):
            s = scope[path]
            lines.append(f"- {path}: P004 rejections {s['p004'].get('RULE_VIOLATED', 0)}; "
                f"P004-invalid despite P005 sufficiency {s['p004_invalid_despite_p005_sufficiency']}. "
                f"P005 unresolved reasons: {md(s['p005_unresolved_reasons'])}.")
            if s["hypotheses"] == 0:
                lines.append(f"- No Normal Impulse {path} hypothesis was available in this bounded search; P004/P005 were not evaluated on that path.")
        pd = {d["code"]: d["count"] for d in scope["parent_generation_diagnostics"]}
        cd = {d["code"]: d["count"] for d in scope["child_generation_diagnostics"]}
        lines += ["", f"Search exclusions: {pd.get('PIVOTS_EXCLUDED_BY_CONSIDERATION_WINDOW', 0)} parent pivots "
            f"outside the latest-six consideration window; {pd.get('SUBSEQUENCES_REJECTED_BY_SPAN_OR_SKIP_BOUNDS', 0)} "
            f"subsequences outside span/skip bounds. Child windows with insufficient pivots: "
            f"{cd.get('INSUFFICIENT_INTERVAL_PIVOTS', 0)}; finer-coverage failures: {cd.get('FINER_COVERAGE_FAILURES', 0)}. "
            "No cap exception occurred; these exclusions are not evidence of family impossibility. Full diagnostics remain in JSON.", ""]
        partial_windows = Counter((r["window_start"], r["window_end"], r["bars"])
            for r in scope["requirements"] if r["coverage"] != "FULL_WINDOW_COVERAGE")
        for (start, end, bars), count in partial_windows.items():
            lines.append(f"- {count} requirement links use incompletely covered window {start} to {end}, "
                         f"with {bars} supplied bars per link. No full-coverage geometry was fabricated.")
        lines += [""]
    lines += ["## Limitations and next decision", ""] + ["- " + b for b in BLOCKERS]
    lines += ["- Validated-family producers and issuances remain 0 / 0. Missing children are not terminal waves.",
        "- Data quality below retains provider omissions; nominal interval gaps are not exchange-calendar proof of missing trading bars.",
        "- No RSI/MACD/EWO, Fibonacci evidence, volume interpretation, targets, entry/exit advice or trading invalidation levels were added.",
        "- Next step: review these candidate/evidence links; additional exact-family claims remain blocked by source authority, not by a preference score.", ""]
    for d in report["data"]["datasets"]:
        quality = d["quality"]
        lines.append(f"- {d['timeframe']}: provider warnings {md(d['warnings'])}; dropped null-OHLC rows "
            f"{md(d['metadata'].get('dropped_null_ohlc_row_indices', []))}; "
            f"duplicate timestamps {md(quality.get('duplicate_timestamps_utc', []))}; "
            f"nominal interval gaps {len(quality.get('missing_intervals', []))}.")
    lines += ["", "## Evidence exports and replay", "",
        f"candidates.csv: {audit['hypothesis_rows']} rows. endpoints.csv: {audit['endpoint_rows']} rows. "
        f"All {audit['requirement_links']} originating hypothesis links are retained. "
        "market_report.json contains full results within the executed search and exact source references. "
        "Run the offline command in README.md against saved inputs; no serialized methodology authority is reused.", ""]
    return "\n".join(lines)


def run_report(folder, output, *, mode="OFFLINE_REPLAY", failure=None,
               progress=lambda message: print(message, flush=True)):
    folder, output = Path(folder).resolve(), Path(output).resolve()
    if not folder.is_relative_to(pipeline.ROOT) or not output.is_relative_to(pipeline.ROOT):
        raise ValueError("Report paths must stay inside Runtime_WORKSPACE")
    if output.exists():
        raise FileExistsError("Report output must be new")
    manifest, datasets = pipeline.load_inputs(folder)
    report = {"stage": STAGE, "kind": "BOUNDED_NON_CERTIFYING_REPORT",
        "configuration": pipeline.plain(pipeline.configuration()), "display_groups_per_path": DISPLAY_GROUPS_PER_PATH,
        "authority": dict(AUTHORITY), "data": data_notes(folder, manifest, datasets, mode, failure),
        "scopes": [], "hypotheses": [], "internal_links": [], "blockers": list(BLOCKERS)}
    kernel = MethodologyKernel(Path(r"C:\ElliottCodex\Brain_LOCKED"))
    for parent, finer in pipeline.PAIRS:
        collected = []
        scope = pipeline.run_scope(datasets[parent], datasets[finer], kernel,
            manifest["requested_at_utc"], progress,
            observe_results=lambda *objects: collected.append(collect_live(*objects, parent)))
        if len(collected) != 1:
            raise ValueError("Missing live reporting observation")
        report["scopes"].append(scope)
        report["hypotheses"].extend(collected[0].pop("hypotheses"))
        report["internal_links"].append({"parent_scope": parent, **collected[0]})
    report["groups"] = group_rows(report["hypotheses"])
    assign_display_refs(report)
    report["audit"] = audit_document(report)
    markdown = render_markdown(report)
    exports = evidence_exports(report)
    pipeline.write_new(output / "market_report.json", report)
    write_bytes_new(output / "market_report.md", markdown.encode("utf-8"))
    for name, content in exports.items():
        write_bytes_new(output / name, content.encode("utf-8"))
    pipeline.write_new(output / "configuration.json", report["configuration"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--fallback-inputs", type=Path)
    args = parser.parse_args(argv)
    for path in (args.inputs, args.output, args.fallback_inputs):
        if path is not None and not path.resolve().is_relative_to(pipeline.ROOT):
            parser.error("Paths must remain inside Runtime_WORKSPACE")
    if args.output.exists() or (args.capture and args.inputs.exists()):
        parser.error("Capture and report destinations must be new")
    mode, failure, inputs = "OFFLINE_REPLAY", None, args.inputs
    try:
        if args.capture:
            try:
                pipeline.capture(inputs)
                mode = "FRESH_CAPTURE"
            except YahooFinanceProviderError as error:
                failure = f"{type(error).__name__}: {error}"
                pipeline.write_new(args.inputs / "capture_failure.json", {
                    "attempted_at_utc": datetime.now(timezone.utc), "failure": failure,
                    "partial_capture_not_used": True})
                if args.fallback_inputs is None:
                    raise
                inputs, mode = args.fallback_inputs, "STALE_FALLBACK"
        result = run_report(inputs, args.output, mode=mode, failure=failure)
        print(json.dumps(result["audit"]), flush=True)
        return 0
    except Exception as error:
        pipeline.write_new(args.output.parent / (args.output.name + "_failure.json"), {
            "stage": STAGE, "status": "INCOMPLETE", "type": type(error).__name__,
            "message": str(error), "traceback": traceback.format_exc()})
        print(traceback.format_exc(), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
