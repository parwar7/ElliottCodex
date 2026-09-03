"""Strict conversion of non-authoritative human values into manual inputs.

This PROJECT_ANALYSIS_INFRASTRUCTURE adapter maps a closed JSON-shaped value
vocabulary to existing public manual-fact types. It does not interpret market
data, determine applicability, execute validators, or create authority.
"""

from __future__ import annotations

import copy
from enum import Enum
import math
from typing import NoReturn, TypeVar

from .bounded_manual_chart_analysis import (
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
)
from .manual_structure_candidate_builder import (
    ManualCardinalityBehavior,
    ManualDegreePeerFact,
    ManualDirectChildCardinalityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualP004Wave2OriginFact,
    ManualP023VisibilityFact,
    ManualParentChildDegreeFact,
)
from .models import DegreeStatus, DegreeTreeNode, InternalStatus
from .p003_one_larger_degree_theme import P003OneLargerDegreeRelation
from .p004 import CandidateScope, ImpulseDirection
from .p023_visibility_guard import P023VisibilityState
from .subject_binding import AnalyzedWaveSubject


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
INPUT_SCHEMA_VERSION = "HUMAN_READABLE_MANUAL_CANDIDATE_CLI_V1"
SNAPSHOT_SCHEMA_VERSION = "MANUAL_CANDIDATE_ANALYSIS_SNAPSHOT_V1"


class HumanReadableManualCandidateError(ValueError):
    """Raised when a JSON-shaped manual declaration fails closed."""


_EnumT = TypeVar("_EnumT", bound=Enum)


def _fail(message: str) -> NoReturn:
    raise HumanReadableManualCandidateError(message)


def _exact_object(
    value: object,
    name: str,
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> dict[str, object]:
    if type(value) is not dict:
        _fail(f"{name} must be one JSON object.")
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - optional)
    if missing:
        _fail(f"{name} is missing required fields: {', '.join(missing)}.")
    if unknown:
        _fail(f"{name} contains unknown fields: {', '.join(unknown)}.")
    return value


def _text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        _fail(f"{name} must be one non-blank JSON string.")
    return value


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        _fail(f"{name} must be one JSON boolean.")
    return value


def _number(value: object, name: str) -> int | float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        _fail(f"{name} must be one finite JSON number.")
    return value


def _list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        _fail(f"{name} must be one JSON array.")
    return value


def _enum(value: object, enum_type: type[_EnumT], name: str) -> _EnumT:
    token = _text(value, name)
    try:
        return enum_type(token)
    except ValueError:
        allowed = ", ".join(item.value for item in enum_type)
        _fail(f"{name} must be one of: {allowed}.")


def _subject(value: object, name: str) -> AnalyzedWaveSubject:
    item = _exact_object(
        value,
        name,
        required=frozenset({"subject_id", "observation_provenance_ref"}),
    )
    return AnalyzedWaveSubject(
        _text(item["subject_id"], f"{name}.subject_id"),
        _text(
            item["observation_provenance_ref"],
            f"{name}.observation_provenance_ref",
        ),
    )


def _degree_node(value: object, index: int) -> DegreeTreeNode:
    name = f"facts[].direct_child_degrees[{index}]"
    item = _exact_object(
        value,
        name,
        required=frozenset(
            {"label", "degree", "degree_status", "internal_status", "parent_label"}
        ),
    )
    return DegreeTreeNode(
        label=_text(item["label"], f"{name}.label"),
        degree=_optional_text(item["degree"], f"{name}.degree"),
        degree_status=_enum(
            item["degree_status"], DegreeStatus, f"{name}.degree_status"
        ),
        internal_status=_enum(
            item["internal_status"], InternalStatus, f"{name}.internal_status"
        ),
        parent_label=_optional_text(item["parent_label"], f"{name}.parent_label"),
    )


