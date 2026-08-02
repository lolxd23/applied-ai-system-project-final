"""Reliability check: runs real game states through the AI coach multiple
times and reports how consistently it gives correct-direction hints."""

import random
import time

from ai_coach import get_ai_hint

TRIALS = 10

STATUS_LABELS = {
    "ok": "PASS",
    "guardrail_inconsistent": "GUARDRAIL BLOCKED (inconsistent direction)",
    "guardrail_leak": "GUARDRAIL BLOCKED (leaked secret)",
    "api_error": "API ERROR (not a guardrail block)",
}

passed = 0
status_counts = {}
for i in range(TRIALS):
    low, high = 1, 100
    secret = random.randint(low, high)
    guess = random.randint(low, high)
    while guess == secret:
        guess = random.randint(low, high)

    hint, status = get_ai_hint(guess, secret, low, high, attempts_left=5)
    ok = status == "ok"
    passed += ok
    status_counts[status] = status_counts.get(status, 0) + 1
    print(f"Trial {i+1}: guess={guess} secret={secret} -> {STATUS_LABELS[status]}")

    time.sleep(13)

api_errors = status_counts.get("api_error", 0)
guardrail_blocks = TRIALS - passed - api_errors

print(f"\n{passed}/{TRIALS} hints passed ({100*passed/TRIALS:.0f}%)")
print(f"  guardrail blocks: {guardrail_blocks} (the guardrail actually caught a bad hint)")
print(f"  api errors:       {api_errors} (call failed before the guardrail ran, e.g. rate limits)")