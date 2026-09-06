"""Read-only reconciliation of a bounded report against its preserved inputs."""
import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path

import nvda_bounded_report as report


def audit(folder):
    folder = Path(folder)
    raw = json.loads((folder / "market_report.json").read_bytes())
    if raw["stage"] != report.STAGE or raw["kind"] != "BOUNDED_NON_CERTIFYING_REPORT":
        raise ValueError("Unexpected report format")
    checked = report.audit_document(raw)
    inputs = (report.pipeline.ROOT / raw["data"]["input_folder"]).resolve()
    if not inputs.is_relative_to(report.pipeline.ROOT):
        raise ValueError("Input reference escapes workspace")
    manifest, datasets = report.pipeline.load_inputs(inputs)
    expected_notes = report.data_notes(inputs, manifest, datasets, raw["data"]["mode"], raw["data"]["fallback_reason"])
    if raw["data"] != expected_notes:
        raise ValueError("Data dates/provenance differ from preserved capture")
    snapshots = {report.pipeline.sha(report.pipeline.encoded(v)): v for v in datasets.values()}
    indices = {key: {b.timestamp_utc.isoformat(): b for b in obs.bars} for key, obs in snapshots.items()}
    checked_prices = 0
    for row in raw["hypotheses"]:
        obs = snapshots[row["snapshot_content_sha256"]]
        if row["timeframe"] != obs.timeframe.label or row["source_response_sha256"] != obs.provenance.source_sha256:
            raise ValueError("Snapshot/timeframe/provider link mismatch")
        for e in row["endpoints"]:
            bar = indices[row["snapshot_content_sha256"]][e["timestamp_utc"]]
            if e["price_field"] not in ("high", "low"):
                raise ValueError("Unexpected price basis")
            price = getattr(bar, e["price_field"])
            if price != e["price"] or report.pipeline.plain(Fraction(price)) != e["represented_ratio"]:
                raise ValueError("Endpoint price differs from exact saved observation")
            if report.pipeline.plain(bar.provenance) != e["bar_provenance"]:
                raise ValueError("Bar provenance differs")
            checked_prices += 1
        if row["p004"]:
            trace = row["p005_observation_trace"]
            expected = [e for e in row["endpoints"] if e["role"] in ("1", "3", "5")]
            for a, b in zip(expected, trace["endpoints"], strict=True):
                for k in ("role", "edge", "pivot_id", "timestamp_utc", "price_field", "price", "represented_ratio", "bar_provenance"):
                    if a[k] != b[k]:
                        raise ValueError("P005 evidence and displayed role differ")
            for behavior in ("p004", "p005"):
                if row[behavior]["status"] != trace[behavior + "_status"] or row[behavior]["reason"] != trace[behavior + "_reason"]:
                    raise ValueError("Rule status/reason differs from live trace")
    expected_md = report.render_markdown(raw)
    if (folder / "market_report.md").read_text(encoding="utf-8") != expected_md:
        raise ValueError("Markdown differs from complete report record")
    for name, text in report.evidence_exports(raw).items():
        if (folder / name).read_bytes() != text.encode("utf-8"):
            raise ValueError("CSV differs from complete report record")
        expected_count = checked["hypothesis_rows"] if name == "candidates.csv" else checked["endpoint_rows"]
        if len(list(csv.DictReader(io.StringIO(text)))) != expected_count:
            raise ValueError("CSV row totals differ")
    for block, scope in zip(raw["internal_links"], raw["scopes"], strict=True):
        original = {r["requirement_id"]: r for r in scope["requirements"]}
        for req in block["requirements"]:
            r = original[req["requirement_id"]]
            if req["required_internal_shape"] != r["shape_required"] or req["child_index"] != r["child_index"]:
                raise ValueError("Internal requirement link differs")
        if len(original) != len(block["requirements"]):
            raise ValueError("Missing requirement")
    return {**checked, "all_saved_endpoint_prices_verified": checked_prices,
            "all_capture_dates_and_quality_verified": True, "markdown_csv_reconciled": True,
            "authority_note": "Saved records are not certificates. Live identity validation occurred before export."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_folder", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.report_folder), indent=2))
