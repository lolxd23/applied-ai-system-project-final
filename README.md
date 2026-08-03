# 🎮 Game Glitch Investigator: AI Coach Edition

## Original Project (Modules 1–3)

This started as a debugging assignment — I got a broken Streamlit number-guessing game and had to find and fix the bugs. The game lets you guess a secret number based on difficulty, and gives Higher/Lower hints to help you narrow it down. It had 4 bugs when I got it: the difficulty setting didn't actually change the number range, hints pointed the wrong way, scoring was inconsistent, and you could type any number even outside the range. I fixed all of that in the original assignment.

## What This Does

This version takes that fixed game and adds a real AI feature: instead of a plain "Go Higher!" / "Go Lower!" message, the game asks Google's Gemini API to write a short, fun coaching hint every time you guess wrong. The important part isn't just "it calls an AI" — it's that I built a way to check the AI's answer before trusting it, so the game can't accidentally lie to the player even if the AI messes up.

## How It's Built

The diagram (`diagrams/architecture.mmd`) shows it in 4 parts:

1. **Input** — you type a guess into the app.
2. **Process** — the code checks your guess is valid, compares it to the secret number, then sends your guess + the secret + the range to Gemini. Gemini sends back a direction (higher/lower) and a hint.
3. **Guardrail** — before you ever see the hint, the code double-checks: does the AI's direction actually match reality? Does the hint accidentally give away the number? If either check fails, or the API just fails (like a rate limit), the game falls back to the plain hint instead.
4. **Output & Testing** — you see the real hint or the fallback, your score updates, and every single call gets logged. I also wrote tests and a script that runs the AI a bunch of times to see how often it actually passes the guardrail.

## How to Run It

1. Clone it:


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

## Why I Built It This Way

- **Check the hint before showing it, not after.** If the game gives a wrong hint, the whole thing is pointless — so I made correctness non-negotiable and built the check to run before anything shows up on screen.
- **Fallback instead of breaking.** If the guardrail catches a bad hint, or the API just fails, the game quietly shows the plain hint instead of crashing or showing an error. Downside: the player doesn't know when the AI actually failed behind the scenes, but I'd rather the game just keep working.
- **Used `gemini-flash-latest` instead of locking to one version.** This actually saved me — the exact model I started with got retired mid-project, and using "latest" meant I didn't have to go find a new one and rewrite things.
- **Logged everything, wins and failures.** Every call gets written to a log file, so I actually had real data to look at instead of just guessing why something didn't work.

## Testing Summary

============================= test session starts ==============================
platform darwin -- Python 3.12.4, pytest-7.4.4,pluggy-1.0.0
rootdir: /Users/hajramuzammal/applied-ai-system-project/applied-ai-system-final
plugins: anyio-4.14.2
collected 11 items

tests/test_ai_coach.py ....                         [ 36%]
tests/test_game_logic.py .......                         [100%]

============================== 11 passed in 1.26s ==============================

## Reflection

Building this with AI helping me made the harder parts go a lot faster especially the guardrail logic. I probably would've taken way longer to figure out "check the direction, check for leaks, then log it" on my own, but going step by step with an assistant let me build it in layers without losing track of what I was doing.

What actually surprised me was that the real failures weren't the AI being dumb they were just infrastructure stuff, like hitting a rate limit. That taught me that "does the AI work" isn't really the right question "does the whole system stay safe when the AI doesn't work" is the one that actually matters.

I also learned I can't just accept every suggestion without checking it myself. At one point the AI coach code got changed to return two values instead of one, but the app code wasn't updated to match I only caught it because I actually tested it in the browser instead of assuming it was fine. If I kept building this out, I'd add retries before falling back, and fix the leak-check so it doesn't get confused by small numbers.