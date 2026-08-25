"""
Validators
----------
Sanity-checks Gemini's parsed JSON before it ever reaches the UI layer,
so a malformed or partial response fails loudly and early instead of
crashing a page deep in rendering.
"""


class SchemaValidationError(Exception):
    pass


REQUIRED_TOP_LEVEL_KEYS = ["topic", "subject", "summary", "flashcards", "quiz"]


def validate_study_pack(pack: dict) -> dict:
    if not isinstance(pack, dict):
        raise SchemaValidationError("Response was not a JSON object.")

    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in pack]
    if missing:
        raise SchemaValidationError(f"Response is missing required fields: {missing}")

    if not isinstance(pack.get("flashcards"), list) or len(pack["flashcards"]) == 0:
        raise SchemaValidationError("No flashcards were generated.")

    quiz = pack.get("quiz")
    if not isinstance(quiz, list) or len(quiz) == 0:
        raise SchemaValidationError("No quiz questions were generated.")

    for i, q in enumerate(quiz):
        if not isinstance(q.get("options"), list) or len(q["options"]) < 2:
            raise SchemaValidationError(f"Quiz question {i + 1} doesn't have valid options.")
        if q.get("correct_answer") not in q["options"]:
            # Some models occasionally mismatch casing/whitespace — normalize once.
            normalized = q["correct_answer"].strip() if q.get("correct_answer") else ""
            match = next((o for o in q["options"] if o.strip() == normalized), None)
            if match:
                q["correct_answer"] = match
            else:
                raise SchemaValidationError(
                    f"Quiz question {i + 1}'s correct answer doesn't match its options."
                )

    return pack
