import inspect
import unittest

import support
from elliott_methodology_kernel import (
    DegreePeerCheckStatus,
    DegreePeerConsistencyInput,
    DegreePeerExecutionRole,
    check_degree_peer_consistency,
)
from elliott_methodology_kernel.models import (
    DegreeStatus,
    DegreeTreeNode,
    InternalStatus,
    SourceClassification,
)


def child(label: str, degree: str | None, *, resolved: bool = True) -> DegreeTreeNode:
    return DegreeTreeNode(
        label=label,
        degree=degree,
        degree_status=DegreeStatus.RESOLVED if resolved else DegreeStatus.UNRESOLVED,
        internal_status=InternalStatus.UNRESOLVED,
        parent_label="parent",
    )


def candidate(*children: DegreeTreeNode, parent_node_id: str | None = "parent"):
    return DegreePeerConsistencyInput(
        parent_node_id=parent_node_id,
        direct_child_degrees=tuple(children),
    )


class DegreePeerConsistencyTests(unittest.TestCase):
    def test_two_identical_resolved_peers_satisfy(self) -> None:
        result = check_degree_peer_consistency(
            candidate(child("1", "Minor"), child("2", "Minor"))
        )
        self.assertEqual(DegreePeerCheckStatus.RULE_SATISFIED, result.status)
        self.assertFalse(result.fatal_to_candidate)

    def test_three_identical_resolved_peers_satisfy(self) -> None:
        result = check_degree_peer_consistency(
            candidate(
                child("1", "Intermediate"),
                child("2", "Intermediate"),
                child("3", "Intermediate"),
            )
        )
        self.assertEqual(DegreePeerCheckStatus.RULE_SATISFIED, result.status)

    def test_two_different_resolved_peers_violate_and_are_fatal(self) -> None:
        result = check_degree_peer_consistency(
            candidate(child("1", "Minor"), child("2", "Intermediate"))
        )
        self.assertEqual(DegreePeerCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_later_child_difference_violates_and_is_fatal(self) -> None:
        result = check_degree_peer_consistency(
            candidate(
                child("1", "Minor"),
                child("2", "Minor"),
                child("3", "Minute"),
            )
        )
        self.assertEqual(DegreePeerCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_one_unresolved_child_makes_whole_check_unresolved(self) -> None:
        result = check_degree_peer_consistency(
            candidate(child("1", "Minor"), child("2", None, resolved=False))
        )
        self.assertEqual(
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )
        self.assertFalse(result.fatal_to_candidate)

    def test_multiple_unresolved_peers_are_unresolved(self) -> None:
        result = check_degree_peer_consistency(
            candidate(
                child("1", None, resolved=False),
                child("2", None, resolved=False),
                child("3", "Minor"),
            )
        )
        self.assertEqual(
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_all_unresolved_peers_are_unresolved(self) -> None:
        result = check_degree_peer_consistency(
            candidate(
                child("1", None, resolved=False),
                child("2", None, resolved=False),
            )
        )
        self.assertEqual(
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_zero_children_are_insufficient(self) -> None:
        result = check_degree_peer_consistency(candidate())
        self.assertEqual(
            DegreePeerCheckStatus.UNRESOLVED_INSUFFICIENT_PEERS, result.status
        )
        self.assertFalse(result.fatal_to_candidate)

    def test_one_child_is_insufficient(self) -> None:
        result = check_degree_peer_consistency(candidate(child("1", "Minor")))
        self.assertEqual(
            DegreePeerCheckStatus.UNRESOLVED_INSUFFICIENT_PEERS, result.status
        )

    def test_parent_degree_is_absent_and_has_no_effect(self) -> None:
        fields = DegreePeerConsistencyInput.__dataclass_fields__
        self.assertNotIn("parent_degree", fields)
        result = check_degree_peer_consistency(
            candidate(child("1", "Primary"), child("2", "Primary"))
        )
        self.assertEqual(DegreePeerCheckStatus.RULE_SATISFIED, result.status)

    def test_missing_parent_identity_is_unresolved(self) -> None:
        result = check_degree_peer_consistency(
            candidate(child("1", "Minor"), child("2", "Minor"), parent_node_id=None)
        )
        self.assertEqual(
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT, result.status
        )

    def test_no_time_duration_price_or_parent_degree_inputs_exist(self) -> None:
        fields = set(DegreePeerConsistencyInput.__dataclass_fields__)
        self.assertEqual({"parent_node_id", "direct_child_degrees"}, fields)
        for forbidden in ("timeframe", "duration", "price", "parent_degree"):
            self.assertNotIn(forbidden, fields)

    def test_no_hierarchy_step_or_degree_assignment_occurs(self) -> None:
        supplied = candidate(child("1", "Primary"), child("2", "Primary"))
        before = tuple(node.degree for node in supplied.direct_child_degrees)
        result = check_degree_peer_consistency(supplied)
        after = tuple(node.degree for node in supplied.direct_child_degrees)
        self.assertEqual(DegreePeerCheckStatus.RULE_SATISFIED, result.status)
        self.assertEqual(before, after)

    def test_satisfaction_does_not_claim_candidate_validity(self) -> None:
        result = check_degree_peer_consistency(
            candidate(child("1", "Minor"), child("2", "Minor"))
        )
        self.assertFalse(result.fatal_to_candidate)
        self.assertIn("no broader candidate validity", result.reason.lower())

    def test_every_status_family_has_complete_traceability(self) -> None:
        cases = (
            check_degree_peer_consistency(
                candidate(child("1", "Minor"), child("2", "Minor"))
            ),
            check_degree_peer_consistency(
                candidate(child("1", "Minor"), child("2", "Minute"))
            ),
            check_degree_peer_consistency(
                candidate(child("1", "Minor"), child("2", None, resolved=False))
            ),
            check_degree_peer_consistency(candidate()),
        )
        self.assertEqual(set(DegreePeerCheckStatus), {result.status for result in cases})
        for result in cases:
            self.assertIsNone(result.source_principle_id)
            self.assertEqual(SourceClassification.DEFINITION, result.source_class)
            self.assertEqual(
                DegreePeerExecutionRole.HARD_VALIDATION, result.execution_role
            )
            self.assertEqual(
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY", result.behavior_id
            )
            self.assertTrue(result.protected_sources)
            self.assertEqual(result.status.value, result.outcome)
            self.assertTrue(result.reason)

    def test_only_mixed_resolved_peers_are_fatal(self) -> None:
        cases = {
            DegreePeerCheckStatus.RULE_SATISFIED: check_degree_peer_consistency(
                candidate(child("1", "Minor"), child("2", "Minor"))
            ),
            DegreePeerCheckStatus.RULE_VIOLATED: check_degree_peer_consistency(
                candidate(child("1", "Minor"), child("2", "Minute"))
            ),
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT: check_degree_peer_consistency(
                candidate(child("1", "Minor"), child("2", None, resolved=False))
            ),
            DegreePeerCheckStatus.UNRESOLVED_INSUFFICIENT_PEERS: check_degree_peer_consistency(
                candidate()
            ),
        }
        for status, result in cases.items():
            self.assertEqual(
                status == DegreePeerCheckStatus.RULE_VIOLATED,
                result.fatal_to_candidate,
            )

    def test_behavior_has_no_forbidden_dependencies_or_inputs(self) -> None:
        module = inspect.getmodule(check_degree_peer_consistency)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        for forbidden in (
            "elliott_runtime",
            "TradingView",
            "market_data",
            "provider",
            "EvidenceState",
            "CountRank",
            "Fibonacci",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
