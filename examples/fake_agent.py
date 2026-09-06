"""Scripted fake agent used by the AgentLeash demo.

Stands in for a real LLM-calling agent loop: each mode returns a list of
(step_text, cost) tuples that a real agent would otherwise produce one at a
time by calling an LLM API.
"""

NORMAL_STEPS = [
    ("Look up the user's account details", 0.35),
    ("Summarize the account status", 0.30),
    ("Draft a response email", 0.40),
    ("Check the response for policy compliance", 0.25),
    ("Send the reply and log the ticket as resolved", 0.30),
]

# A realistic runaway: two distinct setup steps, then the agent gets stuck
# re-planning the same failed API call in slightly different words.
RUNAWAY_STEPS = [
    ("Look up the user's account details", 0.35),
    ("Call the billing API to fetch invoices", 0.40),
    ("Billing API call failed, retry fetching the invoices", 0.50),
    ("Retry fetching the invoices from the billing API", 0.50),
    ("Try fetching the invoices from the billing API again", 0.50),
    ("Attempt to fetch the invoices from the billing API again", 0.50),
    ("One more retry to fetch the invoices from the billing API", 0.50),
    ("Try again to fetch the invoices from the billing API", 0.50),
    ("Retry the billing API invoice fetch one more time", 0.50),
    ("Fetch the invoices from the billing API, retrying again", 0.50),
]


def generate_steps(mode):
    if mode == "normal":
        return list(NORMAL_STEPS)
    if mode == "runaway":
        return list(RUNAWAY_STEPS)
    raise ValueError(f"unknown mode: {mode!r} (expected 'normal' or 'runaway')")
