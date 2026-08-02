# 🎮 Game Glitch Investigator: AI Coach Edition

## Original Project (Modules 1–3)

This project began as a **debugging assignment**: an AI had generated a broken Streamlit number-guessing game, and the goal was to find and fix the bugs. The original game let a player guess a secret number within a difficulty-based range, using Higher/Lower hints to narrow it down. It shipped with four bugs — a difficulty selector that didn't change the number range, a type-comparison bug that gave backwards hints, an inconsistent scoring rule, and no bounds checking on guesses — all of which were identified and fixed as part of that assignment.

## Title and Summary

**Game Glitch Investigator: AI Coach Edition** takes that fixed guessing game and adds a live AI feature: instead of a static "Go Higher!" / "Go Lower!" message, the game asks Google's Gemini API to generate a short, playful coaching hint for every wrong guess. This matters because it shows how a simple deterministic app can be upgraded with an LLM feature *safely* — the AI's output is verified before it's trusted, and the app never breaks or lies to the player even when the AI does.

## Architecture Overview

The system diagram (`system_diagram.mmd`) breaks the app into four stages:

1. **Input** — the player submits a guess in the Streamlit UI.
2. **Process** — the guess is validated and compared against the secret number, then sent to Gemini as part of a prompt (along with the range and attempts remaining). Gemini returns a direction ("higher"/"lower") and a fun hint sentence.
3. **Guardrail** — before anything is shown to the player, the system checks whether Gemini's stated direction actually matches the real comparison, and whether the hint text accidentally reveals the secret number. If either check fails, or the API call itself fails (e.g. rate limits), the app falls back to the original plain hint instead.
4. **Output & Testing** — the validated hint (or fallback) updates the score and displays to the player. Every AI call, guardrail pass, and guardrail block is logged to `ai_coach.log`. A pytest suite and a standalone reliability script (`reliability_check.py`) independently verify the guardrail logic and measure how often live Gemini calls pass it.

## Setup Instructions

1. Clone the repo:

git clone https://github.com/lolxd23/applied-ai-system-project-final.git
cd applied-ai-system-project-final

2. Install dependencies:

pip install -r requirements.txt

3. Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) (click "Get API key").
4. Create a `.env` file in the project root:

echo 'GEMINI_API_KEY=your-key-here' > .env

5. Run the app:

streamlit run app.py

6. Run the tests:

pytest

7. (Optional) Run the live reliability check — makes real API calls, takes ~2 minutes:

python reliability_check.py


## Sample Interactions

*Guess = 30, secret = 75, range 1–100:*
> 🤖 Coach: "Crank up the energy and shoot way higher than that!"

*Guess = 42, secret = 38, range 1–100:*
> 🤖 Coach: "Ooh, you're super warm, but tap the brakes just a tiny bit!"

*Guess = 53, secret = 62, range 1–100:*
> 🤖 Coach: "Great hustle, but you'll need to jump just a little bit higher!"

## Design Decisions

- **Guardrail before display, not after.** The AI's hint is fully validated against ground truth *before* the player ever sees it, rather than showing it and correcting later. A guessing game is worthless if the hints can lie, so correctness was treated as non-negotiable.
- **Fallback over failure.** Any guardrail rejection or API error silently falls back to the original plain-text hint rather than showing an error to the player. The trade-off is that the player doesn't always know when the AI failed behind the scenes — but the game staying playable was prioritized over transparency about backend failures.
- **`gemini-flash-latest` over a pinned version.** Using the "latest" alias instead of a specific model snapshot means the app won't break when Google retires older models (which happened once already during development — see Testing Summary). The trade-off is less predictability in exact output style over time.
- **Logging everything, not just failures.** Every call — success or failure — is logged with the guess, secret, and result, so the reliability script has real data to report on instead of just a pass/fail count.

## Testing Summary

- **Unit tests (11 total, all passing):** 7 original tests cover the core game logic (range selection, guess parsing, comparison, scoring). 4 new tests cover the AI guardrail logic (`expected_direction` and `hint_is_consistent`) using deterministic inputs — no live API calls, so they run instantly and reliably.
- **What broke during development:** the originally chosen model (`gemini-2.5-flash`) was retired mid-project and had to be swapped for `gemini-flash-latest`. The free-tier daily quota (20 requests/day) was also exhausted during testing, which surfaced real `429 RESOURCE_EXHAUSTED` errors from the live API — and confirmed the fallback guardrail handled every one of them gracefully, with zero crashes and a clear log trail explaining exactly why each call failed.
- **Live reliability results:** Two reliability runs (10 trials each) produced 60% and 70% pass rates. Nearly all failures were traced via logging to Gemini's free-tier daily quota (20 requests/day) being exhausted mid-testing — not incorrect AI reasoning. A third run attempted the next day failed 0/10 for the same reason, confirming the quota resets on a longer cycle than expected. See `model_card.md` for the full evaluation table.

## Reflection

Building this with an LLM in the loop made a few things noticeably easier than I expected going in. Writing the guardrail logic — checking whether Gemini's hint direction actually matched the real comparison — would have taken me a lot longer to design from scratch, but sketching it out with an AI assistant let me iterate on the idea quickly: first pass, then add the secret-leak check, then wire in logging, without losing momentum between each step.

The part that surprised me was how much value showed up in the *failures*, not just the successes. When I hit the free-tier daily quota mid-testing, my first instinct was that something was broken. But the guardrail and fallback handled every single failed call gracefully — the game kept working, and the log file told me exactly why each call failed. That was a good reminder that "AI feature works" isn't really the bar; "AI feature fails safely" is the bar that actually matters once something like this is running for real users.

I also had to stay pretty hands-on rather than just accepting whatever code was suggested — a few times a rewritten file quietly introduced a mismatch (like `ai_coach.py` returning a tuple while `app.py` still expected a single value), and catching that meant actually reading the diffs instead of assuming everything just worked. If I extended this project, I'd add retry-with-backoff logic instead of an immediate fallback, and I'd tighten the secret-leak check so it doesn't false-positive on small numbers.