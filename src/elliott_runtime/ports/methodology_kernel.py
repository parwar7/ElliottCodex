"""The sole Runtime-facing Methodology Kernel interface."""

from __future__ import annotations

from typing import Protocol

from elliott_methodology_kernel.contracts import AnalysisRequest, AnalysisResultEnvelope


class MethodologyKernelPort(Protocol):
    def analyze(self, request: AnalysisRequest) -> AnalysisResultEnvelope: ...
