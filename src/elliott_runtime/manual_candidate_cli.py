"""Local CLI for strict non-authoritative manual-candidate JSON input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import NoReturn, TextIO

from elliott_methodology_kernel import (
    EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION,
    ExplicitPivotCandidateError,
    ExplicitPivotCandidateRequest,
    HumanReadableManualCandidateError,
    INPUT_SCHEMA_VERSION,
    MethodologyKernel,
    SNAPSHOT_SCHEMA_VERSION,
    parse_human_readable_explicit_pivot_candidate,
    parse_human_readable_manual_candidate,
    render_explicit_pivot_report,
    render_manual_candidate_snapshot,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
MAX_INPUT_BYTES = 1_048_576
ManualCandidateCliError = HumanReadableManualCandidateError
parse_manual_candidate_document = parse_human_readable_manual_candidate
render_non_authoritative_snapshot = render_manual_candidate_snapshot


def _fail(message: str) -> NoReturn:
    raise ManualCandidateCliError(message)


def _json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"Duplicate JSON object key is not allowed: {key}.")
        result[key] = value
    return result


def load_manual_candidate_file(path: str | Path):
    """Read one bounded UTF-8 JSON file and construct an exact untrusted request."""
    input_path = Path(path)
    try:
        payload = input_path.read_bytes()
    except OSError as error:
        raise ManualCandidateCliError(f"Cannot read input file: {error}") from error
    if len(payload) > MAX_INPUT_BYTES:
        _fail(f"Input exceeds the {MAX_INPUT_BYTES}-byte limit.")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ManualCandidateCliError("Input must be strict UTF-8.") from error
    try:
        document = json.loads(
            text,
            object_pairs_hook=_json_pairs,
            parse_constant=lambda token: _fail(
                f"Non-finite JSON number is not allowed: {token}."
            ),
        )
    except json.JSONDecodeError as error:
        raise ManualCandidateCliError(
            f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}."
        ) from error
    if type(document) is not dict:
        _fail("document must be one JSON object.")
    version = document.get("schema_version")
    if version == INPUT_SCHEMA_VERSION:
        return parse_human_readable_manual_candidate(document)
    if version == EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION:
        return parse_human_readable_explicit_pivot_candidate(document)
    _fail(
        "schema_version must be exactly one supported version: "
        f"{INPUT_SCHEMA_VERSION}, {EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION}."
    )


def _write_json(stream: TextIO, value: object) -> None:
    stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True))
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="elliott-manual-candidate",
        description=(
            "Run one strict, manually supplied candidate through the bounded "
            "local analysis workflow. Output is non-authoritative JSON."
        ),
    )
    parser.add_argument("input", help="Path to one UTF-8 JSON candidate document.")
    args = parser.parse_args(argv)
    try:
        request = load_manual_candidate_file(args.input)
        kernel = MethodologyKernel()
        if type(request) is ExplicitPivotCandidateRequest:
            result = kernel.analyze_explicit_pivot_candidate(request)
            snapshot = render_explicit_pivot_report(result)
        else:
            result = kernel.analyze_bounded_manual_chart(request)
            snapshot = render_manual_candidate_snapshot(result)
        _write_json(sys.stdout, snapshot)
        return 0
    except (
        ExplicitPivotCandidateError,
        ManualCandidateCliError,
        TypeError,
        ValueError,
    ) as error:
        _write_json(
            sys.stderr,
            {"error": "INVALID_MANUAL_CANDIDATE_INPUT", "message": str(error)},
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "INPUT_SCHEMA_VERSION",
    "MAX_INPUT_BYTES",
    "ManualCandidateCliError",
    "SNAPSHOT_SCHEMA_VERSION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "load_manual_candidate_file",
    "main",
    "parse_manual_candidate_document",
    "render_non_authoritative_snapshot",
]
