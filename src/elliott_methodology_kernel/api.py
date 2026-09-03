"""The only public invocation boundary for methodology behavior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .brain import BrainManifest, DEFAULT_PROTECTED_ROOT, load_brain_manifest
from .models import AnalysisRequest, AnalysisResultEnvelope, KernelStatus, UnresolvedState
from .schema import assert_valid, load_protected_output_schema
from .single_candidate_orchestration import (
    SingleCandidateAnalysisRequest,
    SingleCandidateAnalysisResult,
    _orchestrate_single_candidate,
)
from .explicit_behavior_execution import (
    ExplicitBehaviorExecutionRequest,
    ExplicitBehaviorExecutionResult,
    _execute_candidate_inputs,
)
from .manual_structure_candidate_builder import (
    ManualStructureCandidateBuildResult,
    ManualStructureCandidateRequest,
    _build_manual_candidate,
)
from .bounded_manual_chart_analysis import (
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
    _analyze_bounded_manual_chart,
)


KERNEL_VERSION = "0.1.0-phase1-contract"


class MethodologyKernel:
    """Phase 1 contract implementation; substantive methodology is absent."""

    def __init__(self, protected_root: str | Path = DEFAULT_PROTECTED_ROOT) -> None:
        self._brain_manifest: BrainManifest = load_brain_manifest(protected_root)
        self._schema = load_protected_output_schema(protected_root)

    @property
    def brain_manifest(self) -> BrainManifest:
        return self._brain_manifest

    def validate_analysis_output(self, output: Mapping[str, Any]) -> None:
        assert_valid(dict(output), self._schema)

    def analyze(self, request: AnalysisRequest) -> AnalysisResultEnvelope:
        """Return an explicit unresolved result until reviewed methodology exists."""
        manifest_reference = hashlib.sha256(
            json.dumps(
                self._brain_manifest.observed_hashes,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return AnalysisResultEnvelope(
            request_id=request.request_id,
            status=KernelStatus.NOT_IMPLEMENTED,
            unresolved=UnresolvedState(
                items=(
                    "Substantive Elliott methodology is not implemented in Phase 1.",
                )
            ),
            analysis=None,
            brain_manifest_reference=manifest_reference,
            kernel_version=KERNEL_VERSION,
        )

    def analyze_candidate(
        self,
        request: SingleCandidateAnalysisRequest,
    ) -> SingleCandidateAnalysisResult:
        """Verify and summarize one exact caller-supplied candidate package."""
        manifest_reference = hashlib.sha256(
            json.dumps(
                self._brain_manifest.observed_hashes,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return _orchestrate_single_candidate(
            request,
            brain_manifest_reference=manifest_reference,
            kernel_version=KERNEL_VERSION,
        )

    def analyze_candidate_inputs(
        self,
        request: ExplicitBehaviorExecutionRequest,
    ) -> ExplicitBehaviorExecutionResult:
        """Execute exact supplied behavior inputs, then reuse candidate orchestration."""
        return _execute_candidate_inputs(request, self.analyze_candidate)

    def analyze_manual_candidate(
        self,
        request: ManualStructureCandidateRequest,
    ) -> ManualStructureCandidateBuildResult:
        """Build exact inputs from explicit manual facts, then reuse execution."""
        return _build_manual_candidate(request, self.analyze_candidate_inputs)

    def analyze_bounded_manual_chart(
        self,
        request: BoundedManualChartAnalysisRequest,
    ) -> BoundedManualChartAnalysisResult:
        """Run the bounded end-to-end workflow for one explicit manual candidate."""
        return _analyze_bounded_manual_chart(request, self.analyze_manual_candidate)
