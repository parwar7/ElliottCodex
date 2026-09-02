"""Logical development audit contracts; no physical sealing is claimed."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


DEVELOPMENT_RUN_HISTORY_MODE = "DEVELOPMENT_LOGICAL_WRITE_ONCE"


@dataclass(frozen=True, slots=True)
class DevelopmentRunEnvelope:
    run_id: str
    created_at_utc: str
    input_hash: str
    brain_manifest_reference: str
    kernel_version: str
    kernel_hash: str
    audit_events: tuple["AuditEvent", ...] = ()
    run_history_mode: str = DEVELOPMENT_RUN_HISTORY_MODE


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    run_id: str
    timestamp_utc: str
    previous_event_hash: str | None
    input_hash: str
    brain_manifest_reference: str
    kernel_version: str
    kernel_hash: str
    event_type: str
    state_transition: Mapping[str, Any]
    provenance: Mapping[str, Any]
    run_history_mode: str = DEVELOPMENT_RUN_HISTORY_MODE

    def event_hash(self) -> str:
        encoded = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
