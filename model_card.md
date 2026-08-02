# Model Card — Game Glitch Investigator: AI Coach Edition

## Reliability and Evaluation

11 out of 11 automated tests passed (7 game-logic tests, 4 AI guardrail tests). Across two live reliability runs (10 trials each), the AI hint passed the consistency guardrail 60% and 70% of the time — nearly all failures traced to Gemini's free-tier daily quota being exhausted (logged as `429 RESOURCE_EXHAUSTED`), not incorrect AI reasoning. Every failure, whether a guardrail rejection or an API error, was caught and logged, and the game fell back to a plain hint with zero crashes.

| Test Input | Evaluation Criteria | Result |
|---|---|---|
| Guess 30, secret 75, range 1–100 | Hint direction correct, no number leaked | Pass — "Crank up the energy and shoot way higher than that!" |
| Guess 42, secret 38, range 1–100 | Hint direction correct, no number leaked | Pass — "Ooh, you're super warm, but tap the brakes just a tiny bit!" |
| Guess 53, secret 62, range 1–100 | Hint direction correct, no number leaked | Pass — "Great hustle, but you'll need to jump just a little bit higher!" |
| Out-of-range guess (e.g. 500 on range 1–100) | Rejected with clear error, no crash | Pass — "Guess must be between 1 and 100." |
| API call during quota exhaustion | Falls back to plain hint, no crash | Pass — showed "📈 Go HIGHER!" instead |
| Live reliability run, trial with secret=4 | Hint doesn't leak secret digit | Fail — false positive, guardrail blocked a hint that likely didn't actually leak anything, over-strict substring match |

## Reflection and Ethics

**Limitations and biases:**
The AI coach depends entirely on the Gemini free tier, which caps out at a low daily request quota (20/day) — this makes the feature unreliable for extended play sessions or repeated testing, and would need a paid tier or a caching/rate-limiting strategy for real use. The secret-leak guardrail is also overly strict: it blocks any hint containing the secret number as a substring, which produces false positives when the secret is a small number that might appear incidentally in phrasing. The system has no memory across guesses — each hint is generated independently, so the AI can't reference the player's guess history or adjust its tone over a longer session.

**Could this be misused, and how would I prevent it?**
The risk surface here is low since it's a self-contained single-player game with no user data collection, accounts, or external actions. The main way it could misbehave is the AI hint accidentally revealing the secret number outright, which would defeat the purpose of the game — this is exactly what the guardrail is designed to catch before display, and the fallback ensures a leaked or incorrect hint is never actually shown to the player.

**What surprised me while testing:**
I expected the failure mode to be "the AI gives a wrong hint," but the actual failure I hit in testing was infrastructure-level (API rate limits), not a reasoning error from the model. That was a good reminder that reliability testing needs to account for the whole pipeline, not just the model's output quality — a perfectly reasoning model is still unreliable if the surrounding system doesn't handle its downtime gracefully.

**Collaboration with AI during this project:**
I built this with an AI coding assistant throughout — from designing the guardrail approach, to writing `ai_coach.py`, to debugging issues as they came up.

- **Helpful suggestion:** The guardrail design itself — checking the AI's stated hint direction against the actual ground-truth comparison (and rejecting/falling back if they disagree) before ever showing it to the player. This turned "trust the AI" into "verify, then trust," which is the core safety mechanism of the whole feature.
- **Flawed suggestion:** At one point `ai_coach.py` was updated to return a `(hint, status)` tuple instead of a single value, but `app.py` wasn't updated to match — it was still doing `if ai_hint:` on what was now always a truthy tuple. This would have silently broken the fallback logic if I hadn't caught it by testing in the browser and checking the actual variable shapes.