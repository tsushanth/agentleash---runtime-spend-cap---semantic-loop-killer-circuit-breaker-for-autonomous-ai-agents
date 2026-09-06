"""`python -m agentleash demo` entry point."""

import argparse
import json
import sys

from .guard import SpendCapGuard, GuardTripped


def _load_steps(mode):
    # Imported lazily so `import agentleash` never requires the examples/
    # package to be on the path.
    from examples.fake_agent import generate_steps

    return generate_steps(mode)


def _make_approval_hook(approval_mode):
    if approval_mode != "prompt":
        return None

    def approval_hook(guard):
        answer = input(
            f"\n[AgentLeash] Soft threshold reached "
            f"(${guard.total_cost:.2f} / ${guard.spend_cap:.2f} spend cap). "
            "Approve continuing this run? [y/N] "
        )
        return answer.strip().lower() == "y"

    return approval_hook


def run_demo(args):
    with open(args.config) as f:
        config = json.load(f)

    steps = _load_steps(args.mode)
    guard = SpendCapGuard(
        spend_cap=config["spend_cap"],
        soft_threshold_fraction=config.get("soft_threshold_fraction"),
        similarity_threshold=config.get("similarity_threshold", 0.6),
        max_consecutive_similar=config.get("max_consecutive_similar", 3),
        approval_hook=_make_approval_hook(args.approval_mode),
    )

    print(f"AgentLeash demo — mode={args.mode!r} spend_cap=${guard.spend_cap:.2f}")
    print("-" * 64)

    for step_text, cost in steps:
        try:
            result = guard.check_step(step_text, cost)
        except GuardTripped as e:
            print(
                f"[step {guard.steps_run:>2}] cost=${cost:.2f} "
                f"total=${guard.total_cost:.2f} "
                f"similarity={guard.loop_detector.last_similarity:.2f}  "
                f"\"{step_text}\""
            )
            print("-" * 64)
            print(f"CIRCUIT BREAKER TRIPPED — {e.reason}: {e.detail}")
            print(
                f"Halted after {guard.steps_run}/{len(steps)} scripted steps, "
                f"total spend ${guard.total_cost:.2f}."
            )
            return 1

        print(
            f"[step {result['step']:>2}] cost=${result['cost']:.2f} "
            f"total=${result['total_cost']:.2f} "
            f"similarity={result['similarity']:.2f}  "
            f"\"{step_text}\""
        )

    print("-" * 64)
    print(
        f"Run completed normally — {guard.steps_run} steps, "
        f"total spend ${guard.total_cost:.2f}, no trip."
    )
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="agentleash")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the scripted fake-agent demo")
    demo.add_argument(
        "--mode", choices=["normal", "runaway"], default="normal",
        help="Which scripted fake-agent run to play back (default: normal)",
    )
    demo.add_argument(
        "--config", default="examples/config.json",
        help="Path to the guard config JSON (default: examples/config.json)",
    )
    demo.add_argument(
        "--approval-mode", choices=["none", "prompt"], default="none",
        help="If 'prompt', pause at the soft spend threshold for a y/n approval",
    )
    demo.set_defaults(func=run_demo)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
