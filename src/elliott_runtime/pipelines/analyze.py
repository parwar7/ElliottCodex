"""Transport an analysis request through the public Kernel port."""

from __future__ import annotations

from elliott_methodology_kernel.contracts import AnalysisRequest, AnalysisResultEnvelope
from elliott_runtime.ports.methodology_kernel import MethodologyKernelPort


def run_analysis(
    kernel: MethodologyKernelPort,
    request: AnalysisRequest,
) -> AnalysisResultEnvelope:
    return kernel.analyze(request)
