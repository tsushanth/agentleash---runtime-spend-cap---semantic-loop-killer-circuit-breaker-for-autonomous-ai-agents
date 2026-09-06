# AgentLeash

A tiny, framework-agnostic circuit breaker for autonomous AI agent loops.

Wrap whatever function makes your "LLM call" (real or fake) and AgentLeash will:

- **Enforce a hard dollar spend cap** — trip the breaker the instant cumulative
  cost crosses the configured limit.
- **Detect semantic re-planning loops** — catch an agent that keeps retrying
  the same idea in reworded form (e.g. "retry fetching the API" vs "let me
  try the API call again"), not just literal repeats.
- **Pause for human approval at a soft threshold** — before the hard cap
  hits, optionally stop and ask a human whether the run should continue.

This is a **local MVP scaffold**: plain Python 3 standard library, no LLM API
key, no server, no accounts. See [`plan.md`](plan.md) for the full scope and
what's intentionally left out (real framework adapters, hosted dashboard,
real webhook delivery — see that file for the complete list).

## How it works

- `agentleash/guard.py` — `SpendCapGuard` accumulates cost per step and
  raises `GuardTripped` when the hard cap is exceeded, when a human declines
  to approve continuing past a soft threshold, or when the loop detector
  flags a run.
- `agentleash/loop_detector.py` — `LoopDetector` scores each new step's text
  against recent prior steps using a blend of `difflib.SequenceMatcher` and
  word-overlap (Jaccard) similarity, and flags a loop once N consecutive
  steps come back "similar enough".
- `examples/fake_agent.py` — a scripted stand-in for a real agent loop, with
  a `normal` run (completes cleanly) and a `runaway` run (gets stuck
  re-planning a failed API call in different words).
- `agentleash/cli.py` — `python -m agentleash demo` wires the fake agent
  through the guard and prints a live per-step log.

## Install

Nothing to install — stdlib only. Just run it from the repo root with
Python 3.

## Run the demo

```bash
# 1. A normal run: stays under budget, completes cleanly.
python3 -m agentleash demo --mode normal --config examples/config.json

# 2. A runaway run: the agent re-plans the same failed step over and over.
#    The breaker trips (loop detected or spend cap exceeded) before the
#    agent's full scripted step count is reached.
python3 -m agentleash demo --mode runaway --config examples/config.json

# 3. Same runaway run, but with a human-approval gate at the "soft"
#    spend threshold (stands in for the human-approval webhook).
python3 -m agentleash demo --mode runaway --config examples/config.json --approval-mode prompt
```

In run 3, when prompted, answering `n` trips the breaker immediately
(`approval_denied`); answering `y` lets the run continue, at which point the
loop detector still catches the runaway re-planning pattern shortly after.

## Configuration

`examples/config.json`:

```json
{
  "spend_cap": 5.0,
  "soft_threshold_fraction": 0.5,
  "similarity_threshold": 0.55,
  "max_consecutive_similar": 4
}
```

- `spend_cap` — hard dollar limit for the run.
- `soft_threshold_fraction` — fraction of `spend_cap` at which to pause for
  human approval (omit/`null` to disable approval gating).
- `similarity_threshold` — score in `[0, 1]` above which two steps are
  considered semantically similar.
- `max_consecutive_similar` — how many similar steps in a row trip the loop
  breaker.

## Run the tests

```bash
python3 -m unittest discover tests
```

- `tests/test_guard.py` — the spend cap trips at the right cumulative cost
  (not before), and the approval hook can approve or deny a run at the soft
  threshold.
- `tests/test_loop_detector.py` — paraphrased, repetitive steps are flagged
  as a loop; genuinely distinct steps are not.

## Using it in your own agent loop

```python
from agentleash import SpendCapGuard, GuardTripped

guard = SpendCapGuard(spend_cap=10.0, similarity_threshold=0.6, max_consecutive_similar=3)

for step_text, cost in your_agent_loop():
    try:
        guard.check_step(step_text, cost)
    except GuardTripped as e:
        print(f"stopped: {e.reason} — {e.detail}")
        break
```
