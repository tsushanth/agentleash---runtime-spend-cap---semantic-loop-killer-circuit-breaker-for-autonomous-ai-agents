# AgentLeash — Local MVP Scaffold Plan

## Goal of this MVP

Prove the core value — **wrap an agent loop, track spend, detect semantic
re-planning loops, and trip a circuit breaker before budget blows past a
cap** — entirely on a local machine, with no real LLM API key, no server,
and no accounts required to run the demo.

## 1. Stack

**Plain Python 3, stdlib only.** No web framework, no ML library, no DB.

Why:
- The wrapper's job is to sit *around* whatever function makes the "LLM
  call" (real or fake) and observe two things: a reported cost/token count,
  and the text of the agent's next planned action. Neither requires a
  framework.
- Semantic-loop detection for the demo uses `difflib.SequenceMatcher` +
  a simple word-overlap (Jaccard) score over normalized/lowercased step
  text — good enough to catch "reworded but same idea" re-planning loops
  (e.g. "retry fetching the API" vs "let me try the API call again")
  without needing embeddings, an API key, or network access.
- Python is the natural choice because the real target frameworks
  (LangGraph, CrewAI) are Python-native, so the demo interface (wrap any
  callable that returns `(text, cost)`) reads as credible/portable, even
  though this MVP never actually calls LangGraph/CrewAI.
- CLI entry point via stdlib `argparse` — no packaging/build step needed
  to run it (`python -m agentleash ...`).

## 2. Explicitly out of scope for this local MVP

- **Real LLM API calls** — the demo uses a scripted fake "agent" that
  simulates both a normal run and a runaway/looping run, each step
  returning canned text + a cost figure. Proves the breaker logic without
  needing an API key or incurring real spend.
- **Hosted dashboard / policy layer** — not built. The pitch mentions this
  as a monetization layer later; the local MVP only needs the core
  library logic.
- **Human-approval webhook (real HTTP)** — simulated as a local
  interactive prompt (`input()`) or a "pending approval" JSON file the
  demo script checks, instead of standing up a server/ngrok/webhook
  receiver.
- **Auth, accounts, billing, multi-tenancy** — irrelevant to proving the
  circuit-breaker mechanic.
- **Deploy/hosting/packaging (PyPI publish, Docker, etc.)** — not needed
  to run locally.
- **Real framework adapters** (LangGraph/CrewAI/browser-use integration
  shims) — out of scope; the MVP proves the generic wrapper contract
  only. Adapters are future work once the core is validated.
- **Persistent storage / real database** — spend state lives in memory
  for the duration of one run; optionally appended to a local JSON log
  file for inspection, nothing more.

## 3. File / directory layout

```
agentleash/
  __init__.py          # exports SpendCapGuard, LoopDetector, GuardTripped
  guard.py             # core circuit breaker: spend accounting, threshold
                        #   checks, approval-hook trigger, kill/pause logic
  loop_detector.py      # semantic similarity check over recent step texts
  cli.py                # `python -m agentleash demo` entry point

examples/
  fake_agent.py         # scripted agent: --mode normal | --mode runaway
                        #   yields (step_text, cost) tuples per "call"
  config.json            # spend cap ($), similarity threshold, max
                        #   consecutive similar steps before trip

tests/
  test_guard.py          # spend cap trips at the right cumulative cost
  test_loop_detector.py  # near-duplicate phrasing is flagged as a loop,
                        #   genuinely different steps are not

plan.md                 # this file
```

## 4. Verification

- **Unit tests** (`python -m unittest discover tests`):
  - `test_guard.py`: feed a sequence of costs that cross the configured
    cap and assert `GuardTripped` is raised at the right step, not
    before.
  - `test_loop_detector.py`: feed paraphrased-but-repetitive plan strings
    and assert the detector flags a loop after N similar steps; feed
    genuinely distinct steps and assert it does not false-positive.

- **Manual run-through** (the actual demo):
  1. `python -m agentleash demo --mode normal --config examples/config.json`
     → agent completes its scripted steps, total spend stays under cap,
     process exits 0 with a summary line (steps run, total cost, no
     trip).
  2. `python -m agentleash demo --mode runaway --config examples/config.json`
     → fake agent repeats semantically-similar re-planning steps while
     accumulating cost; CLI prints a live per-step spend/similarity log,
     then prints a `CIRCUIT BREAKER TRIPPED` message (either "loop
     detected" or "spend cap exceeded", whichever fires first) and halts
     the loop before it reaches the fake agent's full scripted step
     count — the concrete before/after that proves the guard did its
     job.
  3. `python -m agentleash demo --mode runaway --approval-mode prompt`
     → when the run crosses a lower "soft" threshold, the CLI pauses and
     asks the user to approve continuing (y/n) before resuming, standing
     in for the human-approval webhook.
