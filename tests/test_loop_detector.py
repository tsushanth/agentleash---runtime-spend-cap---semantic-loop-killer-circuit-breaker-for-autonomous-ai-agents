import unittest

from agentleash import LoopDetector


class TestLoopDetector(unittest.TestCase):
    def test_flags_a_loop_after_n_paraphrased_similar_steps(self):
        detector = LoopDetector(similarity_threshold=0.5, max_consecutive_similar=3)

        # First step sets the baseline (nothing to compare against yet), then
        # three paraphrased re-plans of the same failed API call in a row.
        steps = [
            "Retry fetching the invoices from the billing API",
            "Try fetching the invoices from the billing API again",
            "Attempt to fetch the invoices from the billing API again",
            "One more retry to fetch the invoices from the billing API",
        ]

        tripped_flags = [detector.observe(s) for s in steps]

        self.assertFalse(tripped_flags[0])
        self.assertFalse(tripped_flags[1])
        self.assertFalse(tripped_flags[2])
        self.assertTrue(tripped_flags[3])

    def test_does_not_false_positive_on_genuinely_distinct_steps(self):
        detector = LoopDetector(similarity_threshold=0.6, max_consecutive_similar=3)

        steps = [
            "Look up the user's account details",
            "Draft a response email to the customer",
            "Check the response for policy compliance",
            "Send the reply and close the ticket",
        ]

        tripped_flags = [detector.observe(s) for s in steps]

        self.assertFalse(any(tripped_flags))

    def test_dissimilar_step_resets_the_consecutive_count(self):
        detector = LoopDetector(similarity_threshold=0.5, max_consecutive_similar=3)

        detector.observe("Retry fetching the invoices from the billing API")
        detector.observe("Try fetching the invoices from the billing API again")
        tripped = detector.observe("Send the final report to the customer by email")

        self.assertFalse(tripped)
        self.assertEqual(detector._consecutive, 0)


if __name__ == "__main__":
    unittest.main()
