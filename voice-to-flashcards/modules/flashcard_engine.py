"""
Flashcard Engine
----------------
Pure logic for flashcard progression, known/review tracking, and
progress calculation. No Streamlit imports here — keeps this testable
and separate from rendering.
"""


def init_flashcard_progress(num_cards: int) -> dict:
    return {
        "current_index": 0,
        "known": set(),
        "review": set(),
        "total": num_cards,
    }


def mark_known(progress: dict, index: int) -> dict:
    progress["known"].add(index)
    progress["review"].discard(index)
    return progress


def mark_review(progress: dict, index: int) -> dict:
    progress["review"].add(index)
    progress["known"].discard(index)
    return progress


def next_card(progress: dict) -> dict:
    if progress["current_index"] < progress["total"] - 1:
        progress["current_index"] += 1
    return progress


def prev_card(progress: dict) -> dict:
    if progress["current_index"] > 0:
        progress["current_index"] -= 1
    return progress


def completion_pct(progress: dict) -> float:
    if progress["total"] == 0:
        return 0.0
    seen = len(progress["known"]) + len(progress["review"])
    return round(100 * seen / progress["total"], 1)
