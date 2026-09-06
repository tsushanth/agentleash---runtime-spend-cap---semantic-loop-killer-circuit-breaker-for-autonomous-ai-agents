import unittest

from agentleash import SpendCapGuard, GuardTripped


class TestSpendCapGuard(unittest.TestCase):
    def test_trips_at_the_right_cumulative_cost(self):
        guard = SpendCapGuard(spend_cap=1.0, similarity_threshold=1.1)
        costs = [0.4, 0.4, 0.4]  # cumulative: 0.4, 0.8, 1.2 -> crosses cap on step 3

        guard.check_step("do thing one", costs[0])
        guard.check_step("do thing two", costs[1])

        with self.assertRaises(GuardTripped) as ctx:
            guard.check_step("do thing three", costs[2])

        self.assertEqual(ctx.exception.reason, "spend_cap")
        self.assertEqual(guard.steps_run, 3)
        self.assertAlmostEqual(guard.total_cost, 1.2)

    def test_does_not_trip_before_cap_is_crossed(self):
        guard = SpendCapGuard(spend_cap=10.0, similarity_threshold=1.1)

        for i in range(5):
            result = guard.check_step(f"distinct step number {i}", 1.0)
            self.assertEqual(result["total_cost"], i + 1)

        self.assertEqual(guard.steps_run, 5)

    def test_approval_hook_can_deny_and_trip_the_run(self):
        guard = SpendCapGuard(
            spend_cap=10.0,
            soft_threshold_fraction=0.5,  # soft threshold = 5.0
            similarity_threshold=1.1,
            approval_hook=lambda g: False,
        )

        guard.check_step("step one", 3.0)
        with self.assertRaises(GuardTripped) as ctx:
            guard.check_step("step two", 3.0)  # crosses soft threshold of 5.0

        self.assertEqual(ctx.exception.reason, "approval_denied")

    def test_approval_hook_can_approve_and_continue(self):
        guard = SpendCapGuard(
            spend_cap=10.0,
            soft_threshold_fraction=0.5,
            similarity_threshold=1.1,
            approval_hook=lambda g: True,
        )

        guard.check_step("step one", 3.0)
        result = guard.check_step("step two", 3.0)  # crosses soft threshold, approved

        self.assertEqual(result["total_cost"], 6.0)
        self.assertEqual(guard.steps_run, 2)


if __name__ == "__main__":
    unittest.main()
