"""Core circuit breaker: spend accounting, threshold checks, approval-hook
trigger, and kill logic.
"""

from .loop_detector import LoopDetector


class GuardTripped(Exception):
    """Raised when the circuit breaker trips a run."""

    def __init__(self, reason, detail=None):
        self.reason = reason  # "spend_cap" | "loop_detected" | "approval_denied"
        self.detail = detail
        message = f"{reason}: {detail}" if detail else reason
        super().__init__(message)


class SpendCapGuard:
    """Wraps an agent loop and trips a GuardTripped circuit breaker when:

    - cumulative spend exceeds ``spend_cap`` (hard stop), or
    - a human declines to approve continuing past ``soft_threshold`` (if an
      ``approval_hook`` is configured), or
    - ``max_consecutive_similar`` steps in a row look like semantic
      re-planning of the same idea (loop detection).
    """

    def __init__(
        self,
        spend_cap,
        soft_threshold_fraction=None,
        similarity_threshold=0.6,
        max_consecutive_similar=3,
        window=5,
        approval_hook=None,
    ):
        self.spend_cap = spend_cap
        self.soft_threshold = (
            spend_cap * soft_threshold_fraction if soft_threshold_fraction else None
        )
        self.approval_hook = approval_hook

        self.total_cost = 0.0
        self.steps_run = 0
        self._soft_triggered = False

        self.loop_detector = LoopDetector(
            similarity_threshold=similarity_threshold,
            max_consecutive_similar=max_consecutive_similar,
            window=window,
        )

    def check_step(self, step_text, cost):
        """Record one agent step. Returns a status dict, or raises GuardTripped."""
        self.total_cost += cost
        self.steps_run += 1

        if self.total_cost > self.spend_cap:
            raise GuardTripped(
                "spend_cap",
                f"total spend ${self.total_cost:.2f} exceeded cap ${self.spend_cap:.2f}",
            )

        if (
            self.soft_threshold is not None
            and not self._soft_triggered
            and self.total_cost >= self.soft_threshold
        ):
            self._soft_triggered = True
            approved = self.approval_hook(self) if self.approval_hook else True
            if not approved:
                raise GuardTripped(
                    "approval_denied",
                    f"run paused at soft threshold ${self.soft_threshold:.2f}, "
                    "human declined to continue",
                )

        if self.loop_detector.observe(step_text):
            raise GuardTripped(
                "loop_detected",
                f"{self.loop_detector.max_consecutive_similar} consecutive "
                "semantically similar steps",
            )

        return {
            "step": self.steps_run,
            "cost": cost,
            "total_cost": self.total_cost,
            "similarity": self.loop_detector.last_similarity,
        }
