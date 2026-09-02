"""Traceability contracts for future reviewed methodology behaviors."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SourceClassification


@dataclass(frozen=True, slots=True)
class TraceabilityRecord:
    behavior_id: str
    protected_source_file: str
    source_principle_id: str | None
    source_classification: SourceClassification
    implementation_module: str
    covering_tests: tuple[str, ...]
    unresolved_note: str | None = None


@dataclass(frozen=True, slots=True)
class TraceabilityMatrix:
    records: tuple[TraceabilityRecord, ...] = ()

