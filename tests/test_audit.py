import unittest

import support
from elliott_methodology_kernel.audit import (
    AuditEvent,
    DevelopmentRunEnvelope,
    DEVELOPMENT_RUN_HISTORY_MODE,
)


class AuditContractTests(unittest.TestCase):
    def test_audit_event_is_logically_labeled_and_hashable(self) -> None:
        event = AuditEvent(
            event_id="event-1",
            run_id="run-1",
            timestamp_utc="2026-01-01T00:00:00+00:00",
            previous_event_hash=None,
            input_hash="a" * 64,
            brain_manifest_reference="b" * 64,
            kernel_version="0.1.0-phase1-contract",
            kernel_hash="c" * 64,
            event_type="RUN_CREATED",
            state_transition={"from": None, "to": "NOT_IMPLEMENTED"},
            provenance={"source": "test"},
        )
        self.assertEqual(DEVELOPMENT_RUN_HISTORY_MODE, event.run_history_mode)
        self.assertEqual(64, len(event.event_hash()))

        run = DevelopmentRunEnvelope(
            run_id="run-1",
            created_at_utc="2026-01-01T00:00:00+00:00",
            input_hash="a" * 64,
            brain_manifest_reference="b" * 64,
            kernel_version="0.1.0-phase1-contract",
            kernel_hash="c" * 64,
            audit_events=(event,),
        )
        self.assertEqual(DEVELOPMENT_RUN_HISTORY_MODE, run.run_history_mode)
        self.assertEqual((event,), run.audit_events)


if __name__ == "__main__":
    unittest.main()
