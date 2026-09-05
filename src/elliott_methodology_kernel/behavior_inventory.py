"""Complete executable inventory, including dedicated sufficiency-only APIs.

The legacy candidate-envelope compatibility table describes its ten supported
transports, not the complete Kernel inventory after the P005 additive API.
"""
from .candidate_analysis_envelope import _BEHAVIOR_COMPATIBILITY
from .p005_percentage_sufficiency import P005_BEHAVIOR_ID

EXECUTABLE_BEHAVIOR_IDS = tuple(item.behavior_id for item in _BEHAVIOR_COMPATIBILITY) + (P005_BEHAVIOR_ID,)
