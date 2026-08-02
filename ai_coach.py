"""AI Game Coach — generates natural-language hints using Gemini.

Guardrail: the AI must declare a direction (higher/lower) and we verify it
against the ground truth before showing it. If the AI is wrong, unavailable,
or slow, the app falls back to the plain hint so the game never lies.
Every call is logged to ai_coach.log.
"""

import json
import logging
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemini-flash-latest"

logging.basicConfig(
    filename="ai_coach.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def expected_direction(guess: int, secret: int) -> str:
    """Ground truth the AI's answer is checked against."""
    return "higher" if guess < secret else "lower"


def hint_is_consistent(ai_direction: str, guess: int, secret: int) -> bool:
    """Guardrail: does the AI's stated direction match reality?"""
    return ai_direction.strip().lower() == expected_direction(guess, secret)


def get_ai_hint(guess: int, secret: int, low: int, high: int, attempts_left: int):
    """Return (hint, status) where hint is a validated AI coaching hint or
    None, and status is one of:
      "ok"                    - hint was generated and passed the guardrail
      "guardrail_inconsistent" - AI's stated direction didn't match reality
      "guardrail_leak"        - AI's hint text leaked the secret number
      "api_error"             - the API call itself failed (rate limit, etc.)

    A None hint (any non-"ok" status) tells the app to fall back to the
    plain Higher/Lower hint.
    """
    prompt = (
        "You are a playful coach in a number guessing game. "
        f"The range is {low} to {high}. The player guessed {guess}. "
        f"The secret number is {secret}. They have {attempts_left} attempts left. "
        "Respond with ONLY a JSON object, no markdown fences, in this format: "
        '{"direction": "higher" or "lower", "hint": "one short fun sentence '
        'nudging the player without revealing the secret number"}'
    )
    try:
        client = _get_client()
        response = client.models.generate_content(model=MODEL, contents=prompt)
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        direction, hint = data["direction"], data["hint"]

        if not hint_is_consistent(direction, guess, secret):
            logging.warning(
                "GUARDRAIL BLOCKED inconsistent hint: guess=%s secret=%s "
                "ai_direction=%s hint=%r", guess, secret, direction, hint,
            )
            return None, "guardrail_inconsistent"

        if str(secret) in hint:
            logging.warning("GUARDRAIL BLOCKED hint leaking secret: %r", hint)
            return None, "guardrail_leak"

        logging.info(
            "AI hint OK: guess=%s secret=%s direction=%s hint=%r",
            guess, secret, direction, hint,
        )
        return hint, "ok"

    except Exception as exc:
        logging.error("AI call failed, falling back to plain hint: %s", exc)
        return None, "api_error"