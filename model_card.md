# Model Card — Game Glitch Investigator: AI Coach Edition

## Reliability and Evaluation

All 11 tests pass (7 for the game logic, 4 for the AI guardrail). I also ran the AI through 10 real guesses twice to see how consistent it actually was — got 60% and 70% pass rates. Almost all the fails weren't the AI being wrong, they were Gemini's free daily limit running out (`429 RESOURCE_EXHAUSTED` in the log). Every time something failed, whether it was the guardrail catching a bad hint or the API just breaking, the game logged it and fell back to the plain hint instead of crashing.

| Test Input | What I Was Checking | Result |
|---|---|---|
| Guess 30, secret 75, range 1–100 | Right direction, doesn't give away the number | Pass — "Crank up the energy and shoot way higher than that!" |
| Guess 42, secret 38, range 1–100 | Right direction, doesn't give away the number | Pass — "Ooh, you're super warm, but tap the brakes just a tiny bit!" |
| Guess 53, secret 62, range 1–100 | Right direction, doesn't give away the number | Pass — "Great hustle, but you'll need to jump just a little bit higher!" |
| Out-of-range guess (like 500 on a 1–100 range) | Gets rejected, doesn't crash | Pass — "Guess must be between 1 and 100." |
| API call while quota was maxed out | Falls back to plain hint, doesn't crash | Pass — showed "📈 Go HIGHER!" instead |
| A run where the secret was 4 | Hint shouldn't leak the number | Fail — the guardrail blocked a hint that probably wasn't actually leaking anything, it's just too strict about single digits |

## Reflection and Ethics

**Limitations and biases:**
Biggest one is the Gemini free tier only 20 requests a day, so this can't really handle long play sessions or a lot of testing without hitting that wall. I'd need a paid plan or some kind of caching to make this usable for real. The guardrail that checks for leaked numbers is also too strict it blocks anything containing the secret number as a substring, so small numbers like single digits cause false positives. Also the AI has no memory between guesses, so it can't build on your guess history or change its tone as the game goes on.

**Could this be misused?**
Not really a big risk here — it's just a single-player game with no accounts or data collection. The one real way it could go wrong is the AI accidentally saying the secret number out loud in a hint, which would ruin the whole point of the game. That's exactly what the guardrail catches before anything gets shown, and the fallback makes sure a bad or leaky hint never actually reaches the player.

**What surprised me:**
I expected the AI to mess up by just giving wrong hints. Instead, the actual problem was infrastructure hitting rate limits not the model reasoning badly. That taught me reliability isn't just "does the model get it right," it's "does the whole system survive when something outside my control breaks."

**Working with AI on this project:**
I used an AI assistant the whole way through building the guardrail idea and debugging as stuff broke.

- **Something that actually helped:** the guardrail idea itself checking if the AI's stated direction matches what's actually true before showing it to the player. Instead of just trusting whatever the AI says, the system double-checks it first. That's basically the whole safety net for this feature.
- **Something that went wrong:** at one point `ai_coach.py` got changed to return two values (`hint, status`) instead of just one, but `app.py` didn't get updated to match — so it was still doing `if ai_hint:` on a tuple that's always truthy. That would've quietly broken the fallback logic if I hadn't actually tested it in the browser and looked at what the variables were doing.