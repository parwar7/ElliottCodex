import inspect
import math
import unittest

import support
from elliott_methodology_kernel import (
    CandidateScope,
    ExecutionRole,
    ImpulseDirection,
    P004Input,
    RuleCheckStatus,
    check_p004,
)
from elliott_methodology_kernel.models import SourceClassification


def candidate(
    direction=ImpulseDirection.UP,
    origin=100.0,
    extreme=101.0,
    scope=CandidateScope.NORMAL_IMPULSE,
):
    return P004Input(
        candidate_scope=scope,
        direction=direction,
        wave1_origin=origin,
        wave2_retracement_extreme=extreme,
    )


class P004Tests(unittest.TestCase):
    def test_upward_extreme_above_origin_satisfies_rule(self) -> None:
        self.assertEqual(
            RuleCheckStatus.RULE_SATISFIED,
            check_p004(candidate(extreme=100.01)).status,
        )

    def test_upward_extreme_equal_to_origin_satisfies_rule(self) -> None:
        self.assertEqual(
            RuleCheckStatus.RULE_SATISFIED,
            check_p004(candidate(extreme=100.0)).status,
        )

    def test_upward_extreme_below_origin_violates_rule(self) -> None:
        result = check_p004(candidate(extreme=99.99))
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_downward_extreme_below_origin_satisfies_rule(self) -> None:
        result = check_p004(
            candidate(direction=ImpulseDirection.DOWN, extreme=99.99)
        )
        self.assertEqual(RuleCheckStatus.RULE_SATISFIED, result.status)

    def test_downward_extreme_equal_to_origin_satisfies_rule(self) -> None:
        result = check_p004(
            candidate(direction=ImpulseDirection.DOWN, extreme=100.0)
        )
        self.assertEqual(RuleCheckStatus.RULE_SATISFIED, result.status)

    def test_downward_extreme_above_origin_violates_rule(self) -> None:
        result = check_p004(
            candidate(direction=ImpulseDirection.DOWN, extreme=100.01)
        )
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, result.status)
        self.assertTrue(result.fatal_to_candidate)

    def test_missing_wave1_origin_is_unresolved(self) -> None:
        result = check_p004(candidate(origin=None))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_missing_wave2_extreme_is_unresolved(self) -> None:
        result = check_p004(candidate(extreme=None))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_non_finite_price_is_unresolved(self) -> None:
        result = check_p004(candidate(extreme=math.nan))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_boolean_wave1_origin_is_unresolved(self) -> None:
        result = check_p004(candidate(origin=True))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_boolean_wave2_extreme_is_unresolved(self) -> None:
        result = check_p004(candidate(extreme=False))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_numeric_string_price_is_unresolved(self) -> None:
        result = check_p004(candidate(origin="100.0"))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_empty_string_price_is_unresolved(self) -> None:
        result = check_p004(candidate(extreme=""))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_finite_integer_prices_are_evaluated_normally(self) -> None:
        satisfied = check_p004(candidate(origin=100, extreme=101))
        violated = check_p004(candidate(origin=100, extreme=99))
        self.assertEqual(RuleCheckStatus.RULE_SATISFIED, satisfied.status)
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, violated.status)

    def test_positive_infinity_is_unresolved(self) -> None:
        result = check_p004(candidate(extreme=math.inf))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_negative_infinity_is_unresolved(self) -> None:
        result = check_p004(candidate(extreme=-math.inf))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_unknown_direction_is_unresolved(self) -> None:
        result = check_p004(candidate(direction=ImpulseDirection.UNKNOWN))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)

    def test_non_normal_impulse_scope_is_unsupported(self) -> None:
        result = check_p004(candidate(scope="DIAGONAL"))
        self.assertEqual(
            RuleCheckStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
            result.status,
        )

    def test_raw_normal_impulse_scope_matches_enum_behavior(self) -> None:
        enum_result = check_p004(candidate(scope=CandidateScope.NORMAL_IMPULSE))
        raw_result = check_p004(candidate(scope="NORMAL_IMPULSE"))
        self.assertEqual(enum_result.status, raw_result.status)

    def test_raw_up_direction_matches_enum_behavior(self) -> None:
        enum_result = check_p004(candidate(direction=ImpulseDirection.UP, extreme=99.0))
        raw_result = check_p004(candidate(direction="UP", extreme=99.0))
        self.assertEqual(enum_result.status, raw_result.status)
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, raw_result.status)

    def test_raw_down_direction_matches_enum_behavior(self) -> None:
        enum_result = check_p004(candidate(direction=ImpulseDirection.DOWN, extreme=101.0))
        raw_result = check_p004(candidate(direction="DOWN", extreme=101.0))
        self.assertEqual(enum_result.status, raw_result.status)
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, raw_result.status)

    def test_unknown_raw_direction_is_unresolved(self) -> None:
        result = check_p004(candidate(direction="SIDEWAYS"))
        self.assertEqual(RuleCheckStatus.UNRESOLVED_MISSING_INPUT, result.status)
        self.assertNotEqual(RuleCheckStatus.RULE_SATISFIED, result.status)

    def test_rule_has_no_evidence_inputs(self) -> None:
        fields = tuple(P004Input.__dataclass_fields__)
        self.assertEqual(
            (
                "candidate_scope",
                "direction",
                "wave1_origin",
                "wave2_retracement_extreme",
            ),
            fields,
        )
        self.assertEqual(("candidate",), tuple(inspect.signature(check_p004).parameters))

    def test_violation_cannot_be_overridden_by_external_evidence(self) -> None:
        violating = candidate(extreme=99.99)
        with self.assertRaises(TypeError):
            check_p004(violating, fibonacci="SUPPORTS", volume="SUPPORTS")
        self.assertEqual(
            RuleCheckStatus.RULE_VIOLATED,
            check_p004(violating).status,
        )

    def test_no_hidden_numeric_tolerance(self) -> None:
        immediately_below = math.nextafter(100.0, -math.inf)
        result = check_p004(candidate(extreme=immediately_below))
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, result.status)

    def test_upward_immediately_above_origin_satisfies_rule(self) -> None:
        immediately_above = math.nextafter(100.0, math.inf)
        result = check_p004(candidate(extreme=immediately_above))
        self.assertEqual(RuleCheckStatus.RULE_SATISFIED, result.status)

    def test_downward_immediately_above_origin_violates_rule(self) -> None:
        immediately_above = math.nextafter(100.0, math.inf)
        result = check_p004(
            candidate(direction=ImpulseDirection.DOWN, extreme=immediately_above)
        )
        self.assertEqual(RuleCheckStatus.RULE_VIOLATED, result.status)

    def test_downward_immediately_below_origin_satisfies_rule(self) -> None:
        immediately_below = math.nextafter(100.0, -math.inf)
        result = check_p004(
            candidate(direction=ImpulseDirection.DOWN, extreme=immediately_below)
        )
        self.assertEqual(RuleCheckStatus.RULE_SATISFIED, result.status)

    def test_traceability_is_complete(self) -> None:
        result = check_p004(candidate())
        self.assertEqual("P004", result.principle_id)
        self.assertEqual(SourceClassification.RULE, result.source_class)
        self.assertEqual(ExecutionRole.HARD_VALIDATION, result.execution_role)
        self.assertEqual("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", result.behavior_id)
        self.assertEqual(result.status.value, result.outcome)
        self.assertTrue(result.reason)
        self.assertIn("docs/elliott/PATTERN_BRAIN.md#A-normal-impulse-rule-1", result.protected_sources)

    def test_traceability_is_complete_for_every_status_family(self) -> None:
        results = (
            check_p004(candidate()),
            check_p004(candidate(extreme=99.0)),
            check_p004(candidate(origin=None)),
            check_p004(candidate(scope="DIAGONAL")),
        )
        expected_statuses = {
            RuleCheckStatus.RULE_SATISFIED,
            RuleCheckStatus.RULE_VIOLATED,
            RuleCheckStatus.UNRESOLVED_MISSING_INPUT,
            RuleCheckStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
        }
        self.assertEqual(expected_statuses, {result.status for result in results})
        for result in results:
            with self.subTest(status=result.status):
                self.assertEqual("P004", result.principle_id)
                self.assertEqual(SourceClassification.RULE, result.source_class)
                self.assertEqual(ExecutionRole.HARD_VALIDATION, result.execution_role)
                self.assertEqual(
                    "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                    result.behavior_id,
                )
                self.assertTrue(result.protected_sources)
                self.assertTrue(result.reason)
                self.assertEqual(result.status.value, result.outcome)

    def test_satisfied_and_unresolved_results_are_not_fatal(self) -> None:
        self.assertFalse(check_p004(candidate()).fatal_to_candidate)
        self.assertFalse(check_p004(candidate(origin=None)).fatal_to_candidate)

    def test_only_rule_violation_is_fatal_to_candidate(self) -> None:
        results = {
            RuleCheckStatus.RULE_SATISFIED: check_p004(candidate()),
            RuleCheckStatus.RULE_VIOLATED: check_p004(candidate(extreme=99.0)),
            RuleCheckStatus.UNRESOLVED_MISSING_INPUT: check_p004(
                candidate(origin=None)
            ),
            RuleCheckStatus.UNRESOLVED_UNSUPPORTED_SCOPE: check_p004(
                candidate(scope="DIAGONAL")
            ),
        }
        for status, result in results.items():
            with self.subTest(status=status):
                self.assertEqual(
                    status is RuleCheckStatus.RULE_VIOLATED,
                    result.fatal_to_candidate,
                )


if __name__ == "__main__":
    unittest.main()
