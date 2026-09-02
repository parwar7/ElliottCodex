from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import support
from elliott_methodology_kernel import MethodologyKernel
from elliott_methodology_kernel.models import (
    AnalysisRequest,
    DataProvenance,
    DataQualityReport,
    KernelStatus,
    MarketType,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)
from elliott_runtime.pipelines.analyze import run_analysis


class KernelContractTests(unittest.TestCase):
    def test_analysis_is_explicitly_not_implemented_and_unresolved(self) -> None:
        timeframe = Timeframe("1H", 3600)
        observations = NormalizedMarketObservations(
            symbol=SymbolIdentity("TEST", MarketType.OTHER),
            timeframe=timeframe,
            bars=(),
            provenance=DataProvenance(
                source_type="test",
                source_identifier="memory",
                source_sha256="0" * 64,
                source_resolution=timeframe,
                ingested_at_utc=datetime.now(timezone.utc).isoformat(),
            ),
            quality=DataQualityReport(),
        )
        request = AnalysisRequest(
            observations=observations,
            requested_at_utc=datetime.now(timezone.utc).isoformat(),
            request_id="request-1",
        )
        kernel = MethodologyKernel(support.PROTECTED_ROOT)
        result = run_analysis(kernel, request)
        self.assertEqual(KernelStatus.NOT_IMPLEMENTED, result.status)
        self.assertIsNone(result.analysis)
        self.assertTrue(result.unresolved.items)

    def test_runtime_pipeline_accepts_only_public_port_behavior(self) -> None:
        class FakeKernel:
            def __init__(self) -> None:
                self.request = None

            def analyze(self, request):
                self.request = request
                return "transported"

        fake = FakeKernel()
        marker = object()
        self.assertEqual("transported", run_analysis(fake, marker))
        self.assertIs(marker, fake.request)


if __name__ == "__main__":
    unittest.main()