def _fact(value: object, subject: AnalyzedWaveSubject, index: int) -> object:
    name = f"facts[{index}]"
    base = _exact_object(
        value,
        name,
        required=frozenset({"type"}),
        optional=frozenset(
            {
                "candidate_scope",
                "direction",
                "wave1_origin_price",
                "wave2_end_price",
                "parent_node_id",
                "direct_child_degrees",
                "parent_degree",
                "parent_degree_status",
                "child_degree",
                "child_degree_status",
                "visibility_state",
                "relation",
                "behavior",
            }
        ),
    )
    fact_type = _text(base["type"], f"{name}.type")

    def exact_fields(*fields: str) -> dict[str, object]:
        return _exact_object(value, name, required=frozenset(("type", *fields)))

    if fact_type == "P004_WAVE2_ORIGIN":
        item = exact_fields(
            "candidate_scope", "direction", "wave1_origin_price", "wave2_end_price"
        )
        return ManualP004Wave2OriginFact(
            _enum(item["candidate_scope"], CandidateScope, f"{name}.candidate_scope"),
            _enum(item["direction"], ImpulseDirection, f"{name}.direction"),
            _number(item["wave1_origin_price"], f"{name}.wave1_origin_price"),
            _number(item["wave2_end_price"], f"{name}.wave2_end_price"),
        )
    if fact_type == "DEGREE_PEER_CONSISTENCY":
        item = exact_fields("parent_node_id", "direct_child_degrees")
        nodes = tuple(
            _degree_node(node, node_index)
            for node_index, node in enumerate(
                _list(item["direct_child_degrees"], f"{name}.direct_child_degrees")
            )
        )
        return ManualDegreePeerFact(
            _text(item["parent_node_id"], f"{name}.parent_node_id"), nodes
        )
    if fact_type == "PARENT_CHILD_DEGREE_ADJACENCY":
        item = exact_fields(
            "parent_degree",
            "parent_degree_status",
            "child_degree",
            "child_degree_status",
        )
        return ManualParentChildDegreeFact(
            _text(item["parent_degree"], f"{name}.parent_degree"),
            _enum(
                item["parent_degree_status"],
                DegreeStatus,
                f"{name}.parent_degree_status",
            ),
            _text(item["child_degree"], f"{name}.child_degree"),
            _enum(
                item["child_degree_status"],
                DegreeStatus,
                f"{name}.child_degree_status",
            ),
        )
    if fact_type == "P023_VISIBILITY":
        item = exact_fields("visibility_state")
        return ManualP023VisibilityFact(
            subject,
            _enum(
                item["visibility_state"],
                P023VisibilityState,
                f"{name}.visibility_state",
            ),
        )
    if fact_type == "P003_ONE_LARGER_DEGREE_RELATION":
        item = exact_fields("relation")
        return ManualP003OneLargerDegreeRelationFact(
            _enum(
                item["relation"],
                P003OneLargerDegreeRelation,
                f"{name}.relation",
            )
        )
    if fact_type == "DIRECT_CHILD_CARDINALITY":
        item = exact_fields("behavior")
        return ManualDirectChildCardinalityFact(
            _enum(
                item["behavior"],
                ManualCardinalityBehavior,
                f"{name}.behavior",
            )
        )
    _fail(f"{name}.type is unsupported: {fact_type}.")


