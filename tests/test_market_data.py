import json
from pathlib import Path
import tempfile
import unittest

import support
from elliott_methodology_kernel.models import MarketType, SymbolIdentity, Timeframe
from elliott_runtime.market_data import MarketDataError, load_csv, load_json


SYMBOL = SymbolIdentity("TEST", MarketType.OTHER)
HOURLY = Timeframe("1H", 3600)


class MarketDataTests(unittest.TestCase):
    def test_csv_normalization_duplicate_missing_and_provenance(self) -> None:
        content = (
            "timestamp,open,high,low,close,volume\n"
            "2026-01-01T03:00:00Z,3,4,2,3.5,12\n"
            "2026-01-01T00:00:00Z,1,2,0.5,1.5,10\n"
            "2026-01-01T01:00:00Z,2,3,1,2.5,11\n"
            "2026-01-01T01:00:00Z,2,3,1,2.5,11\n"
        )
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            path = Path(directory) / "bars.csv"
            path.write_text(content, encoding="utf-8")
            result = load_csv(path, SYMBOL, HOURLY)
        self.assertEqual(4, len(result.bars))
        self.assertEqual("2026-01-01T00:00:00+00:00", result.bars[0].timestamp_utc.isoformat())
        self.assertEqual(("2026-01-01T01:00:00+00:00",), result.quality.duplicate_timestamps_utc)
        self.assertEqual(1, result.quality.missing_intervals[0].missing_bar_count)
        self.assertTrue(result.quality.volume_complete)
        self.assertFalse(result.provenance.resampled)
        self.assertEqual(2, result.bars[0].provenance.source_record_index)
        self.assertEqual("csv", result.provenance.source_type)
        self.assertFalse(result.bars[0].provenance.naive_timezone_assumed_utc)

    def test_json_normalization_preserves_missing_volume(self) -> None:
        payload = {"bars": [{
            "timestamp": "2026-01-01T00:00:00+02:00",
            "open": 1,
            "high": 2,
            "low": 0.5,
            "close": 1.5,
        }]}
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            path = Path(directory) / "bars.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = load_json(path, SYMBOL, HOURLY)
        self.assertEqual("2025-12-31T22:00:00+00:00", result.bars[0].timestamp_utc.isoformat())
        self.assertFalse(result.quality.volume_available)
        self.assertFalse(result.quality.volume_complete)
        self.assertEqual("json", result.provenance.source_type)
        self.assertFalse(result.bars[0].provenance.naive_timezone_assumed_utc)

    def test_naive_timestamp_assumption_is_explicitly_recorded(self) -> None:
        payload = [{
            "timestamp": "2026-01-01T00:00:00",
            "open": 1,
            "high": 2,
            "low": 0.5,
            "close": 1.5,
        }]
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            path = Path(directory) / "naive.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = load_json(path, SYMBOL, HOURLY)
        bar = result.bars[0]
        self.assertEqual("2026-01-01T00:00:00", bar.provenance.source_timestamp)
        self.assertEqual("2026-01-01T00:00:00+00:00", bar.timestamp_utc.isoformat())
        self.assertTrue(bar.provenance.naive_timezone_assumed_utc)

    def test_malformed_ohlc_is_rejected(self) -> None:
        payload = [{
            "timestamp": "2026-01-01T00:00:00Z",
            "open": 10,
            "high": 9,
            "low": 8,
            "close": 9,
        }]
        with tempfile.TemporaryDirectory(dir=support.RUNTIME_ROOT / "tests") as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(MarketDataError):
                load_json(path, SYMBOL, HOURLY)


if __name__ == "__main__":
    unittest.main()