def parse_human_readable_manual_candidate(
    document: object,
) -> BoundedManualChartAnalysisRequest:
    """Convert one strict non-authoritative JSON value to the exact MVP request."""
    root = _exact_object(
        document,
        "document",
        required=frozenset(
            {
                "schema_version",
                "request_id",
                "requested_at_utc",
                "subject",
                "candidate_id",
                "facts",
                "provenance_refs",
            }
        ),
        optional=frozenset(
            {"ordered_children", "constructed_binding_id", "no_rescue_requested"}
        ),
    )
    version = _text(root["schema_version"], "schema_version")
    if version != INPUT_SCHEMA_VERSION:
        _fail(f"schema_version must be exactly {INPUT_SCHEMA_VERSION}.")
    subject = _subject(root["subject"], "subject")
    facts = tuple(
        _fact(item, subject, index)
        for index, item in enumerate(_list(root["facts"], "facts"))
    )
    provenance_refs = tuple(
        _text(item, f"provenance_refs[{index}]")
        for index, item in enumerate(
            _list(root["provenance_refs"], "provenance_refs")
        )
    )
    children_value = root.get("ordered_children")
    if children_value is None:
        ordered_children = None
    else:
        ordered_children = tuple(
            _subject(item, f"ordered_children[{index}]")
            for index, item in enumerate(_list(children_value, "ordered_children"))
        )
    binding_id = root.get("constructed_binding_id")
    if binding_id is not None:
        binding_id = _text(binding_id, "constructed_binding_id")
    no_rescue = _boolean(
        root.get("no_rescue_requested", False), "no_rescue_requested"
    )
    try:
        return BoundedManualChartAnalysisRequest(
            request_id=_text(root["request_id"], "request_id"),
            requested_at_utc=_text(root["requested_at_utc"], "requested_at_utc"),
            subject=subject,
            candidate_id=_text(root["candidate_id"], "candidate_id"),
            manual_behavior_facts=facts,
            ordered_child_subjects=ordered_children,
            constructed_binding_id=binding_id,
            no_rescue_requested=no_rescue,
            provenance_refs=provenance_refs,
        )
    except (TypeError, ValueError) as error:
        raise HumanReadableManualCandidateError(str(error)) from error


def _token(value: object) -> str | bool | int | float | None:
    if isinstance(value, Enum):
        return str(value.value)
    if value is None or type(value) in (str, bool, int, float):
        return value
    return type(value).__name__


def render_manual_candidate_snapshot(
    result: BoundedManualChartAnalysisResult,
) -> dict[str, object]:
    """Render exact scalar diagnostics without serializing methodology authority."""
    if type(result) is not BoundedManualChartAnalysisResult:
        _fail("Snapshot rendering requires one exact bounded-analysis result.")
    try:
        copy.copy(result)
    except Exception as error:
        raise HumanReadableManualCandidateError(
            "Snapshot rendering requires one unchanged bounded-analysis result."
        ) from error
    traces = []
    for trace in result.traceability:
        outcome = trace.result_object
        traces.append(
            {
                "behavior_id": trace.behavior_id,
                "manual_fact_type": (
                    None if trace.manual_fact is None else type(trace.manual_fact).__name__
                ),
                "input_type": type(trace.explicit_input.input_object).__name__,
                "result_type": type(outcome).__name__,
                "status": _token(getattr(outcome, "status", None)),
                "outcome": _token(getattr(outcome, "outcome", None)),
                "reason": _token(getattr(outcome, "reason", None)),
                "fatal_to_candidate": _token(
                    getattr(outcome, "fatal_to_candidate", None)
                ),
            }
        )
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "artifact_classification": ARTIFACT_CLASSIFICATION,
        "authority": "NON_AUTHORITATIVE_HUMAN_READABLE_SNAPSHOT",
        "request_id": result.request_id,
        "subject_id": result.subject.subject_id,
        "candidate_id": result.candidate_id,
        "final_summary": result.final_summary.value,
        "reviewed_is_valid": False,
        "methodology_coverage": [
            {"behavior_id": item.behavior_id, "state": item.state.value}
            for item in result.methodology_coverage
        ],
        "unresolved_reasons": list(result.unresolved_reasons),
        "structural_invalidity_certificate_count": len(
            result.structural_invalidity_certificates
        ),
        "traceability": traces,
        "provenance_refs": list(result.provenance_refs),
    }


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "HumanReadableManualCandidateError",
    "INPUT_SCHEMA_VERSION",
    "SNAPSHOT_SCHEMA_VERSION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "parse_human_readable_manual_candidate",
    "render_manual_candidate_snapshot",
]
